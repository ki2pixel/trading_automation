# Synthèse Stratégique : Smart Trader Geometric

Ce document consolide les paramètres figés à l'issue des différentes passes d'optimisation pour la stratégie géométrique.

## Paramètres validés après Passe 2 (Risk Management)

Les configurations suivantes intègrent les paramètres structurels de base figés en Passe 1 (Géométrie Core) et le Risk Management asymétrique validé en Passe 2 (Net Bracket Exits).
Pour toutes ces configurations de production : `signal_mode` = "Close", `use_safety_stop` = false, `use_net_bracket_exits` = true, `min_long_entry_slots` = 1, `stop_loss_net_percent` = 1.0.

### ZEAL.CO
- **5m** : `lookback_period` = 12, `take_profit_net_percent` = 12.0
- **10m** : `lookback_period` = 23, `take_profit_net_percent` = 12.0

### LOGI
- **5m** : `lookback_period` = 13, `take_profit_net_percent` = 8.0

## Setups En Attente (Issus de la Passe 1 - Neutres/Modérés)

Les configurations ci-dessous nécessitent une gestion stricte du risque ou ont été mises en attente à l'issue de la Passe 1. Pour ces actifs : `use_net_bracket_exits` = false, `use_safety_stop` = false.

### EVD.DE
- **15m** : `lookback_period` = 10
- **10m** : `lookback_period` = 15

### SHL.DE
- **30m** : `lookback_period` = 14