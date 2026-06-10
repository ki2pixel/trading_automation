# Filtre de Régime HMM (Modèle de Markov Caché)

**TL;DR**: La stratégie HMM Regime Filter utilise un modèle de Markov caché récursif pour classer l'état macro du marché en trois catégories (Bull, Bear, Range); en intégrant une inertie d'état (stickiness) et des fenêtres de confirmation temporelles, elle élimine les faux signaux de transition de régime.

---

## Le Problème de l'Oscillation des Régimes (Whipsaw)

Vous développez une stratégie hybride: suivi de tendance en marché directionnel et retour à la moyenne (mean-reversion) en marché neutre. Vous décidez d'utiliser un modèle statistique de Markov pour identifier dynamiquement ces phases. Lors de vos premiers tests historiques, tout semble parfait. 

Puis, vous lancez le modèle sur des données récentes. Le marché entre dans une phase d'hésitation à court terme. À chaque bougie alternativement verte et rouge, votre modèle HMM change de prédiction: il passe de l'état haussier (Bull) à l'état neutre (Range), puis baissier (Bear), avant de revenir au point de départ. Votre algorithme de trading ouvre et ferme des positions en permanence (whipsaw), accumulant des frais de courtage catastrophiques et détruisant votre capital sur de simples micro-fluctuations.

---

## Les Concepts Clés

### Le Whipsaw de Transition (Transition Whipsaw)
C'est le phénomène de sauts d'états ultra-rapides se produisant lorsque les probabilités de deux états (ex: haussier et neutre) sont proches de 0.5. Sans mécanisme de stabilisation, la prédiction oscille de manière chaotique.

### L'Inertie d'État (State Inertia ou Stickiness)
Pour empêcher le modèle de réagir au bruit de court terme, la matrice de probabilité de transition intègre un coefficient d'inertie (`stick`). Ce coefficient sur-pondère la probabilité de rester dans le même état d'une bougie à l'autre, exigeant une force statistique significative pour valider un changement.

### La Fenêtre de Confirmation (Confirmation Window)
Une fois qu'une transition d'état franchit le seuil de probabilité majoritaire (`dom_thresh`), elle n'est pas exécutée immédiatement. Le filtre impose un nombre minimal de barres consécutives (`confirm_bars`) confirmant le nouvel état avant de modifier l'exposition réelle du portefeuille.

---

## Modélisation Temporelle des Transitions

### ❌ Transition Sans Inertie
Dans un modèle naïf, le changement d'état se produit au premier croisement de probabilité, provoquant des allers-retours incessants:

```
[ Probabilité Bull: 0.51, Range: 0.49 ] -> État Bull (Achat)
[ Probabilité Bull: 0.48, Range: 0.52 ] -> État Range (Vente / Neutre)
[ Probabilité Bull: 0.53, Range: 0.47 ] -> État Bull (Achat de nouveau)
```

### ✅ Transition Avec Inertie et Confirmation
Avec une inertie active (`stick = 0.90`) et une confirmation (`confirm_bars = 2`), le modèle filtre les bruits passagers:

```
[ Probabilité Bull: 0.51 ] -> Inertie appliquée -> Reste en Range (Pas d'action)
[ Probabilité Bull: 0.65 ] -> Changement d'état détecté -> En attente de confirmation
[ Bougie 2: État haussier confirmé ] -> Confirmation validée -> Transition vers Bull (Achat)
```

---

## Logique Mathématique de la Stratégie

Le filtre de régime HMM s'exécute à l'aide de calculs récursifs vectorisés compilés en Numba (`_hmm_regime_filter_1d_nb`) pour éliminer tout lag d'exécution:

1.  **Calcul de la Volatilité Relative**: Mesure du log-rendement normalisé sur la fenêtre d'observation (`obs_len`).
2.  **Estimation des Vraisemblances**: Évaluation probabiliste de la dispersion par rapport à la moyenne statistique (`stat_len`) pondérée par le facteur `mu_k`.
3.  **Filtrage Récursif de Markov**: Résolution de l'équation de transition intégrant l'inertie:

$$P(S_t | O_t) \propto P(O_t | S_t) \sum_{S_{t-1}} P(S_t | S_{t-1}) P(S_{t-1} | O_{t-1})$$

Où la probabilité de transition $P(S_t = i | S_{t-1} = i)$ est sur-pondérée par le facteur `stick`.

---

## Tableau des Compromis: Inertie du Modèle

| Configuration de l'Inertie | Rapidité de Détection | Sensibilité aux Faux Signaux | Glissement d'Entrée (Slippage) |
| :--- | :--- | :--- | :--- |
| **Faible Inertie** (`stick < 0.7`) | ✅ Immédiate | ❌ Très élevée (bruit) | ✅ Nul (entrée directe au pivot) |
| **Forte Inertie** (`stick >= 0.9`) | ❌ Retardée | ✅ Très faible (lisse) | ❌ Moyen (décalage de quelques barres) |

---

## La Règle d'Or: Stabilisez l'État, Calibrez le Temps

> **Règle d'Or**: Sur-pondérez la persistance de l'état actuel pour filtrer le bruit, et n'autorisez le changement de régime qu'après une confirmation temporelle stricte.
