# Pipeline de Conversion USDC → EUR (Bybit Spot)

**TL;DR**: Un pipeline transactionnel en 3 étapes — AccumulatorBuffer → MarginSimulator → SpotConversionRouter — qui accumule le PnL des trades Bybit en USDC, vérifie la marge UTA disponible, puis convertit en EUR via un ordre Spot avec FSM d'idempotence et journal d'audit JSON. Tout est en `Decimal` (§2.2).

---

Vous tradez sur Bybit EU en USDC. Chaque trade génère un PnL en stablecoin. Mais votre compte de référence (Trading 212) est libellé en EUR. Vous devez régulièrement convertir ces USDC en EUR pour les réinvestir ou les retirer. Le faire manuellement est fastidieux. Le faire automatiquement sans vérification de marge est dangereux — un ordre de conversion peut faire basculer votre compte UTA sous le seuil de maintenance et déclencher une liquidation.

Ce pipeline résout les deux problèmes : il automatise la conversion tout en garantissant que l'opération ne met jamais en péril votre compte.

---

## Architecture

```
 Trade SELL Bybit (PnL USDC)
           │
           ▼
┌─────────────────────────┐
│  1. AccumulatorBuffer   │  ← Accumule les +values USDC
│     .deposit(amount)    │     Seuil de déclenchement: 15 USDC
│     .should_trigger()   │
└───────────┬─────────────┘
            │ trigger = True
            ▼
┌─────────────────────────┐
│  2. MarginSimulator     │  ← Vérifie l'état UTA
│     .check_conversion() │     MMR check > 1.2x (§2.9)
│     → MarginCheckResult │
└───────────┬─────────────┘
            │ is_safe = True
            ▼
┌─────────────────────────────────────────────┐
│  3. SpotConversionRouter                     │
│     .create_order()   → ConversionOrder     │
│     .submit_order()   → FSM PENDING→SUBMITTED│
│     .reconcile_order() → RECONCILIATION      │
│     .on_fill()        → SUBMITTED→FILLED     │
│     .drain_accumulator() → Buffer vidé       │
└─────────────────────────────────────────────┘
```

---

## 1. AccumulatorBuffer — Le compte épargne USDC

### Pourquoi un buffer

Convertir chaque micro-profit de 0.50 USDC individuellement multiplierait les frais de transaction et noierait le compte dans des micro-ordres. L'accumulateur attend que le solde USDC atteigne un seuil avant de déclencher la conversion.

### Mécanique

```python
buffer = AccumulatorBuffer(source="bybit", trigger_threshold=Decimal("15.00"))

# Appelé dans la même transaction PostgreSQL que le SELL
buffer.deposit(conn, amount=Decimal("3.42"))  # PnL net du trade

if buffer.should_trigger(conn):
    # Solde >= 15 USDC → déclenchement
    router.initiate_conversion(conn, buffer)
```

| Paramètre | Valeur | Description |
|:---|:---|:---|
| `source` | `"bybit"` | Identifiant du buffer dans PostgreSQL |
| `trigger_threshold` | `Decimal("15.00")` | Seuil USDC pour déclencher la conversion |

### Persistance et cohérence transactionnelle

Le buffer est **persisté dans PostgreSQL** (table `conversion_accumulator`) dans la **même transaction** que l'enregistrement du PnL du trade. Conformément à §2.4 :

> *Le staging pipeline Redis (prix live) doit être exécuté STRICTEMENT APRÈS le commit de la transaction PostgreSQL pour éviter d'alimenter le cache avec des données non commitées.*

```python
# Dans signal_executor.py:
with conn:  # transaction PostgreSQL
    record_trade(conn, pnl)
    accumulator.deposit(conn, pnl)   # MÊME transaction
    # Commit → puis MAJ Redis
```

Le `drain()` (vidage après conversion réussie) utilise `SELECT ... FOR UPDATE` pour verrouiller la ligne et éviter les doubles conversions.

---

## 2. MarginSimulator — Le check de solvabilité

### Pourquoi simuler

Avant de soumettre un ordre de conversion, il faut vérifier que le compte UTA restera au-dessus du seuil de maintenance **après** la conversion. Le simulateur interroge l'état réel du compte Bybit puis modélise l'impact de la conversion.

### Données

```python
class MarginState(NamedTuple):
    total_equity: Decimal           # Équité totale du compte
    total_maintenance_margin: Decimal  # Marge de maintien actuelle
    available_balance: Decimal       # Solde disponible

class MarginCheckResult(NamedTuple):
    margin_state: MarginState
    required_minimum: Decimal        # MMR × 1.2 (seuil de sécurité)
    is_safe: bool                    # Conversion possible ?
    reason: str                      # Explication si bloqué
    post_conversion_equity: Decimal  # Équité après conversion
    headroom: Decimal                # Marge de sécurité restante
```

### Règle de sécurité

Conformément à §2.9 : **MMR check > 1.2x**. La conversion est bloquée si l'équité post-conversion est inférieure à 1.2x la marge de maintenance :

```python
# ❌ Bloqué: équité post-conversion < 1.2 × MMR
if post_equity < maintenance_margin * Decimal("1.2"):
    return MarginCheckResult(
        is_safe=False,
        reason=f"Post-conversion equity {post_equity} < 1.2× MMR {required}",
        ...
    )
```

### Verrou post-rejet

Après 3 rejets consécutifs pour marge insuffisante, un **cooldown lock** de 60 secondes est activé (`is_locked()`) pour éviter de spammer l'API Bybit avec des checks inutiles. Le verrou se libère automatiquement après expiration.

