# Gérer les longs calculs sans stress : Le Job Store SQLite

**TL;DR** : Un système de file d'attente persistant basé sur SQLite. Il sépare le serveur web des calculs lourds pour garantir qu'aucun crash ou redémarrage de l'interface n'interrompe tes optimisations en cours.

Tu as configuré une optimisation massive sur 10 000 combinaisons pour ta stratégie Range Filter. Le calcul va durer 4 heures. Au bout de 3 heures et demie, tu fermes accidentellement ton navigateur, ou ton serveur API Web FastAPI subit un micro-redémarrage à cause d'une mise à jour système. 

Dans un système classique non persistant, tout est perdu. Tu dois tout relancer depuis le début et tu viens de gaspiller 3 heures de calcul.

Le **Job Store SQLite** est là pour t'éviter ce cauchemar. En isolant la gestion des tâches dans une base de données locale persistante, il protège ton travail contre les coupures de courant, les crashs d'interface et les manques de mémoire.

---

## Une architecture découplée pour plus de sécurité

Le secret de la robustesse de notre système réside dans la séparation stricte des rôles entre trois composants distincts.

```
+--------------------+
|  Serveur FastAPI   |  <- Ne fait aucun calcul lourd
+--------------------+
          |
          v Enregistre la demande (PENDING)
+-------------------------------------------------+
|  Base SQLite partagée (jobs.sqlite3)            |  <- Le journal de bord persistant
+-------------------------------------------------+
          ^
          | Réserve et exécute la tâche (IN_PROGRESS)
+--------------------+
|  Worker local      |  <- Consomme les calculs en arrière-plan
+--------------------+
```

### 1. Le Serveur FastAPI (L'intermédiaire)
Quand tu cliques sur "Lancer l'optimisation" dans ton interface graphique, le serveur web ne calcule rien lui-même. Il valide simplement ta demande, génère un identifiant unique pour ta tâche (`job_id`), écrit une nouvelle ligne avec le statut `PENDING` dans la base SQLite, et te rend immédiatement la main. Tu peux naviguer sur d'autres pages ou fermer l'interface : l'ordre est enregistré.

### 2. Le Job Store SQLite (Le pivot)
Situé dans `reports/local_optimizer/jobs.sqlite3`, ce simple fichier de base de données est le cœur persistant du système. C'est lui qui stocke l'état d'avancement de toutes les tâches passées, présentes et futures.

### 3. Le Worker (La force brute)
C'est un processus autonome qui tourne en tâche de fond. Il interroge régulièrement le Job Store SQLite pour voir si de nouvelles tâches sont en attente. Dès qu'il trouve un job `PENDING`, il le verrouille en passant son statut à `IN_PROGRESS`, lance les calculs intensifs sur ton processeur, et met à jour sa progression en temps réel dans la base de données.

---

## Le cycle de vie d'une tâche d'optimisation

Chaque simulation longue traverse plusieurs états bien définis :
- **`PENDING`** : Ta demande est dans la file d'attente. Elle attend qu'un worker CPU se libère pour la traiter.
- **`IN_PROGRESS`** : Un worker exécute l'optimisation. Tu peux suivre le pourcentage d'avancement barre par barre.
- **`COMPLETED`** : C'est terminé. Le worker a enregistré le meilleur jeu de paramètres et le rapport de stabilité dans le dossier de résultats.
- **`FAILED`** : Quelque chose a planté (données corrompues, coupure de courant). Le message d'erreur est conservé pour t'aider à comprendre.
- **`CANCELLED`** : Tu as cliqué sur le bouton d'arrêt d'urgence. Le worker arrête proprement ses calculs et libère ton processeur.

---

## Commandes d'administration pour ton terminal

Tu as deux commandes principales pour gérer cette file d'attente en direct.

### Lancer le worker de calcul
Pour commencer à exécuter les tâches en attente dans la file d'attente :

```bash
python3 -m backtest_engine worker \
  --output-dir reports/local_optimizer \
  --poll-interval 1.0 \
  --worker-id worker-node-01
```

> [!TIP]
> Si tu veux intégrer le backtester dans un script automatisé qui s'arrête dès que la file d'attente est vide, ajoute l'option `--once`. Le worker exécutera le premier job disponible puis quittera proprement le terminal.

### Nettoyer la base après un crash brutal
Si ton système d'exploitation décide de tuer le worker parce que ta machine a manqué de mémoire vive (erreur Out of Memory ou OOM Kill), la tâche en cours restera indéfiniment marquée comme `IN_PROGRESS` dans la base SQLite.

Pour débloquer la file d'attente et marquer proprement ce job orphelin en échec, utilise la commande de nettoyage :

```bash
python3 -m backtest_engine mark-crashed \
  --worker-id worker-node-01 \
  --exit-code 137
```

Le moteur interprète automatiquement les codes de sortie système courants pour écrire un rapport d'erreur utile dans tes logs (ex: le code `137` sera traduit en clair par *"Worker crashed : OOM / SIGKILL"*, et le code `139` par *"Worker crashed : Segfault / SIGSEGV"*).

---

## Maintenance automatique de la base de données

Une base de données qui grossit sans fin finit par ralentir le système. Notre Job Store intègre un service de nettoyage automatique pour rester léger :
- **Suppression par âge (TTL)** : Toutes les tâches terminées (`COMPLETED` ou `FAILED`) qui datent de plus de 24 heures sont automatiquement supprimées du fichier SQLite.
- **Suppression par volume** : Nous conservons un historique maximal de 100 tâches. Si tu dépasses cette limite, les jobs terminés les plus anciens sont effacés. Bien sûr, les jobs actifs ou en attente ne sont jamais touchés.
