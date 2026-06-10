# Classification de Lorentz (KNN)

**TL;DR**: La stratégie de classification de Lorentz utilise un classifieur de plus proches voisins (KNN) adapté pour prédire la direction du marché; en déformant l'espace métrique via une distance lorentzienne et en filtrant les signaux par régression de Nadaraya-Watson, elle élimine le bruit inhérent aux métriques Euclidiennes classiques.

---

## Le Problème de la Distance dans les Données Financières

Vous tentez d'entraîner un modèle K-Nearest Neighbors (KNN) classique pour classer vos signaux de trading. Vous normalisez vos features: le RSI, l'ADX et le CCI. Vous utilisez la distance euclidienne standard pour trouver les situations historiques les plus similaires. 

C'est là que vous rencontrez un obstacle majeur: dans les marchés financiers, les variables ne se comportent pas de manière linéaire ou uniforme. Un pic de volatilité extrême sur l'ADX peut étirer artificiellement la distance euclidienne globale, masquant le fait que la structure sous-jacente du RSI et du CCI est identique à un événement historique clé. La distance euclidienne suppose un espace plat et symétrique; hors, les marchés financiers sont remplis de distorsions et de valeurs aberrantes qui faussent les calculs de similarité.

---

## Les Concepts Clés

### La Déformation Spatiale de Lorentz (Lorentzian Space Warp)
Au lieu d'utiliser une ligne droite (Euclidienne) pour mesurer l'écart entre deux points de features, la distance de Lorentz applique une échelle logarithmique. Les petites différences de features sont préservées, tandis que l'impact des valeurs extrêmes ou aberrantes est compressé. Cela permet de conserver une similarité structurelle même lors de variations anormales du marché.

### Le Lissage de Nadaraya-Watson (Rational Quadratic Kernel)
Pour éviter les signaux hachés générés par les prédictions KNN brutes, la stratégie intègre une régression non-paramétrique. Ce filtre calcule une moyenne pondérée dans le temps des prédictions passées, donnant une importance exponentiellement plus faible aux bougies éloignées. Il fait office de filtre passe-bas temporel tout en préservant la causalité.

### Le Piège de la Dimension Plate (The Flat Dimension Trap)
Vouloir optimiser séparément tous les paramètres d'une stratégie de Machine Learning sur Optuna conduit à une explosion combinatoire ingérable. La solution consiste à utiliser un pré-scan vectorisé avec le Bridge VectorBT pour isoler les plages de paramètres cohérentes avant d'affiner précisément la stratégie.

---

## Comparaison des Métriques Spatiales

### ❌ La Distance Euclidienne Standard
La métrique euclidienne est sensible aux valeurs aberrantes de features (ex: pic soudain de CCI ou d'ADX); elle sur-pondère les grands écarts isolés:

$$d_{Euclidienne} = \sum_{i=1}^{n} (f_{1,t} - f_{1,i})^2$$

### ✅ La Distance de Lorentz
La métrique lorentzienne applique une fonction logarithmique qui compresse l'effet des grands écarts, rendant le KNN robuste face au bruit macro:

$$d_{Lorentz} = \sum_{i=1}^{n} \ln(1 + |f_{1,t} - f_{1,i}|)$$

---

## Implémentation Logicielle et Optimisation

Le calcul de la similarité KNN sur un historique de plusieurs milliers de bougies (`max_bars_back = 2000`) est extrêmement coûteux. C'est pourquoi la stratégie est structurée en trois niveaux de performance:

1.  **Feature Ingestion (Pandas/VectorBT)**: Calcul vectorisé et rapide des 5 features de base (RSI, WaveTrend, CCI, ADX).
2.  **KNN Kernel (Numba JIT)**: Exécution compilée `@njit` de la recherche de voisins lorentziens. La boucle de recherche sur les 2 000 dernières bougies s'exécute en C pur sans surcharge Python.
3.  **Multiprocessing (SHM)**: Partage des données de prix en mémoire partagée via `/dev/shm` pour permettre aux workers d'Optuna de s'attacher aux mêmes tableaux Numpy sans duplication.

---

## Compromis Techniques

| Métrique de Similarité | Sensibilité au Bruit | Vitesse d'Exécution | Capacité de Généralisation |
| :--- | :--- | :--- | :--- |
| **Euclidienne standard** | ❌ Très élevée (valeurs aberrantes) | ✅ Très rapide (calcul direct) | ❌ Faible (overfitting rapide) |
| **Lorentzienne** | ✅ Faible (effet logarithme) | ❌ Moyenne (Numba requis) | ✅ Excellente (zones robustes) |

---

## La Règle d'Or: Compressez l'Espace, Lissez le Temps

> **Règle d'Or**: Utilisez une géométrie non-linéaire (Lorentz) pour regrouper vos features et une régression causale (Nadaraya-Watson) pour valider vos signaux temporels.
