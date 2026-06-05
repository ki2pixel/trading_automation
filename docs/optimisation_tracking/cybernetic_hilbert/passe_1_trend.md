# Rapport : cybernetic_hilbert - Passe 1 (Trend Mode)

**Date d'analyse** : 05 Juin 2026
**Objectif de la Passe** : Optimisation de la période de lissage de Hilbert (`hilbert_smooth_period`) en mode tendance (`phase_mode_enabled = false`).
**Paramètres figés** : `phase_mode_enabled = false`.
**Métrique cible** : `return_vs_buy_hold_pct_points`.
**Itérations éligibles totales** : 0.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 1 n'a généré **aucune itération éligible (0)** sur l'ensemble des 10 actifs testés et sur l'ensemble des timeframes (1m à 240m).
Le but était de trouver un sweet spot pour `hilbert_smooth_period` offrant un avantage statistique clair avec un drawdown acceptable (-20% à -25%) et un profit factor >= 1.25 (selon les critères de la roadmap).
Cependant, aucune configuration n'a satisfait ces critères minimaux.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Edge Fort (Profit Factor >= 1.25, Itérations > 0)
*Aucun actif ne remplit ces critères.*

### 🟡 Neutres / Modérés (Edge léger)
*Aucun actif ne remplit ces critères.*

### 🔴 Rejetés (Absence d'edge / 0 Itération)
L'ensemble des actifs testés ont été rejetés car ils n'ont retourné aucune itération éligible avec un score fini ou des métriques satisfaisantes.

* **AMS.MC** : Rejeté sur tous les timeframes testés.
* **EVD.DE** : Rejeté sur tous les timeframes testés.
* **FPE.DE** : Rejeté sur tous les timeframes testés.
* **GMAB** : Rejeté sur tous les timeframes testés.
* **LOGI** : Rejeté sur tous les timeframes testés.
* **NVO** : Rejeté sur tous les timeframes testés.
* **NVS** : Rejeté sur tous les timeframes testés.
* **SAP** : Rejeté sur tous les timeframes testés.
* **SHL.DE** : Rejeté sur tous les timeframes testés.
* **ZEAL.CO** : Rejeté sur tous les timeframes testés.

---

## 3. Recommandations pour la Passe 2

Puisque la Passe 1 (Trend Mode) n'a révélé aucun edge exploitable sur les symboles testés, aucune configuration n'a été validée pour cette approche.
Conformément à la feuille de route, la **Passe 2** se concentrera sur l'exploration du **Phase Mode** (`phase_mode_enabled = true`). Il conviendra de vérifier si la composante cyclique de l'indicateur de Hilbert offre un meilleur avantage statistique que la détection de tendance pure sur ces mêmes actifs.
