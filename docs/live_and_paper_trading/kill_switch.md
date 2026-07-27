# Kill Switch — Circuit Breaker Distribué

**TL;DR**: Un système de coupe-circuit distribué basé sur Redis Pub/Sub qui suspend instantanément tout le trading sur tous les workers en cas d'anomalie (max drawdown journalier, taux d'erreur API, commande manuelle), annule les ordres en attente et bascule le mode en "Close-Only".

---

Vous avez déployé votre Paper Trader sur plusieurs workers en parallèle. Tout fonctionne depuis des semaines. Puis, un vendredi à 15h52, une anomalie silencieuse commence à générer des ordres erronés — un bug de parsing de signal qui envoie des BUY au lieu de SELL, ou un dépassement du drawdown maximum autorisé. Sans mécanisme de coupe-circuit global, chaque worker continue d'exécuter ses propres ordres, aggravant les pertes minute après minute. Vous ne découvrez le problème qu'en consultant vos logs le soir.

Le **Kill Switch** est le fusible général de l'infrastructure. Il arrête TOUT, partout, immédiatement.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Redis Pub/Sub                        │
│              channel: "URGENCY"                       │
│  Messages: {"action": "suspend"} / {"action": "resume"}│
└──────────┬──────────────────────────┬────────────────┘
           │                          │
    ┌──────▼──────┐            ┌──────▼──────┐
    │ Worker A    │            │ Worker B    │
    │ KillSwitch  │            │ KillSwitch  │
    │ Listener    │            │ Listener    │
    └──────┬──────┘            └──────┬──────┘
           │                          │
    ┌──────▼──────────────────────────▼──────┐
    │       KillSwitchManager (per worker)    │
    │  - suspend_trading()                    │
    │  - cancel_all_pending_orders()          │
    │  - snapshot_positions()                 │
    │  - enter_close_only_mode()              │
    └─────────────────────────────────────────┘
```

---

## Composants

### 1. KillSwitchListener — Écoute Redis Pub/Sub

Le `KillSwitchListener` maintient une connexion persistante au canal Redis `URGENCY`. Configuration de résilience réseau imposée par §2.8 du référentiel technique :

```python
# TCP keepalive OS-level + health check Redis
listener = KillSwitchListener(
    redis_url=...,
    socket_keepalive=True,       # §2.8: contrer les déconnexions silencieuses
    health_check_interval=30,     # Ping Redis toutes les 30s
)
await listener.start()
```

**Cycle de vie** :
- **Connexion** → Subscribe au canal `URGENCY`
- **Message reçu** → Parse l'action (`suspend` / `resume`), appelle `KillSwitchManager`
- **Déconnexion** → Reconnecte automatiquement et silencieusement (`logger.info`, pas de traceback — §2.3)
- **Timeout Redis** → Logué comme warning, reconnexion automatique

### 2. KillSwitchManager — Orchestrateur de suspension

Point d'entrée unique par worker. Actions déclenchées à la réception d'un ordre `suspend` :

| Étape | Action | Timeout |
|:---|:---|:---|
| 1 | Marquer `_trading_suspended = True` (flag global) | Immédiat |
| 2 | Snapshot des positions ouvertes (PostgreSQL) | 10s |
| 3 | Cancel ALL pending orders (Trading 212 + Bybit) | 10s/broker |
| 4 | Persister l'état `KILL_SWITCH_ACTIVE` dans Redis | 5s |
| 5 | Écrire confirmation JSON dans `trading_audit.log` | - |
| 6 | Basculer en mode Close-Only (sorties autorisées, entrées bloquées) | Immédiat |

En cas d'échec d'annulation d'un broker, le message d'erreur est loggé mais ne bloque pas l'annulation de l'autre broker (§2.3 — isolation des erreurs par connecteur).

### 3. PersistentKillSwitchStateEnforcer — Persistance Redis

Garantit que l'état du Kill Switch survit aux redémarrages des workers. Utilise une clé Redis `kill_switch:state` avec une TTL configurable.

```
❌ Sans persistance Redis :
   Worker crash → redémarrage → le flag in-memory est perdu → trading reprend
   comme si de rien n'était.

✅ Avec PersistentKillSwitchStateEnforcer :
   Worker crash → redémarrage → lecture de Redis → Kill Switch toujours actif
   → le worker refuse toute nouvelle entrée.
```

---

## États et transitions

```
  NORMAL ──[suspend]──▶ SUSPENDED ──[resume]──▶ NORMAL
    │                      │
    │                      ├─ cancel_all_orders()
    │                      ├─ snapshot_positions()
    │                      └─ enter_close_only_mode()
    │
    └── [drawdown_limit / error_rate] ──▶ (déclenchement automatique)
```

### Déclencheurs automatiques

Le Kill Switch peut être activé automatiquement par :
- **Max Drawdown journalier** : défini dans `configs/risk_limits.json`
- **Taux d'erreur API** : si > N% des requêtes échouent sur une fenêtre glissante
- **Anomalie de fréquence** : si le nombre d'ordres/seconde dépasse le seuil configuré (§2.9)

### Déclenchement manuel

```bash
# Via Redis CLI
redis-cli PUBLISH URGENCY '{"action": "suspend", "source": "operator", "reason": "manual intervention"}'

# Reprise
redis-cli PUBLISH URGENCY '{"action": "resume", "source": "operator"}'
```

---

## Sécurité et invariants

| Règle | Implémentation |
|:---|:---|
| **§2.8 — TCP keepalive** | `socket_keepalive=True` + `health_check_interval=30` |
| **§2.3 — Isolation des erreurs** | Exception broker A n'annule pas broker B |
| **§2.3 — Pas de traceback sur déconnexion** | `logger.info` pour les timeouts Redis prévisibles |
| **§2.8 — Reconnexion automatique** | Boucle `while True` avec backoff exponentiel |
| **§2.9 — Close-Only après suspension** | Entrées bloquées, sorties autorisées |
| **Audit trail** | Chaque transition loggée en JSON structuré dans `trading_audit.log` |

---

## The Golden Rule

> **Règle d'or** : Un système de trading sans coupe-circuit distribué n'est pas un système de trading — c'est un pari. Le Kill Switch doit pouvoir arrêter TOUS les workers en moins d'une seconde, même si Redis est le seul point de coordination survivant.

---

## Références

- **Code source** : `backtest_engine/live/kill_switch.py` (465 LOC)
- **Audit sécurité** : `docs/audit/paper-trading-backend-2026-07-26.md`
- **Skill associé** : `execution-order-routing` — FSM d'ordre et idempotence
- **Skill associé** : `risk-money-management` — circuit breakers et drawdown limits
