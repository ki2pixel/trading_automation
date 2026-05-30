# Dépannage rapide (Troubleshooting)

**TL;DR** : "Port déjà utilisé", "Module introuvable" ou problème de permission ? Pas de panique. Voici comment débloquer ton terminal et vérifier que tout fonctionne en quelques secondes.

Tu lances ton serveur de backtest, tu ouvres ton terminal et là... c'est le drame. Une ligne d'erreur incompréhensible s'affiche et le script s'arrête net. 

Ces frictions techniques font partie du quotidien du développement. Souvent, la solution est extrêmement simple mais difficile à deviner seul. 

Voici un guide direct pour résoudre les 4 problèmes les plus courants en 2 minutes chrono.

---

## 1. L'erreur "Port déjà utilisé" (Port 8765 occupied)
Le serveur web FastAPI utilise par défaut le port `8765`. Si tu as déjà lancé le serveur dans un autre terminal (ou si un ancien processus a planté sans libérer le port), tu obtiendras une erreur de démarrage.

### La solution
Le plus simple est d'utiliser notre script de démarrage `start_backtest_engine.sh` car il s'occupe de chercher et de tuer proprement toute instance fantôme. 

Si tu préfères faire le nettoyage à la main, exécute cette commande pour forcer l'arrêt du processus qui bloque :

```bash
pkill -f "python3 -m backtest_engine serve --host 127.0.0.1 --port 8765"
```

---

## 2. L'erreur "ModuleNotFoundError" (Module non trouvé)
Tu tentes de lancer un backtest et Python te répond sèchement qu'il ne connaît pas le module `backtest_engine`.

### La solution
Cette erreur se produit généralement quand tu lances ta commande depuis le mauvais dossier. 
1. Assure-toi d'être positionné à la racine exacte de ton répertoire de projet.
2. Utilise toujours la syntaxe avec l'option `-m` (module) pour que Python résolve les chemins internes correctement : `python3 -m backtest_engine <commande>`.

---

## 3. L'erreur "Permission Denied" (Permission refusée)
Tu essaies d'exécuter le script shell de démarrage et ton système Linux te bloque en disant que tu n'as pas le droit de le faire.

### La solution
Par défaut, les nouveaux fichiers téléchargés ou copiés sous Linux n'ont pas le droit d'exécution activé par sécurité. Tu dois l'autoriser manuellement une première fois :

```bash
chmod +x start_backtest_engine.sh
```

---

## 4. Comment vérifier que tout fonctionne ? (Tests unitaires)
Si tu as modifié du code ou si tu veux t'assurer que ton environnement Python est parfaitement configuré pour le backtester, lance notre suite de tests automatisés.

### La méthode recommandée (Pytest)
Pytest va exécuter les 202 tests unitaires de non-régression et te donner un diagnostic complet de l'état du système :

```bash
python3 -m pytest tests/
```

### La méthode de secours (sans installation supplémentaire)
Si tu n'as pas encore installé Pytest, tu peux utiliser le moteur de test natif de Python :

```bash
python3 -m unittest discover -s tests
```
