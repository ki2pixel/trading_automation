# Audit de faisabilité : Optimizer cloud sur VULTR

Évaluer la faisabilité technique et économique de déporter les jobs lourds de l'optimizer local (notamment bayésien 1min) sur des instances VULTR éphémères facturées à l'heure, tout en conservant l'UI locale comme contrôleur hybride.

## 1. Contexte & problématique

- **Local** : 24 threads, jobs bayésiens 1min pouvant durer plusieurs heures.
- **Besoin** : accéder ponctuellement à 32–96 threads dédiés sans laisser d'instance allumée en permanence.
- **Contraintes** : coûts maîtrisés, récupération des artefacts, arrêt automatique, UI locale en mode "cloud".

## 2. Synthèse des offres VULTR pertinentes

| Produit | Pertinence | Observation |
|---------|------------|-------------|
| **VX1 Cloud Compute** (dedicated CPU) | **Élevée** | Facturation à l'heure réelle, pas de plafond 672h. Plans 4c à 192c. Boot <15s. |
| **Optimized Cloud Compute** (legacy) | Moyenne | Moins performant/€ que VX1. Utile uniquement si VX1 indisponible dans une région. |
| **Block Storage** | Élevée | Volume persistant détachable pour stocker `storage/processed` entre jobs. |
| **Object Storage** | Élevée | Staging pour upload des données et download des artefacts. Tarification ~$5/TB/mois. |
| **Container Registry** | Moyenne | Requis si on conteneurise l'optimizer. Accélère le déploiement. |
| **Kubernetes Engine** | Faible | Overkill pour un usage sporadique et éphémère. Complexité non justifiée. |
| **Serverless Inference** | Nulle | Dédié LLM/IA inference, pas de compute CPU généraliste. |

## 3. Options d'architecture évaluées

### Option A — Instance éphémère par job (recommandée)

**Principe** : l'UI locale déclenche la création d'une instance VX1 via l'API. Un *startup script* (cloud-init) clone le repo, installe les dépendances, télécharge les données depuis un Object Storage (ou les reçoit en SCP), exécute le job, upload les résultats, appelle un webhook local, puis détruit l'instance.

- **Avantages** : coût strictement limité à la durée du job, pas d'infrastructure dormante, isolement total entre jobs.
- **Inconvénients** : overhead de boot + setup (~2–4 min par job), risque d'oubli de destruction si le script échoue.
- **Mitigation** : snapshot du système pré-configuré + systemd timer qui force le destroy après timeout.

### Option B — Pool "warm" de N instances

**Principe** : maintenir un petit pool d'instances toujours allumées mais en attente de jobs (queue SSH ou HTTP).

- **Avantages** : latence quasi nulle pour lancer un job.
- **Inconvénients** : coût continu ($0.24–$0.96/hr par instance), contredit l'objectif de ne pas laisser allumer hors backtests.
- **Verdict** : à écarter sauf si usage très fréquent (> 20h/jour).

### Option C — Kubernetes + Jobs

**Principe** : cluster VKE managé avec des nodes autoscalables.

- **Avantages** : orchestration native, gestion de file d'attente.
- **Inconvénients** : coût fixe du control plane + complexité opérationnelle. Non justifié pour un usage hebdomadaire.
- **Verdict** : trop lourd pour le besoin actuel.

## 4. Analyse coût / performance

### Hypothèses
- Job bayésien typique : 3h sur 1min avec beaucoup d'itérations.
- Volume de données : ~130 Mo par symbole, cible ~1 Go sécurité.
- Bande passante VX1 incluse : 5–10 To, largement suffisant.

### Comparaison des plans VX1 pertinents

| Plan VX1 | vCPUs | RAM | Prix/hr | Coût/job 3h | vs local (24c) |
|----------|-------|-----|---------|-------------|----------------|
| 8c-32g | 8 | 32 GB | $0.240 | $0.72 | Sous-dimensionné pour le besoin |
| 16c-64g | 16 | 64 GB | $0.480 | $1.44 | Équivalent local (24c vs 16c dédiés) |
| 32c-128g | 32 | 128 GB | $0.960 | $2.88 | ~2× plus rapide, coût doublé |
| 48c-192g | 48 | 192 GB | $1.440 | $4.32 | ~3× plus rapide |

### Scénarios d'usage mensuel

| Usage | Plan | Coût mensuel estimé |
|-------|------|---------------------|
| 5 jobs × 3h | 16c-64g | ~$7.20 |
| 10 jobs × 3h | 32c-128g | ~$28.80 |
| 20 jobs × 3h | 32c-128g | ~$57.60 |
| Instance 24c locale 24/7 (équivalent) | — | ~$770/mois si cloud continu |

