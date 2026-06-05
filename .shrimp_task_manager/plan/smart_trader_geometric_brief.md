# Spécifications: Smart Trader Final Episode AI-Assisting Geometric Strategy

## 1. Description Générale
L'objectif est d'implémenter la stratégie géométrique "Smart Trader Final Episode" en Python, optimisée avec Numpy/Numba pour s'intégrer au backtest_engine. Cette stratégie transforme l'évolution des prix et du temps en un espace géométrique normalisé (ICS) pour identifier des compressions, rejets et alignements structurels sans lag.

## 2. Exigences Mathématiques et Composantes

### 2.1. Volatilité de Yang-Zhang (Sigma)
Calcul vectorisé de l'estimateur de volatilité Yang-Zhang sur la fenêtre de lookback. Il combine :
- Volatilité Overnight (Close to Open)
- Volatilité Open to Close
- Volatilité de la session
Ce `sigma` sert à normaliser l'axe des prix.

### 2.2. Isotropic Coordinate System (ICS)
Les coordonnées doivent être dimensionnellement compatibles :
- Déplacement vertical (`dy`) : `log(price) / sigma`
- Déplacement horizontal (`dx`) : `bars_since_anchor / lookback` (lookback par défaut = 23)

### 2.3. Ancres Gelées (Frozen Anchors)
Lorsqu'un cycle commence (ou se réinitialise), on fige :
- **Ceiling** : Highest High sur le lookback
- **Floor** : Lowest Low sur le lookback
- **Center** : Moyenne géométrique `sqrt(Ceiling * Floor)`
L'ancre est invalidée et réinitialisée si le prix de clôture casse le Ceiling ou le Floor.

### 2.4. Les 5 Triangles
Calculés à chaque barre depuis la dernière ancre gelée :
1. **Ceiling** : Du Ceiling gelé au High actuel.
2. **Center** : Du Center gelé à la moyenne géométrique (H*L)^0.5 actuelle.
3. **Floor** : Du Floor gelé au Low actuel.
4. **Pin Up** : Mesure la mèche supérieure relative au Ceiling.
5. **Pin Down** : Mesure la mèche inférieure relative au Floor.

### 2.5. Les 4 Métriques (20 Lentilles Géométriques)
Pour chaque triangle :
- **Angle** : `atan(dy/dx) * 180/pi`
- **Distance** : `dy`
- **Area** : `0.5 * |dy| * |dx|`
- **Centroid** : Point d'équilibre géométrique en Y.

### 2.6. Logique de Quorum et Signaux (Slots)
- Un système de "Slots" configure des conditions (ex: Floor Angle > 0, Ceiling Area cross < 20).
- **Quorum Logic** : Si un nombre requis (Minimum slots required) de slots actifs est validé pour l'entrée Long ou Short, un signal est généré.
- Logique vectorisée et stricte (pas de boucles Python lentes, zéro-copie favorisé).

## 3. Contraintes d'Architecture
- Doit respecter les directives d'optimisation `architecte.md` et `linus.md`.
- Vectorisation Pandas/Numpy indispensable.
- Numba pour les calculs géométriques et la détection dynamique d'ancres si Pandas n'est pas suffisant.
- Les tests unitaires doivent valider rigoureusement l'isotropie (ICS) et la détection des triangles.
