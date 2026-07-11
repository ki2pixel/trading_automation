[MEMORY BANK: ACTIVE (MCP-PULL)]

**Statut : REJET**

- **Note de goût : 3/10**
- **Diagnostic de structure de données :** les données API sont mêlées à des fragments HTML, ce qui casse l’intégrité financière et ouvre une surface d’injection.
- **Compatibilité :** aucune rupture d’API constatée ; l’interface actuelle affiche toutefois des valeurs incorrectes ou périmées.

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité |
| :-- | :-- | :-- | :-- |
| FT-01 | Intégrité financière | Les transactions et configurations Bybit sont formatées en EUR au lieu d’USDT. | Haute |
| FT-02 | Intégrité des données | La table de configurations a 9 en-têtes pour 11 cellules : les colonnes sont décalées. | Haute |
| FT-03 | État temps réel | Les marqueurs de trades restent périmés malgré le heartbeat ; le cache n’est pas invalidé. | Haute |
| FT-04 | Observabilité | Les statuts de stratégies sont mis en cache indéfiniment et peuvent masquer une erreur moteur. | Haute |
| FT-05 | Sécurité XSS/HTML injection | Des champs API sont interpolés via `innerHTML`, y compris un JSON injecté dans un attribut HTML. | Haute |
| FT-06 | Performance/race | Un polling asynchrone toutes les 10 s peut se chevaucher et recharger jusqu’à 5 000 transactions. | Haute |
| FT-07 | Responsive | L’interface desktop est tronquée sur mobile : sidebar fixe, absence de breakpoint global et overflow caché. | Haute |
| FT-08 | Faux statut opérationnel | « Engine Online » reste vert même si le heartbeat/API est indisponible. | Haute |
| FT-09 | Accessibilité | Modales non accessibles au clavier, focus non géré, interrupteurs de stratégie sans libellé lisible. | Moyenne |
| FT-10 | Fonctionnalité | Le bouton « Clear » des logs n’a aucun gestionnaire ; le JS de login est protégé par l’authentification. | Moyenne |

Constats principaux :

- [app.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:186) affiche toutes les valeurs de configuration en EUR ; [transactions](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:258) fait de même pour Bybit.
- Les en-têtes de [index.html](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/index.html:242) ne correspondent pas aux 11 colonnes créées dans [app.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:185).
- Le cache dans [chart.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/js/chart.js:135) contredit le rafraîchissement déclenché dans [app.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:703) : les nouveaux ordres n’apparaissent pas sur le graphique.
- Les interpolations HTML de [app.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:119) à [app.js](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js:196) doivent être remplacées par des nœuds DOM avec `textContent`. La CSP limite l’exploitation, mais ne justifie pas cette injection.
- [style.css](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/style.css:52) verrouille le conteneur, tandis que la sidebar conserve 260 px ; aucun breakpoint ne réorganise l’application.
- Le statut global est codé en dur dans [index.html](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/index.html:70) et n’est jamais synchronisé avec le heartbeat.

Correctif minimal pour la devise :

```js
const formatAmountForAsset = (asset, value) =>
    asset?.toLowerCase().endsWith('usdt')
        ? formatUSDT(value)
        : formatCurrency(value);
```

Priorité de correction : 1) exactitude devises/en-têtes/états temps réel, 2) suppression complète de `innerHTML` pour les données API, 3) sérialisation du polling et rafraîchissement explicite des caches, 4) breakpoint mobile et modales accessibles.

Validation : le dépôt est propre. Aucun serveur local n’était actif ; l’audit dynamique Playwright n’a donc pas été exécuté.