# Lancer et automatiser la collecte

**TL;DR** : Active le "Mode automatique" depuis ton menu Google Sheets. Le script Apps Script enchaînera alors les cycles de téléchargement en tâche de fond et s'arrêtera de lui-même dès que toutes les données historiques jusqu'à `END_DATE` seront stockées sur ton Drive.

Tu as configuré ta liste d'actions et tes dates dans la feuille `CONFIG`. Maintenant, tu veux lancer la machine. Mais télécharger un historique intraday de plusieurs mois ou années sur une dizaine d'actions représente des milliers de lignes de données. 

Faire cela manuellement, fenêtre de 7 jours après fenêtre de 7 jours, serait un travail titanesque. De plus, les micro-coupures de connexion ou les limitations de temps de calcul de Google risquent de couper ton travail au milieu.

Le collecteur intègre un **superviseur automatique** qui s'occupe de tout gérer en tâche de fond sans aucune intervention de ta part.

---

## Le superviseur automatique : Lance et oublie

Pour lancer la collecte en mode 100% automatique, va dans ton Google Sheet et clique sur :
`SF Collector -> Start auto collector`

### Que se passe-t-il sous le capot ?
1. **Planification du premier cycle** : Le script programme un déclencheur temporisé dans ton compte Google Apps Script (environ 10 secondes après ton clic).
2. **Collecte des cours (`runBarsBatch`)** : Le script commence par télécharger les barres de 5 minutes pour chaque action de ta watchlist, fenêtre par fenêtre.
3. **Collecte des splits (`runSplitsBatch`)** : Une fois que toutes les barres de cours sont récupérées et sauvegardées, le superviseur passe à la récupération des événements de division d'actions (splits).
4. **Collecte des devises (`runFxBatch`)** : Enfin, il extrait la devise de chaque action et télécharge les taux de change historiques nécessaires (ex: `USDEUR`) vers ton dossier Google Drive.
5. **Boucle de sécurité** : Si le script arrive proche de la limite de temps maximale autorisée par Google (6 minutes), il s'arrête proprement de lui-même, programme un nouveau cycle automatique 30 secondes plus tard, et reprend exactement là où il s'était arrêté.
6. **Arrêt automatique** : Dès que l'historique complet jusqu'à ta date de fin (`END_DATE`) est intégralement enregistré, le superviseur désactive le mode automatique et supprime tous ses déclencheurs pour libérer ton compte Google.

---

## Comment le système assure sa survie (Checkpoints et Staging)

### Le journal de bord : La feuille `CHECKPOINTS`
Si ton navigateur web se ferme, si ta connexion coupe ou si le serveur de Google subit un micro-redémarrage, le collecteur ne perd jamais le fil. 

Il écrit chaque étape réussie dans la feuille `CHECKPOINTS` de ton classeur. Lors du cycle suivant, le superviseur consulte cette liste pour sauter les périodes déjà enregistrées et se concentrer uniquement sur les données manquantes.

### La zone de transit : La feuille `STAGING`
Pendant la collecte, tu verras peut-être des données s'afficher et s'effacer rapidement dans la feuille `STAGING`. C'est normal. 

Cette feuille sert de zone tampon temporaire : le script y injecte les formules d'API SheetsFinance, attend que les serveurs calculent les cours, extrait les lignes de données en mémoire pour les envoyer vers ton Google Drive, puis nettoie la feuille pour le lot suivant.

---

## Où trouver tes fichiers de données ?

Une fois collectés, tes fichiers sont structurés proprement dans ton espace de stockage Google Drive, sous le dossier racine `SheetsFinance_Export/` :

```text
SheetsFinance_Export/
  market_data/
    raw_5m/
      AAPL/
        2024/
          AAPL_5m_2024-01.csv
  fx_data/
    raw_5m/
      USDEUR/
        2024/
          USDEUR_5m_2024-01.csv
    symbol_currency_map.csv
  splits/
    AAPL_splits.csv
```

Ces dossiers mensuels ordonnés et ces fichiers CSV sont prêts à être synchronisés sur ta machine locale pour alimenter ton moteur de backtest.
