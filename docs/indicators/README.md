# Indicateurs Techniques — Bibliothèque Numba/VectorBT

**TL;DR**: Bibliothèque d'indicateurs techniques compilés JIT via Numba ou vectorisés via VectorBT. Chaque indicateur est un module indépendant avec une fonction de calcul pure (sans état), utilisable en backtest comme en live.

---

## Indicateurs disponibles

| Indicateur | Fichier | LOC | Méthode | Stratégies associées |
|:---|:---|:---|:---|:---|
| **Hilbert Transform** | `hilbert_transform.py` | 302 | Numba JIT | `cybernetic_hilbert` |
| **Lorentzian Classification** | `lorentzian_classification.py` | 926 | Numba JIT | `lorentzian_classification` |
| **HMM Regime Filter** | `hmm_regime_filter.py` | 171 | Numpy | `hmm_regime_filter` |
| **Adaptive Trend Classification** | `adaptive_trend_classification.py` | 312 | VectorBT | `adaptive_trend_classification` |
| **MSL Trend** | `msl_trend.py` | 61 | VectorBT | `msl_trend` |
| **Trend Type** | `trend_type.py` | 90 | VectorBT | `trend_type` |
| **Pivot Retest** | `pivot_retest.py` | 184 | Numba JIT | `pivot_retest` |
| **Momentum-Based Zigzag** | `momentum_based_zigzag.py` | 328 | Numba JIT | `momentum_based_zigzag` |

---

## Architecture

Chaque module d'indicateur suit le pattern :

```python
# 1. Fonction de calcul pure (Numba JIT ou Numpy vectorisé)
@njit(cache=True)
def compute_indicator(close, high, low, ...):
    # Calcul sans état, entrée/sortie numpy
    return result

# 2. Wrapper VectorBT (optionnel, pour le pré-scan)
Indicator = vbt.IndicatorFactory(
    class_name="...",
    input_names=[...],
    output_names=[...]
).from_apply_func(compute_indicator, ...)
```

---

## Choix techniques

| Aspect | Numba JIT | VectorBT |
|:---|:---|:---|
| **Performance** | Native speed après warmup | Vectorisé, parallèle |
| **Compatibilité backtest** | Numpy arrays (POSIX SHM) | DataFrames multi-colonnes |
| **Utilisation** | Boucle principale backtest | Pré-scan, exploration |
| **Warmup** | ~2s première compilation | Instantané |

---

## Hilbert Transform (302 LOC)

Transformée de Hilbert de John Ehlers pour l'analyse cyclique. Calcule :
- **Sine Wave** : `sin(phase_instantanée)`
- **Lead Sine** : `sin(phase + π/4)` (avance de 45°)
- **Phase Mode** : `1` (cyclique) ou `0` (tendance)
- **Dominant Cycle** : période du cycle dominant détecté

Garantie de causalité : chaque barre `i` n'utilise que les barres `[max(0, i-6) … i]`.

---

## Lorentzian Classification (926 LOC)

Classification par plus proches voisins dans l'espace de Lorentz (distance non-euclidienne). Le plus gros indicateur du projet — 926 LOC, complexité élevée, Numba JIT obligatoire.

---

## HMM Regime Filter (171 LOC)

Modèle de Markov Caché pour la classification de régimes de marché. Utilise l'algorithme forward-backward pour estimer l'état latent (bull/bear/neutral) à partir des rendements.

---

## MSL Trend (61 LOC)

Market Structure Levels — ZLEMA + bande de volatilité ATR. Sortie binaire : `1.0` (bull), `-1.0` (bear), `0.0` (mixte). Le plus léger des indicateurs.

---

## Trend Type (90 LOC)

Classification de type de tendance par BobRivera990. Combine ATR (sideways détection) et ADX/DI (direction). Sortie : `2.0` (up), `-2.0` (down), `0.0` (sideways).

---

## Pivot Retest (184 LOC)

Calcul des niveaux de pivot (Pivot, R1, R2, S1, S2) et détection de retest. Implémenté en Numba JIT avec boucle colonne par colonne pour la performance.

---

**Règle d'or** : Un indicateur est une fonction pure. Pas d'état, pas d'I/O, pas de side effects. Entrée numpy → sortie numpy. Cette pureté garantit la portabilité entre backtest, pré-scan VectorBT et live trading.

*Guidé par documentation/SKILL.md — sections: TL;DR, Architecture, Trade-offs, Golden Rule.*