---

## 3. SpotConversionRouter — La FSM d'exécution

### ConversionOrder : la machine à états

```
PENDING ──[submit]──▶ SUBMITTED ──[fill]──▶ FILLED
                         │                    │
                         ├──[timeout >1m]──▶ RECONCILIATION_PENDING
                         │                         │
                         │                    ┌────┴────┐
                         │               [found]    [not found]
                         │                    │          │
                         │               FILLED/     FAILED
                         │               CANCELED
                         │
                         ├──[api error]──▶ REJECTED
                         └──[unexpected]──▶ FAILED
```

### Idempotence via client_order_id

Chaque `ConversionOrder` génère un UUID v4 de 36 caractères comme `client_order_id` (alias `orderLinkId` Bybit). Conformément à §2.8 et au skill `execution-order-routing` :

```python
@dataclass
class ConversionOrder:
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    broker_order_id: Optional[str] = None

    def to_bybit_payload(self) -> dict:
        return {
            "category": "spot",
            "symbol": self.symbol,       # "EURUSDC"
            "side": self.side,           # "Buy" (Buy EUR with USDC)
            "orderType": self.order_type,  # "Market"
            "qty": str(self.qty_usdc),
            "marketUnit": "quoteCoin",   # qty interprétée en USDC
            "orderLinkId": self.client_order_id,  # UUID → idempotence
        }
```

### Réconciliation post-timeout

Si l'ordre reste en `SUBMITTED` plus de 60 secondes, le routeur passe en `RECONCILIATION_PENDING` et interroge l'API Bybit pour retrouver le statut réel :

```python
# J1-FIX: max 10 tentatives de réconciliation avant FAILED forcé
if order.status == ConversionOrderStatus.SUBMITTED:
    elapsed = (datetime.now(timezone.utc) - order.submitted_at).total_seconds()
    if elapsed > 60:
        order.status = ConversionOrderStatus.RECONCILIATION_PENDING
        order.reconciliation_attempts += 1
        if order.reconciliation_attempts > order.max_reconciliation_attempts:
            order.status = ConversionOrderStatus.FAILED
            order.error_message = "Max reconciliation attempts exceeded"
```

C'est l'implémentation directe du principe §2.8 : *"Toute tentative de rejeu doit être précédée d'une interrogation de statut d'ordre auprès du broker."*

### Flux complet

```python
router = SpotConversionRouter(bybit_client, margin_simulator, accumulator)

# Étape 1: Créer l'ordre
order = router.create_order(qty_usdc=Decimal("15.00"))

# Étape 2: Vérifier la marge
margin_check = router.simulator.check_conversion(order)
if not margin_check.is_safe:
    router.log_blocked(order, margin_check)  # Audit JSON + PostgreSQL
    return

# Étape 3: Soumettre (FSM: PENDING → SUBMITTED)
await router.submit_order(order)

# Étape 4: Réconcilier si nécessaire
await router.reconcile_if_needed(order)

# Étape 5: Drainer l'accumulateur si FILLED
if order.status == ConversionOrderStatus.FILLED:
    router.drain_accumulator(order)  # Buffer → 0, conversion_id persisté
```

### Journal d'audit

Chaque conversion bloquée par la marge est loggée en JSON structuré :

```json
{
    "timestamp": "2026-07-27T10:15:30Z",
    "event": "CONVERSION_BLOCKED",
    "order_id": "blocked-20260727101530-a1b2c3d4",
    "ticker": "EURUSDC",
    "reason": "Post-conversion equity 1245.00 USDC < 1.2× MMR 1560.00 USDC",
    "maintenance_margin": "1300.00",
    "available_balance": "245.00"
}
```

---

## Trade-offs

| Approche | Avantage | Inconvénient |
|:---|:---|:---|
| **Buffer avec seuil** | Réduit les frais de transaction, évite les micro-ordres | Délai entre le PnL et la conversion effective |
| **Simulation de marge** | Protection contre la liquidation, pas d'appel API inutile | Complexité du modèle UTA |
| **FSM avec réconciliation** | Survit aux crashs et timeouts réseau | Code plus verbeux qu'un simple appel async |
| **client_order_id UUID** | Idempotence garantie, pas de double spend | 36 caractères dans les logs |

---

## The Golden Rule

> **Règle d'or** : Aucun USDC ne quitte le compte sans que le simulateur de marge n'ait validé que l'équité post-conversion restera au-dessus de 1.2x la marge de maintenance. Le PnL est enregistré, le buffer est alimenté, la marge est vérifiée, l'ordre est soumis — dans cet ordre, dans une transaction atomique.

---

## Références

- **Code source** :
  - `backtest_engine/live/bybit/conversion/accumulator.py` (121 LOC)
  - `backtest_engine/live/bybit/conversion/order_types.py` (79 LOC)
  - `backtest_engine/live/bybit/conversion/spot_router.py` (482 LOC)
  - `backtest_engine/live/bybit/conversion/margin_simulator.py` (187 LOC)
- **§2.2 AGENTS.md** : Précision financière `Decimal`
- **§2.4 AGENTS.md** : Séquencement PostgreSQL → Redis
- **§2.8 AGENTS.md** : Idempotence et réconciliation
- **§2.9 AGENTS.md** : Pre-Trade Checks, MMR > 1.2x
- **Skill associé** : `execution-order-routing` — FSM et idempotence
- **Skill associé** : `risk-money-management` — simulateur de marge
