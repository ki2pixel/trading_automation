# MSL Trend — Market Structure Levels

**TL;DR**: Détecte les cassures de structure de marché (Market Structure Levels) — support/résistance formés par les pivots — pour identifier les retournements de tendance.

---

Les niveaux de support et résistance classiques (lignes horizontales manuelles) sont subjectifs et inconsistants. MSL Trend automatise la détection des structures de marché en identifiant les pivots successifs (HH/HL en hausse, LH/LL en baisse) et en générant des signaux sur cassure de ces niveaux.

## Mécanique
1. **Détection des pivots** : Higher Highs (HH), Higher Lows (HL), Lower Highs (LH), Lower Lows (LL)
2. **Validation de structure** : Confirmation qu'une série de pivots forme une tendance valide
3. **Signal sur cassure** : Le prix casse le dernier niveau de structure dans la direction opposée

### ❌ Lignes manuelles
```python
support = 145.00  # choisi visuellement, non reproductible
```

### ✅ MSL automatique
```python
msl_level = detect_msl(highs, lows, pivot_strength=3)
# Si close < dernier Higher Low → structure baissière confirmée → SELL
```

## Signaux
- **BUY** : Cassure haussière d'un niveau de résistance MSL
- **SELL** : Cassure baissière d'un niveau de support MSL

**Règle d'or** : Une structure de marché n'est valide qu'avec au moins 3 pivots confirmés. Un seul pivot ne fait pas une tendance.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Golden Rule.*
