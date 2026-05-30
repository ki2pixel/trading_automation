# Gestion multi-devises (Currency Conversion)

**TL;DR** : Toutes les stratégies supportent désormais la conversion dynamique des devises historiques. Ton capital en EUR est correctement converti face aux actifs cotés en USD (comme GMAB) grâce aux taux de change réels fournis à chaque transaction.

Tu as configuré ton compte de trading en Euros (EUR). Tu veux backtester ta stratégie HMA Crossover sur l'action américaine **GMAB**, dont les cours sont exprimés en Dollars (USD). 

Dans un moteur de backtest trop simple, une erreur silencieuse et catastrophique se produit : le moteur mélange les torchons et les serviettes. Il applique tes limites de capital (ex: un bucket maximal de 1 000 EUR) directement sur le prix en USD de l'action, calcule des commissions en dollars sans les convertir, et génère une courbe de capital finale fausse. Tu te retrouves avec des résultats impossibles à reproduire dans la réalité.

Pour résoudre ce problème, nous avons implémenté un système de conversion dynamique de devises en temps réel.

---

## Comment le système résout-il le problème ?

Le moteur s'appuie sur trois couches pour garantir des calculs exacts face à des actifs étrangers.

### 1. La détection automatique de la devise (Asset Discovery)
Chaque fois que tu lances un symbole, le moteur consulte une base de référence locale (`symbol_currency_map.csv`) pour identifier la devise d'origine de l'action (le dollar USD pour `GMAB`, le franc suisse pour d'autres, etc.).

### 2. Le fournisseur de taux historique (FX Rate Provider)
Si la devise de ton compte (EUR) diffère de celle de l'action (USD), le moteur va chercher le dataset canonique de taux de change correspondant (par exemple, le Parquet `USDEUR` dans `storage/processed/fx_data_5m/`) et instancie un module `fx_rate_provider`.

### 3. La conversion barre par barre
À chaque étape de la simulation (chaque bougie de 5 minutes) :
- Les cours de l'actif sont convertis dans la devise de ton compte pour calculer la valeur latente de ton portefeuille (Mark-to-Market).
- Les commissions et le slippage subissent la conversion de change au moment exact de l'exécution de l'ordre.
- La courbe de capital finale (`equity_curve.csv`) et toutes les métriques de profits et de drawdowns sont écrites et garanties dans la devise de ton compte (EUR).

---

## La structure technique du Wrapper multi-devises

Pour éviter de dupliquer cette logique complexe dans le code de chaque stratégie convertie de Pine Script, nous avons centralisé la résolution des devises dans un utilitaire commun appelé `setup_currency_and_fx_provider`.

### L'intégration dans les wrappers de stratégies
Chaque stratégie intègre cet appel lors de son initialisation :

```python
from ._currency_utils import setup_currency_and_fx_provider

# Résout dynamiquement les devises et instancie le taux FX historique
account_currency, asset_currency, fx_rate_provider = setup_currency_and_fx_provider(
    symbol=symbol,
    timeframe_minutes=timeframe_minutes,
    repo_root=repo_root,
    overrides=overrides,
)
```

Ces informations sont ensuite injectées directement dans le simulateur de courtage (`BrokerSimulator`) via sa configuration `BrokerConfig` pour qu'il applique les règles de change lors des ordres d'achat ou de vente.

---

## Statut d'implémentation et de validation

Toutes les stratégies historiques converties ont été migrées avec succès vers cette architecture multi-devises :
1. `hma_crossover`
2. `range_filter`
3. `3commas_bot`
4. `pmax_explorer`
5. `adaptive_volatility_trend`
6. `bjorgum_double_tap`
7. `noise_boundary_intraday` (notre stratégie de référence)

### Les tests de régression validés
Le comportement a été validé scientifiquement par notre suite de tests unitaires (`pytest tests/`) :
- **Assets en EUR** : Validation que les actions européennes tournent sans surcoût de calcul ni conversion FX inutile.
- **Assets en USD** : Validation que le chargement des taux de change historiques `USDEUR` s'effectue correctement et convertit fidèlement chaque transaction.
- **Paramètres de capital** : Validation que les limites en cash (`initial_capital_bucket`, etc.) s'appliquent bien dans la devise du compte (EUR) et non celle de l'action (USD).
- **Courbe d'équité** : Validation de la conformité de la courbe de capital finale.
- **Taux de réussite** : 100% des 202 tests unitaires de la suite passent avec succès.
