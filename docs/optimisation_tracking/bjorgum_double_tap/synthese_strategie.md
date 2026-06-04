# Synthèse Stratégique : bjorgum_double_tap

Ce document consolide les paramètres figés à l'issue des différentes passes d'optimisation.

## Paramètres validés après Passe 1 (Détection du Pattern)

**⚠️ AVERTISSEMENT : ÉCHEC DE LA PASSE 1**

À la suite de la Passe 1 (portant sur l'optimisation de `tol`, `length`, `dLong`, `dShort` avec `fib=100`, `stopPer=0`, `atrStop=false`), **aucun jeu de paramètres n'a été validé**.

L'ensemble des 1 858 itérations éligibles évaluées sur les actifs (notamment AMS.MC, NVS et SHL.DE) a retourné des scores de surperformance (Return vs Buy & Hold) systématiquement et fortement négatifs. Les autres actifs testés n'ont même pas généré de signaux éligibles (manque de trades ou conditions inatteignables).

### Conclusion

- **Aucun paramètre figé** : Le signal de base n'offrant aucun avantage statistique (edge), aucun paramètre n'a pu être promu pour les phases suivantes.
- **Statut de la stratégie** : Bloquée en l'état. Nécessite une révision de la logique de détection ou du filtrage avant de pouvoir envisager une Passe 2.
