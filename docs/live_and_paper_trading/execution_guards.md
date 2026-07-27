# Execution Guards — Garde-fous d'Exécution Pre-Trade

**TL;DR**: Deux garde-fous synchrones exécutés avant chaque routage d'ordre — le **Max Entry Price (MEP)** plafonne le prix d'entrée à un pourcentage du close précédent, et le **Minimum Holding Period (MHP)** bloque les sorties trop rapides. Tous deux utilisent `Decimal` pour la précision financière (§2.2).

---

Vous avez optimisé une stratégie de breakout sur 3 ans d'historique. Le backtest montre un ratio de Sharpe de 2.1. Vous la déployez en Paper Trading. Dès la première semaine, vous remarquez des entrées aberrantes : un signal BUY sur NOVNs_EQ à 98.50 CHF alors que le close précédent était à 87.20 CHF (+13% de gap). Votre stratégie entre, le prix se normalise, et vous prenez -8% sur un trade qui n'aurait jamais dû être exécuté.

Le problème ? Votre stop-loss et votre sizing étaient parfaits dans le backtest, mais personne n'a vérifié le **prix d'entrée lui-même** avant de router l'ordre. Les execution guards comblent exactement cette lacune.

---

## 1. Max Entry Price Guard (MEP)

### Pourquoi ce garde-fou

Le MEP empêche d'entrer sur un actif dont le prix a gapé anormalement par rapport à sa clôture précédente. C'est la première ligne de défense contre :

- Les gaps de week-end sur les actions européennes
- Les anomalies de pricing intraday (flash spikes)
- Les signaux générés sur des données corrompues

### Mécanique

```python
# Pour chaque signal BUY:
prev_close = get_prev_close(ticker, df_1m)  # via cache (ticker, date)
max_allowed = prev_close * Decimal("1.05")    # +5% par défaut

if current_price > max_allowed:
    # ❌ REJET: le prix a gapé de plus de 5%
    raise MaxEntryPriceExceeded(
        ticker=ticker,
        current=current_price,
        prev_close=prev_close,
        max_allowed=max_allowed,
    )
```

| Paramètre | Défaut | Description |
|:---|:---|:---|
| `buffer_pct` | `Decimal("0.05")` (+5%) | Pourcentage au-dessus du close précédent |
| `strict_mode` | `False` | Si `True`, rejette aussi les prix *inférieurs* de plus de `buffer_pct` |

### Cache des closes précédents

Pour éviter des requêtes PostgreSQL à chaque tick, le MEP maintient un cache local :

```python
_prev_close_cache: dict[tuple[str, date], Optional[Decimal]] = {}

# Clé: (ticker, date)
# Valeur: close précédent ou None si non disponible
# Invalidation: au changement de jour UTC
```

Le close précédent est obtenu depuis les données 1-minute déjà en mémoire (colonne `close` du DataFrame à J-1). Pas de requête externe → pas de latence.

### Comportement en cas d'absence de données

Si le close précédent est indisponible (nouvel actif, jour férié) : **fail-open**. Le MEP loggue un warning et laisse passer l'ordre. Principe : ne jamais bloquer un trade légitime à cause d'une lacune de données.

---

## 2. Minimum Holding Period Guard (MHP)

### Pourquoi ce garde-fou

Le MHP empêche le "flip-flop" — ces situations où un signal d'entrée est immédiatement suivi d'un signal de sortie sur la bougie suivante, souvent à cause de bruit de marché ou d'un indicateur instable. Le résultat ? Des frais de transaction pour un PnL nul ou négatif.

### Mécanique

```python
# Pour chaque signal SELL:
bars_since = count_bars_since_entry(agg_index, opened_at, last_closed_time)

if bars_since < min_holding_bars:  # défaut: 3 barres
    # ❌ BLOQUÉ: période de holding minimum non atteinte
    return HoldingPeriodBlocked(
        ticker=ticker,
        bars_held=bars_since,
        required=min_holding_bars,
    )
```

