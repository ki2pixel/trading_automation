# Configurer tes simulations : Au-delà des simples chiffres

**TL;DR** : La configuration ne sert pas juste à lister tes indicateurs. Elle te permet d'aligner tes backtests sur la réalité économique du marché (commissions, slippage, gestion des risques) tout en évitant la duplication de code grâce à l'héritage centralisé de notre V3.

Quand on configure un robot de trading, le premier réflexe est de chercher les "bons" paramètres pour les indicateurs : une longueur de moyenne mobile plus ou moins longue, un multiplicateur de volatilité plus ou moins sensible. 

C'est une erreur classique de négliger les réglages du simulateur lui-même. Tu peux avoir le meilleur signal mathématique du monde, si tu oublies de paramétrer tes frais réels, ton backtest va te faire croire que tu es millionnaire alors que tes bénéfices se feront dévorer par les intermédiaires financiers en quelques jours.

Voici la philosophie derrière nos configurations et comment adapter tes fichiers JSON.

---

## Pourquoi les frais et le slippage décident de ta survie ?

Chaque fois que ta stratégie décide d'ouvrir ou de fermer une position, tu dois payer un tribut au monde réel. Nos fichiers de configuration intègrent ces paramètres au même titre que tes indicateurs.

### 1. La commission (`commission`)
Que ce soit un pourcentage de la transaction ou un montant fixe par ordre, les frais de transaction s'accumulent à chaque trade. Une stratégie active qui prend 5 trades par jour sur un capital moyen peut perdre jusqu'à 30% de sa performance annuelle uniquement en frais de courtage. 

### 2. Le slippage (`slippage`)
Sur les graphiques théoriques, tu achètes toujours au cours de clôture exact de la barre. En réalité, le temps que ton ordre arrive sur le marché, le prix a bougé. Sur des actions ou des crypto-monnaies très volatiles en intraday, tu achètes souvent un peu plus cher que prévu et vends un peu moins cher. C'est le slippage. Paramétrer un slippage réaliste (par exemple 0.1% ou quelques centimes par action) est la différence entre un test scientifique et un vœu pieux.

---

## L'héritage des paramètres communs (La puissance de la V3)

Pour t'éviter de devoir copier-coller les mêmes réglages de commissions, de slippage et de coupe-circuit dans les fichiers de chaque stratégie, notre moteur utilise un système d'héritage centralisé dans `backtest_engine/configuration.py`.

### Comment ça marche ?
Tous les paramètres transversaux sont définis dans un dictionnaire global nommé `COMMON_V3_PARAMETERS`. 
Chaque stratégie (qu'il s'agisse de HMA Crossover ou d'AVT) importe ces définitions en une seule ligne dans son code :

```python
# Un seul point d'entrée pour la configuration globale
HMA_PARAMETER_DEFINITIONS: dict[str, StrategyParameterDefinition] = {
    "fast_len": StrategyParameterDefinition(...),
    "slow_len": StrategyParameterDefinition(...),
    **get_v3_parameters(),  # Récupération automatique de tous les paramètres communs
}
```

### La personnalisation par stratégie
Ce système n'est pas rigide. Si une stratégie spécifique nécessite d'ignorer certaines règles globales, la fonction `get_v3_parameters()` accepte deux options d'ajustement :
- `exclude` : Pour retirer un paramètre non pertinent (par exemple, désactiver la Next-Bar Execution pour une stratégie purement basée sur les cours de clôture).
- `overrides` : Pour modifier localement la valeur par défaut ou le caractère optimisable d'un paramètre commun.

Cette architecture te garantit qu'en ajoutant une nouvelle règle de sécurité globale (comme un stop suiveur dynamique ou un filtre d'heure d'ouverture), elle sera instantanément disponible pour toutes tes stratégies.

---

## Les blocs de paramètres en pratique

Tes fichiers JSON de configuration (dans `configs/strategies/`) contiennent deux types de variables :

### 1. Les variables spécifiques à ton indicateur
Ce sont les leviers mathématiques de ta formule. Par exemple :
- **HMA Crossover** : Les longueurs HMA (`fast_len`, `slow_len`) et la confirmation à la clôture (`confirm_on_close`).
- **Adaptive Volatility Trend (AVT)** : La sensibilité ATR (`atr_mult`), le filtre RSI (`use_rsi_filter`) et le score de signal minimal (`min_signal_score`).
- **Range Filter** : Le multiplicateur de canal (`range_multiplier`) et la période d'échantillonnage (`sampling_period`).
- **3Commas Bot** : Le paramètre de risque (`rnr`), le Stop Loss suiveur (`trail_stop`) et le ratio de sortie R:R (`rr_exit`).
- **PMax Explorer** : Le lissage de la tendance (`pmax_smoothing`) et son multiplicateur (`pmax_multiplier`).
- **Bjorgum Double Tap** : Le lookback et les coefficients de l'ATR pour détecter les rebonds.
- **Noise Boundary Intraday** : Le coefficient de volatilité d'entrée (`volatility_multiplier_enter`) et les horaires de trading intraday.

### 2. Les variables communes de gestion des risques
Elles gèrent la vie de tes trades une fois le signal détecté :
- **Le Bucket de Capital** (`max_capital_bucket`, `initial_capital_bucket`) : Pour limiter l'exposition maximale de ton portefeuille sur une seule idée de trade.
- **Le sens de trading** (`trade_direction_mode`) : Pour autoriser uniquement les positions Longs, Shorts, ou les deux.
- **Les sorties de secours** (`use_net_bracket_exits`, `take_profit_net_percent`, `stop_loss_net_percent`) : Des objectifs fermes de gains ou de pertes calculés nets de frais.

---

## Ajuster à la volée depuis le terminal

Souviens-toi d'une règle d'or : **le terminal a toujours le dernier mot**. 

Si ton fichier JSON contient des frais à 0.1% mais que tu lances ton exécution avec `--estimated-commission-per-order-long 1`, le moteur utilisera la valeur fournie dans ton terminal. C'est l'outil parfait pour tester des scénarios "catastrophe" à la volée sans modifier tes fichiers de configuration de référence.
