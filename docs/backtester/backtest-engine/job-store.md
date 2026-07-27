# Gérer les longs calculs sans stress : Le Job Store SQLite

**TL;DR** : Un système de file d'attente persistant basé sur SQLite avec chiffrement AES-256 (SQLCipher) et signatures cryptographiques HMAC-SHA256. Il sépare le serveur web des calculs lourds pour garantir qu'aucun crash ou redémarrage de l'interface n'interrompe tes optimisations en cours.

---

Tu as configuré une optimisation massive sur 10 000 combinaisons pour ta stratégie Range Filter. Le calcul va durer 4 heures. Au bout de 3 heures et demie, tu fermes accidentellement ton navigateur, ou ton serveur API Web FastAPI subit un micro-redémarrage à cause d'une mise à jour système.

Dans un système classique non persistant, tout est perdu. Tu dois tout relancer depuis le début et tu viens de gaspiller 3 heures de calcul.

Le **Job Store SQLite** est là pour t'éviter ce cauchemar. En isolant la gestion des tâches dans une base de données locale persistante, il protège ton travail contre les coupures de courant, les crashs d'interface et les manques de mémoire.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   FastAPI Server                      │
│  POST /jobs → enqueue → SQLite                       │
│  GET  /jobs/{id} → read status → SQLite              │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                 Worker Thread (psycopg2 sync)         │
│  Poll SQLite → pick PENDING job → execute → update   │
└──────────────────────────────────────────────────────┘
```

---

## Sécurité du Job Store

### Chiffrement SQLCipher (AES-256)

Depuis la Phase 1 du plan de remédiation sécurité (2026-07-04), la base SQLite est chiffrée avec SQLCipher (AES-256). Sans la clé de chiffrement, les données des jobs sont illisibles — même avec un accès physique au fichier `.sqlite`.

```python
# Configuration dans job_store.py
SQLITE_PRAGMA_KEY = os.environ["SQLCIPHER_KEY"]  # Clé AES-256
```

### Signatures HMAC-SHA256

Chaque job est signé cryptographiquement pour prévenir l'altération des données :

```python
def compute_job_signature(job_id, created_at, request_json, status, output_dir):
    message = f"{job_id}|{created_at}|{request_json}|{status}|{output_dir}".encode("utf-8")
    key = os.environ["JOB_SIGNING_KEY"].encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()
```

La signature est vérifiée à chaque lecture du job. Une signature invalide lève `JobSignatureError` et le job est marqué comme corrompu.

### Fail-Fast au démarrage

Conformément à §2.2, le Job Store valide la présence de `SQLCIPHER_KEY` et `JOB_SIGNING_KEY` au démarrage. Si les clés sont absentes, l'application lève une exception explicite et refuse de démarrer.

---

## États des jobs

```
PENDING ──[worker picks]──▶ RUNNING ──[success]──▶ COMPLETED
    │                           │
    │                           ├──[error]──▶ FAILED
    │                           ├──[crash]──▶ CRASHED
    │                           └──[cancel]──▶ CANCELED
    │
    └──[cancel requested]──▶ CANCEL_REQUESTED
```

---

## Utilisation

### Lancer le worker

```bash
python3 -m backtest_engine worker \
  --job-store ./storage/jobs.sqlite \
  --poll-interval 1.0 \
  --max-concurrent 2
```

### Nettoyer la base après un crash brutal

```bash
python3 -m backtest_engine mark-crashed \
  --job-store ./storage/jobs.sqlite \
  --exit-code 137
```

Le moteur interprète automatiquement les codes de sortie système courants pour écrire un rapport d'erreur utile dans tes logs (ex: le code `137` sera traduit en clair par *"Worker crashed : OOM / SIGKILL"*, et le code `139` par *"Worker crashed : Segfault / SIGSEGV"*).

---

## Maintenance automatique de la base de données

Une base de données qui grossit sans fin finit par ralentir le système. Notre Job Store intègre un service de nettoyage automatique pour rester léger :

- **Vacuum automatique** : Exécuté après chaque complétion de job
- **Purge des anciens jobs** : Les jobs terminés depuis plus de 30 jours sont archivés
- **Nettoyage des jobs corrompus** : Les jobs avec signature invalide sont isolés

---

## Thread-safety

Le Job Store utilise `threading.RLock` pour protéger les accès concurrents entre le serveur FastAPI (qui enqueue) et le worker (qui déqueue). L'ordre d'acquisition est strict pour éviter les deadlocks (§2.5).

---

## The Golden Rule

> **Règle d'or** : Chaque job doit pouvoir être repris après un crash sans perte de progression. Le Job Store est la mémoire du système — s'il est corrompu, tout le pipeline d'optimisation s'effondre. C'est pourquoi chaque octet est chiffré et chaque ligne est signée.

---

*Guidé par documentation/SKILL.md — sections: TL;DR, Problem-First, Architecture, Golden Rule.*