| Paramètre | Défaut | Description |
|:---|:---|:---|
| `min_holding_bars` | `3` | Nombre minimum de bougies fermées avant sortie autorisée |
| `timeframe` | Auto-détecté | 1m, 5m, 15m, 45m, etc. |

### Calcul du nombre de barres

```python
def count_bars_since_entry(
    agg_index: pd.DatetimeIndex,
    opened_at: datetime,
    last_closed_time: datetime,
) -> int:
    opened_at = opened_at.replace(tzinfo=timezone.utc)
    after_entry = agg_index[agg_index > opened_at]
    closed_bars = after_entry[after_entry <= last_closed_time]
    return len(closed_bars)
```

Le calcul est strict : seules les barres **complètement fermées** (dont le timestamp est ≤ `last_closed_time`) sont comptabilisées. Une bougie en cours n'est jamais comptée.

### Fail-open pour les positions legacy

Les positions ouvertes avant l'introduction du MHP (ou sans `opened_at` renseigné) ne sont **jamais bloquées** :

```python
if min_holding_bars <= 0 or opened_at is None:
    return False  # fail-open pour les positions legacy
```

---

## ❌/✅ Comparaison : avec vs sans Execution Guards

### ❌ Sans guard: entrée sur gap

```python
# Signal BUY sur NVS à 98.50 (close précédent: 87.20, +13%)
signal = {"ticker": "NVS", "action": "BUY", "price": 98.50}
executor.route(signal)  # → Ordre exécuté, -8% de perte immédiate
```

### ✅ Avec MEP: rejet précoce

```python
# Même signal, mais MEP actif avec buffer_pct=0.05
guard = MaxEntryPriceGuard(buffer_pct=Decimal("0.05"))
result = guard.check(ticker="NVS", price=Decimal("98.50"), df_1m=df)
# → Rejected: 98.50 > 91.56 (87.20 × 1.05)
# L'ordre n'atteint jamais l'API du broker.
```

---

## Intégration dans le pipeline

```
Signal généré
     │
     ▼
┌─────────────────────┐
│ 1. MEP Check        │  ← Rejet si gap > buffer_pct
├─────────────────────┤
│ 2. MHP Check (SELL) │  ← Rejet si holding < min_bars
├─────────────────────┤
│ 3. Margin Check     │  ← §2.9: simulateur de marge UTA
├─────────────────────┤
│ 4. Circuit Breakers │  ← Kill Switch, max exposure
├─────────────────────┤
│ 5. Route Order      │  ← API broker
└─────────────────────┘
```

Les checks sont **synchrones et séquentiels** — si l'étape 1 échoue, les étapes 2-5 ne sont jamais exécutées. C'est le pattern Fail-Fast exigé par §2.2.

---

## Précision financière

Tous les calculs de prix utilisent `decimal.Decimal` conformément à §2.2 :

```python
# ✅ Correct
buffer = prev_close * Decimal("0.05")
max_price = prev_close + buffer

# ❌ Interdit: float pour les calculs financiers
buffer = float(prev_close) * 0.05  # erreur d'arrondi flottant
```

L'ATR (Average True Range), bien que calculé en `float` pour la performance vectorisée, est converti en `Decimal` avant d'alimenter le MEP.

---

## The Golden Rule

> **Règle d'or** : Chaque signal doit franchir les garde-fous dans l'ordre — prix d'entrée, période de holding, marge — avant même que l'identifiant d'ordre (orderLinkId) ne soit généré. Une validation ratée à l'étape N ne doit jamais atteindre l'étape N+1.

---

## Références

- **Code source** : `backtest_engine/live/paper_trading/execution_guards.py` (244 LOC)
- **§2.2 AGENTS.md** : Précision financière — `Decimal` obligatoire pour le live/paper trading
- **§2.9 AGENTS.md** : Pre-Trade Checks — vérification synchrone obligatoire
- **Skill associé** : `execution-order-routing` — routage d'ordres et FSM
