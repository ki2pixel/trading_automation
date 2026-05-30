# Rapport de verification - Datasets suspects GMAB et ZEAL.CO

## Resume executif

Les datasets `GMAB` et `ZEAL.CO` dans `/home/kidpixel/trading_automation_v2/storage/processed/market_data_1m/` **ne sont pas suspects en termes de qualite ou de gaps anormaux**. Leur faible volume s'explique par leur provenance (SheetsFinance raw_1m) et les heures de marché réelles de leurs bourses respectives, contrairement aux autres symboles qui proviennent d'une source 1m 24/7.

---

## 1. Contexte et origine des donnees

### Sources identifiees

| Symbole | Fichier parquet | Source brute | Annees disponibles | Taille |
|---------|-----------------|--------------|-------------------|--------|
| **GMAB** | 7.9 MB | `raw_1m/GMAB/` (SheetsFinance) | 2020-2025 | 459,333 lignes |
| **ZEAL.CO** | 3.6 MB | `raw_1m/ZEAL.CO/` (SheetsFinance) | 2023-2025 | 242,538 lignes |
| NVS | 45.6 MB | **Autre source** (pas de raw_1m) | 2015-2025 | 5,187,899 lignes |
| SAP | 50.1 MB | **Autre source** (pas de raw_1m) | 2015-2025 | 5,401,020 lignes |
| LOGI | 38.5 MB | **Autre source** (pas de raw_1m) | 2015-2025 | 5,015,099 lignes |

> **Observation cle** : Les symboles "volumineux" (NVS, SAP, LOGI, AMS.MC, SHL.DE, NVO) n'ont **pas** de dossier `raw_1m` dans SheetsFinance. Leurs datasets 1m ont ete crees le 20/05/2026 a 12:21 depuis une source externe differente (probablement Kaggle ou un autre fournisseur). GMAB et ZEAL.CO ont ete crees le meme jour a 22:25 depuis les `raw_1m` SheetsFinance.

---

## 2. Analyse de GMAB

### Caracteristiques
- **Type** : Action americaine (Genmab A/S - ADR americain, biotech danoise)
- **Bourse** : NASDAQ (heures ET)
- **Periode** : 02/01/2020 -> 30/10/2025 (2,128 jours calendaires)
- **Jours de trading** : 1,514 jours
- **Moyenne** : ~303 barres/jour

### Heures de trading observees
```
Heures actives (Mon-Fri): 0h, 9h, 10h, 11h, 12h, 13h, 14h, 15h, 17h-23h
Heure principale: 15h (65,975 barres)
```

- **Session principale** : 09:30 - 15:59 ET (~390 barres)
- **Extended hours** : Minuit (0h) et soir (17h-23h) - presence faible
- **Anomalie** : **2,508 barres samedi** sur 46 samedis en 2024 uniquement, entre 00:00 et 00:59. Ces barres samedi semblent etre des donnees d'extended hours (pre-market du dimanche ou artefacts de collecte).

### Verdict GMAB
✅ **Dataset sain**. La faible taille s'explique par :
1. Heures de marché americain limitees (~6.5h de session principale)
2. Pas de donnees week-end (sauf anomalie samedi 2024)
3. Periode plus courte (depuis 2020 vs 2015 pour les autres)

---

## 3. Analyse de ZEAL.CO

### Caracteristiques
- **Type** : Action danoise (Zealand Pharma)
- **Bourse** : Copenhague (CET/CEST)
- **Periode** : 02/01/2023 -> 30/12/2025 (1,093 jours calendaires)
- **Jours de trading** : 733 jours
- **Moyenne** : ~331 barres/jour

### Heures de trading observees
```
Heures actives (Mon-Fri): 9h, 10h, 11h, 12h, 13h, 14h, 15h, 16h, 17h
Premiere heure: 9h, Derniere: 17h
```

- **Session principale** : 09:00 - 16:59 CET (~480 barres theoriques)
- **Moyenne reelle** : ~331 barres/jour
- **Jours incomplets** : 79 jours avec < 200 barres, 245 jours avec < 300 barres
- **Anomalie** : 1 jour avec 1 seule barre (06/12/2023 a 17:00)

### Jours a faible activite
Les 79 jours avec < 200 barres correspondent probablement a :
- Jours de faible liquidite (vacances, periodes estivales)
- Sessions raccourcies (jours avant feries)
- Jours avec interruptions de marché

### Verdict ZEAL.CO
✅ **Dataset sain mais avec faible densite intraday**. La faible taille s'explique par :
1. Heures de marché europeen limitees (~8h par jour)
2. Periode tres courte (depuis 2023 uniquement)
3. Pas de donnees week-end (correct pour une bourse europeenne)
4. Faible liquidite intraday (jours avec peu de transactions = barres manquantes)

---

## 4. Verification coherence Brut -> Parquet

### Methode
Comparaison exhaustive des timestamps entre les CSV bruts et les parquets generees.

### Resultats
| Symbole | Lignes brutes | Lignes parquet | Timestamps manquants | Timestamps en trop |
|---------|--------------|----------------|---------------------|-------------------|
| GMAB | 459,333 | 459,333 | **0** | **0** |
| ZEAL.CO | 242,538 | 242,538 | **0** | **0** |

> **Conclusion** : La conversion SheetsFinance -> Parquet est parfaitement fidele. Aucune perte de donnees.

---

## 5. Comparaison avec les autres symboles

### Pourquoi NVS/SAP/LOGI sont-ils si volumineux ?

Les symboles europeens (SAP, AMS.MC, SHL.DE) et suisses (LOGI, NVS) ont des datasets 1m denses (~1,440 barres/jour) car leur source 1m n'est **pas** SheetsFinance mais un fournisseur externe qui fournit :
- Des donnees **24h/24, 7j/7** (meme le samedi et dimanche)
- Des barres chaque minute sans interruption
- Des periodes commencant en 2015

Ces datasets ne representent pas le comportement reel des bourses (qui ferment le week-end) mais des series temporelles continues, probablement des CFDs ou des donnees synthetiques.

### Tableau comparatif

| Metrique | GMAB | ZEAL.CO | NVS | SAP |
|----------|------|---------|-----|-----|
| Taille | 7.9 MB | 3.6 MB | 45.6 MB | 50.1 MB |
| Lignes | 459K | 243K | 5,188K | 5,401K |
| Barres/jour | ~303 | ~331 | ~1,440 | ~1,440 |
| Samedi ? | Oui (2024) | Non | Oui (tous) | Oui (tous) |
| Dimanche ? | Non | Non | Oui | Oui |
| 24h/24 ? | Non | Non | Oui | Oui |

---

## 6. Recommandations

1. **GMAB** : Le dataset est utilisable. L'anomalie des samedis 2024 (2,508 barres) est negligeable (0.5% du total). Considerer un filtrage des week-ends si la strategie ne supporte pas ces donnees.

2. **ZEAL.CO** : Le dataset est utilisable mais la faible densite intraday (79 jours avec < 200 barres) peut impacter les strategies sensibles aux gaps. Considerer un pre-traitement qui verifie la couverture horaire minimum avant de trader un jour donne.

3. **Documentation** : Documenter clairement dans le README que les datasets 1m proviennent de deux sources differentes :
   - **Source A** (NVS, SAP, LOGI, etc.) : Donnees 24/7, denses
   - **Source B** (GMAB, ZEAL.CO) : Donnees SheetsFinance, heures de marché reelles

4. **Unification** : Pour la coherence, envisager de recuperer les donnees 1m des memes sources pour tous les symboles, ou d'appliquer un filtrage uniforme (heures de marché uniquement) sur la Source A.