**Conclusion coût** : le modèle éphémère est économiquement très favorable. Même 20 jobs/mois restent < $60.

### Options de stockage

| Option | Prix indicatif | Usage |
|--------|----------------|-------|
| Object Storage (S3-compatible) | ~$5/TB/mois | Staging temporaire données + artefacts. Coût négligeable pour 1–5 Go. |
| Block Storage 50 Go | ~$5/mois | Volume persistant détachable. Utile si on veut garder un `storage/processed` à jour sans ré-upload. |
| Local NVMe (inclus VX1-###s) | Inclus | Stockage scratch rapide pendant le job. Disparaît avec l'instance. |

## 5. Architecture cible recommandée

```
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│   UI locale     │──────▶  Orchestrateur     │──────▶  API VULTR v2   │
│  (FastAPI + JS) │      │  (script Python)    │      │  (création VM)  │
└─────────────────┘      └─────────────────────┘      └─────────────────┘
         │                          │
         │    Webhook / polling     │
         │◀─────────────────────────│
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────────┐
│  Job Store      │      │  Object Storage     │
│  (SQLite local) │      │  (staging data)     │
└─────────────────┘      └─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │  Instance VX1 éphémère      │
                    │  - Boot + cloud-init        │
                    │  - pip install / clone      │
                    │  - Download data from OS    │
                    │  - Run optimizer (n workers)│
                    │  - Upload artefacts to OS   │
                    │  - Call webhook             │
                    │  - Auto-destroy             │
                    └─────────────────────────────┘
```

### Workflow détaillé

1. **Soumission** : l'utilisateur bascule l'UI en mode "cloud" et lance un job. La requête est stockée dans le `job_store` local avec un statut `PENDING_CLOUD`.
2. **Provisioning** : l'orchestrateur local appelle `POST /v2/instances` avec :
   - un plan VX1 adapté au job (ex: 32c-128g pour un gros bayésien),
   - un `startup_script` (cloud-init) contenant :
     - les commandes de setup (clone repo, pip install),
     - le téléchargement des données depuis Object Storage,
     - la commande d'exécution du job,
     - l'upload des résultats,
     - l'appel webhook,
     - la destruction de l'instance (`DELETE /v2/instances/{id}`).
3. **Exécution** : l'instance tourne en autonomie. L'UI local peut poller l'orchestrateur ou recevoir le webhook pour mettre à jour le statut.
4. **Récupération** : une fois le webhook reçu, l'UI télécharge les artefacts depuis Object Storage dans `reports/local_optimizer` et affiche les résultats comme si le job avait tourné localement.

## 6. Risques & mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Instance oubliée (non détruite) | Coût continu | Timeout systemd sur l'instance + cron côté orchestrateur qui vérifie les VMs orphelines |
| Échec du startup script | Job perdu, VM idle | Logging sur Object Storage, retry 1×, webhook d'erreur |
| Clé API VULTR exposée | Sécurité | Stocker la clé uniquement côté orchestrstrateur local (fichier `.env`), jamais dans le startup script |
| Données de marché absentes | Échec du job | Pré-upload systématique dans Object Storage avant le provisioning |
| Latence réseau lente | Upload/download long | Compression des données (zstd), région VULTR proche géographiquement |

## 7. Livrables de l'audit & prochaines étapes

1. **Document technique** : le présent audit (ce fichier).
2. **Preuve de concept (POC)** : un script Python standalone qui, via la CLI `vultr-cli` ou `curl`, crée une instance VX1, exécute un `echo "hello"`, upload un fichier, et détruit l'instance.
3. **Benchmark** : mesurer le temps réel d'un job bayésien identique sur VX1 16c et 32c vs le local 24c, et confirmer le ratio prix/perf.
4. **Spécification du mode cloud UI** : document d'interface définissant les nouveaux endpoints API, les champs de configuration (plan VULTR, région, clé API), et les états du job store (`PENDING_CLOUD`, `PROVISIONING`, `RUNNING_CLOUD`, `COMPLETED_CLOUD`, `FAILED_CLOUD`).

---

*Date de l'audit* : 2026-05-25  
*Basé sur* : doc VULTR locale (`/home/kidpixel/trading_automation_v2/docs/vultr`), architecture optimizer (`backtest_engine/web.py`, `optimizer.py`, `job_store.py`), et pricing VULTR 2026.