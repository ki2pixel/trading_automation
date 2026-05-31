# Synthèse : HMA Crossover

## Passe 1 : Signal HMA Brut

Les configurations suivantes ont été validées comme "sweet spots" lors de la Passe Unique. Elles sont verrouillées comme références définitives pour le signal de base, et serviront de socle si la stratégie venait à être enrichie (ex: ajout de gestion du risque ou de filtres de régime lors de futures passes optionnelles) :

### Actifs "Verts" (Performants)

- **GMAB - 30m**
  - **Paramètres** : `fast_len` = 27, `slow_len` = 110, `source_col` = "close", `confirm_on_close` = false

- **GMAB - 45m**
  - **Paramètres** : `fast_len` = 16, `slow_len` = 68, `source_col` = "close", `confirm_on_close` = false

### Actifs "Oranges" (Alternatives)

- **AMS.MC - 45m**
  - **Paramètres** : `fast_len` = 13, `slow_len` = 55, `source_col` = "high", `confirm_on_close` = true

- **NVO - 20m**
  - **Paramètres** : `fast_len` = 15, `slow_len` = 105, `source_col` = "close", `confirm_on_close` = true
