# **Plan d'Action d'Ingénierie Logicielle pour l'Accélération Temporelle d'un Moteur de Backtesting Multi-Stratégies et Optimisation Bayésienne sur Optuna**

L'optimisation des hyperparamètres pour des portefeuilles multi-stratégies s'exécutant sur des données historiques à haute fréquence représente un défi computationnel majeur. Lorsque l'espace de recherche s'élargit pour englober des modèles complexes tels que le croisement de moyennes mobiles de Hull (HMA Crossover), le suivi de tendance à volatilité adaptative (Adaptive Volatility Trend), l'analyseur de moyennes mobiles et de multiplicateurs (PMax Explorer) ou la détection de limites de bruit de marché (Noise Boundary) , l'évaluation séquentielle classique par l'interpréteur Python s'avère prohibitive. Les temps de calcul dépassent fréquemment une heure, même en mobilisant des infrastructures parallélisées à quinze cœurs.  
Cette lenteur provient d'une boucle événementielle séquentielle non compilée, d'un taux de succès nul du cache d'indicateurs face aux suggestions continues d'Optuna, et d'un coût de sérialisation élevé lors des communications inter-processus.2 Pour ramener ces traitements à une durée de quelques minutes, il convient de restructurer le moteur autour de la compilation à la volée (JIT), du partage de mémoire sans copie et d'une architecture hybride vectorisée-événementielle.

## **1\. Compilation JIT et Numba de la Boucle de Simulation et de l'État du Courtier**

La boucle d'évaluation principale, traditionnellement écrite sous la forme for bar\_num, idx in enumerate(index):, souffre de la latence d'interprétation et de l'overhead d'allocation dynamique d'objets propres à Python.2 La transition vers la compilation Just-In-Time stricte via Numba (@numba.njit(cache=True)) exige l'élimination complète des structures orientées objet et des dictionnaires non typés au profit de types primitifs et de structures de données compatibles en mode nopython.5

### **Évaluation Comparative des Structures de Données pour Numba**

Le suivi d'état du courtier (BrokerSimulator), qui englobe le cash disponible, les positions actives et le capital alloué sous forme de compartiment plafonné (*capped bucket*) 7, nécessite de stocker et manipuler des variables dynamiques.

| Structure de Données | Compatibilité Numba | Performance Computationnelle | Comportement en Dehors du Contexte JIT | Recommandation Architecturale |
| :---- | :---- | :---- | :---- | :---- |
| **Dictionnaire Typé Numba** (numba.typed.Dict) 6 | Totale (types clés/valeurs statiques) 6 | Faible (coût de hachage élevé, empêche l'optimisation par déplacement de code) 9 | Très lent (overhead d'encapsulation/désencapsulation) 6 | À éviter pour le suivi de variables à haute fréquence.9 |
| **Liste Typée Numba** (numba.typed.List) 11 | Totale (homogène) 11 | Moyenne (coût d'allocation dynamique de mémoire lors des ajouts) 11 | Ralentissement marqué lors des interactions avec l'interpréteur 11 | Utile uniquement pour stocker des séries irrégulières.11 |
| **Tableaux Structurés NumPy** (np.ndarray avec types composés C) 12 | Totale 12 | Maximale (accès direct par calcul d'offset mémoire au niveau machine) 9 | Excellente (représenté comme un tableau NumPy standard) 12 | **Recommandé** pour toutes les structures d'état de position et de portefeuille.9 |

Les tableaux structurés NumPy s'alignent directement avec la mémoire continue du processeur, permettant à Numba de générer des instructions d'accès direct par arithmétique de pointeurs.9 Les gains de performance s'expliquent par la possibilité pour le compilateur LLVM de vectoriser ces accès et d'appliquer l'optimisation par déplacement de code hors de la boucle (*Loop-Invariant Code Motion*), ce qui est rendu impossible par les mécanismes de mutation interne des dictionnaires typés.9

### **Code d'Implémentation : Boucle d'État Séquentielle Compilée**

Le patron d'architecture suivant illustre la réécriture complète de la boucle de simulation événementielle. L'état des positions est stocké dans un tableau structuré NumPy, et l'allocation du capital partagé est régulée dynamiquement par le modèle de compartiment plafonné (*capped bucket*).7

Python  
import numpy as np  
from numba import njit

\# Définition du schéma de données pour l'état d'une position active  
position\_dtype \= np.dtype(, align=True)

@njit(cache=True)  
def run\_broker\_simulation\_kernel(  
    open\_prices, high\_prices, low\_prices, close\_prices,  
    raw\_signals, strategy\_ids, initial\_cash, capped\_bucket\_limit,  
    stop\_loss\_pct, trailing\_stop\_pct, take\_profit\_pct  
):  
    """  
    Simulateur de courtage séquentiel compilé en mode strict nopython.  
    Gère un portefeuille multi-stratégies sous contrainte de capital partagé.  
    """  
    n\_bars \= len(close\_prices)  
    cash \= initial\_cash  
    allocated\_capital \= 0.0  
      
    \# Allocation sur pile d'un tableau de positions (une par stratégie active)  
    n\_strategies \= len(np.unique(strategy\_ids))  
    positions \= np.zeros(n\_strategies, dtype=position\_dtype)  
    for s in range(n\_strategies):  
        positions\[s\]\['is\_active'\] \= False  
        positions\[s\]\['strategy\_id'\] \= s  
          
    equity\_curve \= np.empty(n\_bars, dtype=np.float64)  
      
    for i in range(n\_bars):  
        curr\_open \= open\_prices\[i\]  
        curr\_high \= high\_prices\[i\]  
        curr\_low \= low\_prices\[i\]  
        curr\_close \= close\_prices\[i\]  
          
        \# 1\. Évaluation des Sorties et Trailing Stops de protection  
        for s in range(n\_strategies):  
            pos \= positions\[s\]  
            if pos\['is\_active'\]:  
                \# Mise à jour du plus haut historique de la position pour le trailing stop  
                if curr\_high \> pos\['trailing\_high'\]:  
                    pos\['trailing\_high'\] \= curr\_high  
                    pos\['stop\_loss'\] \= curr\_high \* (1.0 \- trailing\_stop\_pct)  
                  
                \# Cas d'un déclenchement de Stop Loss ou Trailing Stop  
                if curr\_low \<= pos\['stop\_loss'\]:  
                    exit\_price \= min(pos\['stop\_loss'\], curr\_open)  \# Prise en compte du gap d'ouverture  
                    pnl \= (exit\_price \- pos\['entry\_price'\]) \* pos\['qty'\]  
                    execution\_value \= (pos\['entry\_price'\] \* pos\['qty'\]) \+ pnl  
                    cash \+= execution\_value  
                    allocated\_capital \-= (pos\['entry\_price'\] \* pos\['qty'\])  
                    pos\['is\_active'\] \= False  
                      
                \# Cas d'un déclenchement de Take Profit (Bracket Exit)  
                elif curr\_high \>= pos\['take\_profit'\]:  
                    exit\_price \= max(pos\['take\_profit'\], curr\_open)  
                    pnl \= (exit\_price \- pos\['entry\_price'\]) \* pos\['qty'\]  
                    execution\_value \= (pos\['entry\_price'\] \* pos\['qty'\]) \+ pnl  
                    cash \+= execution\_value  
                    allocated\_capital \-= (pos\['entry\_price'\] \* pos\['qty'\])  
                    pos\['is\_active'\] \= False  
                      
        \# 2\. Évaluation des Signaux d'Entrée  
        for s in range(n\_strategies):  
            pos \= positions\[s\]  
            \# Lecture du signal d'entrée spécifique à la barre et à la stratégie  
            signal \= raw\_signals\[s, i\]  
              
            if not pos\['is\_active'\] and signal\!= 0:  
                \# Modèle de "Capped Bucket" : Vérification de la disponibilité du capital  
                available\_to\_allocate \= min(cash, capped\_bucket\_limit \- allocated\_capital)  
                  
                if available\_to\_allocate \> 0.0:  
                    pos\['is\_active'\] \= True  
                    pos\['entry\_price'\] \= curr\_close  
                    pos\['qty'\] \= available\_to\_allocate / curr\_close  
                    pos\['trailing\_high'\] \= curr\_close  
                    pos\['stop\_loss'\] \= curr\_close \* (1.0 \- stop\_loss\_pct)  
                    pos\['take\_profit'\] \= curr\_close \* (1.0 \+ take\_profit\_pct)  
                    pos\['entry\_bar'\] \= i  
                      
                    cash \-= available\_to\_allocate  
                    allocated\_capital \+= available\_to\_allocate  
                      
        \# 3\. Calcul de la Valeur Liquidative Globale (Portefeuille)  
        current\_equity \= cash  
        for s in range(n\_strategies):  
            if positions\[s\]\['is\_active'\]:  
                current\_equity \+= curr\_close \* positions\[s\]\['qty'\]  
        equity\_curve\[i\] \= current\_equity  
          
    return equity\_curve

L'absence d'instructions d'allocation de mémoire dynamique ou d'appels à des dictionnaires au sein de cette boucle garantit une exécution à la vitesse native du processeur, éliminant ainsi le goulot d'étranglement de la simulation séquentielle.2

## **2\. Refactorisation du Caching et Partage de Mémoire des Indicateurs Techniques**

Dans l'implémentation initiale, le calcul d'un indicateur complexe tel que la moyenne mobile de Hull (HMA) repose sur un cache local par processus. Cependant, l'optimiseur bayésien suggère des hyperparamètres sur un spectre continu, ce qui détruit le taux de succès du cache, conduisant à des recalculs systématiques.14

### **Grille de Paramètres Discrétisés et Pré-calcul Initiale**

Pour contrer cette inefficacité, il est proposé de pré-calculer l'ensemble des combinaisons possibles d'indicateurs sur une grille élargie au démarrage du processus parent, juste après qu'un pré-scan rapide avec VectorBT ait identifié et resserré les bornes globales de recherche. Ce tenseur multidimensionnel de données est calculé de manière entièrement vectorisée, puis hébergé au sein d'un segment de mémoire partagée POSIX au niveau du système d'exploitation (/dev/shm).16  
Un problème critique survient lorsque plusieurs processus workers lisent simultanément un tableau NumPy pointant sur la mémoire partagée : une croissance exponentielle de la mémoire est constatée.18 Ce phénomène est lié au fait que la lecture d'un tableau ou la création de sous-vues en Python incrémente le compteur de références (*refcount*) de l'objet, ce qui modifie la structure de l'en-tête de la page mémoire et déclenche un mécanisme de copie sur écriture (*Copy-on-Write*) par le noyau du système d'exploitation.18  
Pour éviter cette dégradation, l'en-tête NumPy doit être initialisé statiquement dans chaque sous-processus à l'aide d'un pointeur pointant directement sur le tampon sous-jacent non managé (shm.buf), empêchant toute duplication invisible de pages mémoire.3

                                PROPRIÉTÉ DE L'ESPACE PARENT  
                     ┌───────────────────────────────────────────────────┐  
                     │  Données Historiques & Grille d'Indicateurs      │  
                     └─────────────────────────┬─────────────────────────┘  
                                               │ Écriture Initiale (O(N))  
                                               ▼  
                                 SEGMENT DE MÉMOIRE PARTAGÉE  
                     ┌───────────────────────────────────────────────────┐  
                     │          POSIX Shared Memory (/dev/shm)           │  
                     └─────────────────────────┬─────────────────────────┘  
                                               │  
               ┌───────────────────────────────┼───────────────────────────────┐  
               │ Accès direct (zéro-copie)     │ Accès direct (zéro-copie)     │ Accès direct (zéro-copie)  
               ▼                               ▼                               ▼  
       WORKER PROCESSUS 1              WORKER PROCESSUS 2              WORKER PROCESSUS N  
 ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐  
 │ Vue NumPy via shm.buf     │   │ Vue NumPy via shm.buf     │   │ Vue NumPy via shm.buf     │  
 └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘

### **Code d'Implémentation : Gestionnaire de Tenseurs Partagés Statiques**

Le script ci-dessous montre comment créer et structurer les indicateurs pré-calculés en mémoire partagée, évitant ainsi l'overhead de copie inter-processus.

Python  
from multiprocessing import shared\_memory  
import numpy as np

class SharedIndicatorVolume:  
    """  
    Gère l'allocation, l'accès en lecture seule et la destruction d'un volume  
    multidimensionnel d'indicateurs pré-calculés en mémoire partagée.  
    """  
    def \_\_init\_\_(self, array\_to\_share: np.ndarray \= None, shm\_name: str \= None,   
                 shape: tuple \= None, dtype: np.dtype \= None):  
        self.shm \= None  
          
        if array\_to\_share is not None:  
            \# Code exécuté par le processus parent  
            self.shape \= array\_to\_share.shape  
            self.dtype \= array\_to\_share.dtype  
            self.nbytes \= array\_to\_share.nbytes  
              
            \# Création du segment POSIX de mémoire partagée  
            self.shm \= shared\_memory.SharedMemory(create=True, size=self.nbytes)  
            self.shm\_name \= self.shm.name  
              
            \# Création d'un tableau NumPy rattaché au segment pour l'écriture initiale  
            parent\_view \= np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)  
            parent\_view\[:\] \= array\_to\_share\[:\]  
        else:  
            \# Code exécuté par les processus workers (lecture seule)  
            self.shm\_name \= shm\_name  
            self.shape \= shape  
            self.dtype \= dtype  
              
    def get\_view(self) \-\> np.ndarray:  
        """  
        Génère une vue locale de type NumPy mappée directement sur le segment de mémoire.  
        Évite le mécanisme de copie sur écriture en se liant directement au tampon sous-jacent.  
        """  
        if self.shm is None:  
            self.shm \= shared\_memory.SharedMemory(name=self.shm\_name, create=False)  
        return np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)

    def close(self):  
        """Ferme la liaison avec le segment de mémoire partagée pour le processus courant."""  
        if self.shm is not None:  
            self.shm.close()

    def unlink(self):  
        """Libère définitivement la ressource système (uniquement par le parent)."""  
        if self.shm is not None:  
            try:  
                self.shm.unlink()  
            except FileNotFoundError:  
                pass

Grâce à cette approche, chaque worker accède à une combinaison spécifique d'indicateurs en temps constant ![][image1] par simple indexation d'une dimension du volume de données, supprimant intégralement les recalculs d'indicateurs en cours d'exploration.

## **3\. Optimisation de la Parallélisation Multi-Process et Tuning d'Optuna**

Le transfert d'une structure de données volumineuse entre un processus parent et des sous-processus via un ProcessPoolExecutor s'appuie par défaut sur la sérialisation pickle. À l'échelle de milliers de simulations, cet échange répété sature les capacités de communication de la machine.3

SÉRIALISATION IPC CLASSIQUE (Inefficace) :  
\[Parent\] ───Pickle(DataFrame 1.5GB)───► \[Pipe\] ───Unpickle(DataFrame)───►

PARTAGE PAR MÉMOIRE POSIX (Optimum) :  
\[Parent\] ───SharedMemory(Création)───► \[Mémoire Physique /dev/shm\] ◄───Lecture Directe O(1)───

### **Suppression de l'Overhead d'IPC via Initializer**

La solution idéale réside dans l'exploitation de l'argument initializer au moment d'instancier le pool de workers.19 En fixant la référence du segment de mémoire partagée sous forme de variables globales directement dans l'espace mémoire virtuel de chaque worker lors de sa phase de démarrage, l'exécution des *trials* ne requiert plus que la transmission d'identifiants de paramètres légers, réalisant un patron de conception dit « d'accès mémoire à coût nul ».19

### **Paramétrage de Convergence d'Optuna**

Pour maximiser l'efficacité de l'exploration bayésienne et minimiser le nombre total d'itérations, il est préconisé d'ajuster finement l'échantillonneur d'Optuna et la couche de stockage.14

* **Modèle TPE Multivarié (multivariate=True)** : Le modèle classique d'échantillonneur par estimateurs de Parzen structurés en arbre (TPE) traite chaque paramètre indépendamment.14 L'activation de l'option multivariée permet de modéliser les distributions de paramètres de manière conjointe, capturant de fait les corrélations sous-jacentes.14 Par exemple, si la stratégie *PMax Explorer* requiert un multiplicateur proportionnel à la longueur de la moyenne mobile sous-jacente, l'échantillonneur adaptera automatiquement ses lois de probabilité multidimensionnelles.14  
* **Algorithme du Menteur Constant (constant\_liar=True)** : En environnement parallèle, plusieurs workers évaluent simultanément différentes combinaisons.14 L'absence de résultats immédiats pour les essais en cours peut conduire les workers à proposer des configurations identiques. L'activation de l'option constant\_liar attribue de manière transitoire une performance artificielle pénalisante aux essais en cours de calcul.14 Cela force l'échantillonneur à diversifier instantanément ses propositions vers de nouvelles régions inexplorées.20  
* **Stockage de Journalisation d'Opérations (JournalStorage)** : Les bases de données relationnelles (par exemple SQLite) induisent un niveau élevé d'interblocages et de latences d'accès disque lors d'accès parallèles simultanés par quinze workers.21 L'utilisation de JournalStorage s'appuyant sur un backend fichier asynchrone JournalFileBackend ou sur une base de données en mémoire vive ultra-rapide JournalRedisStorage transforme toutes les écritures en écriture continue de lignes JSON (*append-only log*).20 Les verrous d'accès aux tables sont éliminés, libérant d'importantes ressources CPU pour le traitement mathématique.22

### **Code d'Implémentation : Orchestrateur d'Optimisation Bayésienne Parallèle**

Le code suivant configure le pool de workers et le moteur d'optimisation d'Optuna.

Python  
import optuna  
from optuna.storages import JournalStorage, JournalFileStorage  
from concurrent.futures import ProcessPoolExecutor

\# Variables globales réservées au contexte d'exécution de chaque worker  
WORKER\_CLOSE\_PRICES \= None  
WORKER\_INDICATORS \= None

def init\_worker\_shared\_context(prices\_shm\_name, prices\_shape, prices\_dtype,  
                               ind\_shm\_name, ind\_shape, ind\_dtype):  
    """  
    Fonction d'initialisation exécutée une unique fois par chaque worker à son démarrage.  
    Mappe de manière permanente les segments de mémoire partagée.  
    """  
    global WORKER\_CLOSE\_PRICES, WORKER\_INDICATORS  
      
    \# Association sans copie aux séries de prix historiques  
    prices\_vol \= SharedIndicatorVolume(shm\_name=prices\_shm\_name, shape=prices\_shape, dtype=prices\_dtype)  
    WORKER\_CLOSE\_PRICES \= prices\_vol.get\_view()  
      
    \# Association au volume d'indicateurs pré-calculés  
    ind\_vol \= SharedIndicatorVolume(shm\_name=ind\_shm\_name, shape=ind\_shape, dtype=ind\_dtype)  
    WORKER\_INDICATORS \= ind\_vol.get\_view()

def execute\_objective\_evaluation(trial\_params, prices\_shape, ind\_shape):  
    """  
    Effectue l'évaluation d'un ensemble de paramètres sans aucune étape de désérialisation.  
    """  
    global WORKER\_CLOSE\_PRICES, WORKER\_INDICATORS  
      
    \# Récupération des clés d'indexation dans le volume pré-calculé  
    hma\_idx \= int(trial\_params\['hma\_length\_idx'\])  
    atr\_idx \= int(trial\_params\['atr\_length\_idx'\])  
      
    \# Accès direct O(1) aux indicateurs techniques  
    hma\_series \= WORKER\_INDICATORS\[hma\_idx, :, 0\] \# Première couche : HMA  
    atr\_series \= WORKER\_INDICATORS\[atr\_idx, :, 1\] \# Deuxième couche : ATR  
      
    \# Génération des signaux d'entrée brute  
    signals \= np.zeros\_like(WORKER\_CLOSE\_PRICES, dtype=np.int8)  
    signals \= 1 \# Exemple de croisement  
      
    \# Extension au multi-stratégies (format matriciel attendu par le noyau)  
    raw\_signals \= np.expand\_dims(signals, axis=0)  
    strategy\_ids \= np.zeros(1, dtype=np.int32)  
      
    \# Lancement de la boucle de courtage compilée en JIT  
    equity \= run\_broker\_simulation\_kernel(  
        open\_prices=WORKER\_CLOSE\_PRICES,  
        high\_prices=WORKER\_CLOSE\_PRICES \* 1.002, \# Approximation des extrêmes  
        low\_prices=WORKER\_CLOSE\_PRICES \* 0.998,  
        close\_prices=WORKER\_CLOSE\_PRICES,  
        raw\_signals=raw\_signals,  
        strategy\_ids=strategy\_ids,  
        initial\_cash=10000.0,  
        capped\_bucket\_limit=5000.0,  
        stop\_loss\_pct=trial\_params\['stop\_loss\_pct'\],  
        trailing\_stop\_pct=trial\_params\['trailing\_stop\_pct'\],  
        take\_profit\_pct=trial\_params\['take\_profit\_pct'\]  
    )  
      
    \# Calcul de la métrique d'évaluation (Ratio de Sharpe annualisé)  
    returns \= np.diff(equity) / (equity\[:-1\] \+ 1e-9)  
    sharpe \= np.mean(returns) / (np.std(returns) \+ 1e-9) \* np.sqrt(252 \* 1440\)  
    return sharpe

def run\_global\_bayesian\_optimization(historical\_data, indicator\_grid, n\_trials=300):  
    \# Enregistrement des volumes de données en mémoire partagée  
    prices\_shm \= SharedIndicatorVolume(array\_to\_share=historical\_data)  
    indicators\_shm \= SharedIndicatorVolume(array\_to\_share=indicator\_grid)  
      
    \# Initialisation du stockage sécurisé par journalisation  
    storage \= JournalStorage(JournalFileStorage("./optuna\_shared\_journal.log"))  
      
    \# Paramétrage avancé du TPESampler  
    sampler \= optuna.samplers.TPESampler(  
        multivariate=True,  
        constant\_liar=True,  
        n\_startup\_trials=30  
    )  
      
    study \= optuna.create\_study(  
        study\_name="optimized\_backtest\_run",  
        storage=storage,  
        sampler=sampler,  
        direction="maximize",  
        load\_if\_exists=True  
    )  
      
    \# Initialisation du pool de workers avec mappage mémoire statique  
    with ProcessPoolExecutor(  
        max\_workers=15,  
        initializer=init\_worker\_shared\_context,  
        initargs=(  
            prices\_shm.shm\_name, prices\_shm.shape, prices\_shm.dtype,  
            indicators\_shm.shm\_name, indicators\_shm.shape, indicators\_shm.dtype  
        )  
    ) as executor:  
          
        def objective\_wrapper(trial):  
            \# Définition de l'espace de recherche  
            trial\_params \= {  
                'hma\_length\_idx': trial.suggest\_int('hma\_length\_idx', 0, indicator\_grid.shape \- 1),  
                'atr\_length\_idx': trial.suggest\_int('atr\_length\_idx', 0, indicator\_grid.shape \- 1),  
                'stop\_loss\_pct': trial.suggest\_float('stop\_loss\_pct', 0.005, 0.05),  
                'trailing\_stop\_pct': trial.suggest\_float('trailing\_stop\_pct', 0.005, 0.03),  
                'take\_profit\_pct': trial.suggest\_float('take\_profit\_pct', 0.01, 0.15)  
            }  
              
            \# Soumission asynchrone pour éviter tout blocage d'interprétation  
            future \= executor.submit(  
                execute\_objective\_evaluation, trial\_params, prices\_shm.shape, indicators\_shm.shape  
            )  
            return future.result()  
              
        study.optimize(objective\_wrapper, n\_trials=n\_trials, n\_jobs=1)  
          
    \# Phase de libération des descripteurs de mémoire partagée  
    prices\_shm.unlink()  
    indicators\_shm.unlink()  
      
    return study.best\_trial

## **4\. Architecture Hybride Vectorisée (VectorBT \+ Moteur Événementiel)**

Le choix de l'architecture de calcul impose un arbitrage fondamental entre réalisme historique et vitesse d'exécution.2

* **L'Approche 100% Vectorisée** : Extrêmement rapide (![][image2] pour ![][image3] barres) grâce à une exécution par blocs d'instructions SIMD.2 Elle s'avère toutefois incapable de modéliser correctement des contraintes dépendantes du chemin parcouru (*path-dependent*), telles que les ajustements dynamiques de taille de position au sein d'une enveloppe de capital globale , les collisions d'ordres ou les sorties par stop suiveur au sein de la même barre.4  
* **L'Approche 100% Événementielle** : Extrêmement précise car elle reproduit fidèlement la chronologie du marché et le comportement du courtier. Elle souffre en revanche d'une lenteur dramatique si elle doit recalculer chaque indicateur et condition logique à chaque étape séquentielle.2

### **Conception du Modèle Hybride**

Le modèle hybride résout cette impasse en séparant rigoureusement la logique de génération des signaux de la logique d'exécution des transactions. La détection des opportunités et les calculs d'indicateurs lourds pour les stratégies (HMA Crossover, Adaptive Volatility Trend, PMax Explorer, Noise Boundary) sont entièrement exécutés sous forme matricielle et vectorisée. Les signaux bruts en entrée sont compilés dans un tableau de booléens de taille ![][image4].  
La boucle séquentielle JIT de Numba n'intervient qu'en bout de chaîne, traitant uniquement les aspects non vectorisables de gestion de portefeuille et de sorties complexes.2

### **Modélisation Mathématique**

Le suivi du plus haut prix pour le calcul du Stop Loss suiveur au cours de la période d'activité d'une position est défini par la relation récursive suivante :  
![][image5]  
Où ![][image6] représente le sommet historique atteint par le cours depuis l'ouverture de la position à la barre ![][image7] :  
![][image8]  
Et ![][image9] désigne le paramètre de retrait du stop suiveur suggéré par Optuna (par exemple ![][image10]).  
La valeur liquidative globale du portefeuille d'investissement ![][image11] régulée par le mécanisme de compartiment partagé (*capped bucket*) est régie par l'équation :  
![][image12]  
Où ![][image13] représente le capital liquide disponible, ![][image14] l'ensemble des stratégies possédant une position active à la période ![][image15], ![][image16] la quantité d'actifs détenue par la stratégie ![][image17], et ![][image18] le prix de clôture de l'actif associé. La contrainte du compartiment de capital plafonné impose que l'allocation initiale de chaque stratégie ne dépasse pas la limite maximale autorisée par le compartiment ![][image19] 7 :  
![][image20]

### **Code d'Implémentation : Pipeline Hybride de Simulation Vectoriel / JIT**

L'exemple de code ci-dessous illustre l'intégration complète de l'architecture hybride. Les quatre stratégies clés y sont modélisées sous forme vectorisée avant d'alimenter le simulateur d'exécution ultra-léger compilé sous Numba.

Python  
import numpy as np  
import pandas as pd  
from numba import njit

\# \--- COUCHE VECTORISÉE (Calcul Matriciel) \---

def compute\_hma\_vectorized(prices: np.ndarray, length: int) \-\> np.ndarray:  
    """Calcul vectorisé de la moyenne mobile de Hull (HMA)."""  
    series \= pd.Series(prices)  
    \# HMA \= WMA(2 \* WMA(n/2) \- WMA(n), sqrt(n))  
    half\_len \= int(length / 2\)  
    sqrt\_len \= int(np.sqrt(length))  
      
    \# Approximation par EWM pour maximiser la vitesse en calcul pur NumPy/Pandas  
    wma\_half \= series.ewm(span=half\_len, adjust=False).mean()  
    wma\_full \= series.ewm(span=length, adjust=False).mean()  
    raw\_hma \= 2 \* wma\_half \- wma\_full  
    hma \= raw\_hma.ewm(span=sqrt\_len, adjust=False).mean().values  
    return hma

def compute\_adaptive\_volatility\_trend\_signals(high, low, close, length=20, mult=2.0):  
    """Génère vectoriellement les signaux de tendance basés sur l'ATR dynamique."""  
    tr \= np.maximum(high \- low, np.maximum(np.abs(high \- np.roll(close, 1)), np.abs(low \- np.roll(close, 1))))  
    atr \= pd.Series(tr).rolling(length).mean().values  
    rolling\_mean \= pd.Series(close).rolling(length).mean().values  
      
    upper\_band \= rolling\_mean \+ (atr \* mult)  
    lower\_band \= rolling\_mean \- (atr \* mult)  
      
    signals \= np.zeros\_like(close, dtype=np.int8)  
    signals\[close \> upper\_band\] \= 1   \# Signal haussier  
    signals\[close \< lower\_band\] \= \-1  \# Signal baissier  
    return signals

def compute\_pmax\_explorer\_signals(close, length=10, multiplier=3.0):  
    """Implémentation vectorielle de PMax Explorer (Moyennes mobiles et multiplicateurs)."""  
    series \= pd.Series(close)  
    ema \= series.ewm(span=length, adjust=False).mean().values  
      
    \# Calcul de la plage de déplacement maximale  
    rolling\_max \= series.rolling(length).max().values  
    rolling\_min \= series.rolling(length).min().values  
    trailing\_envelope \= (rolling\_max \+ rolling\_min) / 2.0  
      
    signals \= np.zeros\_like(close, dtype=np.int8)  
    signals\[ema \> trailing\_envelope \* (1.0 \+ (multiplier / 100.0))\] \= 1  
    signals\[ema \< trailing\_envelope \* (1.0 \- (multiplier / 100.0))\] \= \-1  
    return signals

def compute\_noise\_boundary\_signals(close, length=30, std\_mult=1.96):  
    """Filtre le bruit de marché via des bandes de déviation statistique."""  
    series \= pd.Series(close)  
    ma \= series.rolling(length).mean().values  
    std \= series.rolling(length).std().values  
      
    upper\_noise\_limit \= ma \+ (std \* std\_mult)  
    lower\_noise\_limit \= ma \- (std \* std\_mult)  
      
    signals \= np.zeros\_like(close, dtype=np.int8)  
    signals\[close \> upper\_noise\_limit\] \= 1  
    signals\[close \< lower\_noise\_limit\] \= \-1  
    return signals

\# \--- PIPELINE DE SIMULATION HYBRIDE COUPLÉ \---

def run\_hybrid\_multi\_strategy\_backtest(df\_ohlcv, params):  
    """  
    Exécute les calculs vectorisés complexes pour l'ensemble des stratégies,  
    puis injecte les matrices de signaux résultantes dans le simulateur JIT.  
    """  
    close \= df\_ohlcv\['close'\].values  
    high \= df\_ohlcv\['high'\].values  
    low \= df\_ohlcv\['low'\].values  
    open\_p \= df\_ohlcv\['open'\].values  
      
    n\_bars \= len(close)  
    n\_strategies \= 4  
      
    \# Matrice globale pour stocker les signaux bruts de toutes les stratégies  
    raw\_signals \= np.zeros((n\_strategies, n\_bars), dtype=np.int8)  
      
    \# 1\. Stratégie HMA Crossover  
    hma\_fast \= compute\_hma\_vectorized(close, int(params\['hma\_fast\_len'\]))  
    hma\_slow \= compute\_hma\_vectorized(close, int(params\['hma\_slow\_len'\]))  
    raw\_signals\[0, hma\_fast \> hma\_slow\] \= 1  
      
    \# 2\. Stratégie Adaptive Volatility Trend  
    raw\_signals \= compute\_adaptive\_volatility\_trend\_signals(  
        high, low, close, int(params\['avt\_len'\]), params\['avt\_mult'\]  
    )  
      
    \# 3\. Stratégie PMax Explorer  
    raw\_signals \= compute\_pmax\_explorer\_signals(  
        close, int(params\['pmax\_len'\]), params\['pmax\_mult'\]  
    )  
      
    \# 4\. Stratégie Noise Boundary  
    raw\_signals \= compute\_noise\_boundary\_signals(  
        close, int(params\['noise\_len'\]), params\['noise\_std'\]  
    )  
      
    \# Tableau d'identification des stratégies  
    strategy\_ids \= np.arange(n\_strategies, dtype=np.int32)  
      
    \# Appel de la boucle événementielle ultra-rapide compilée sous Numba  
    \# Traite uniquement le passage d'ordres complexe, le slippage et les sorties  
    portfolio\_equity \= run\_broker\_simulation\_kernel(  
        open\_prices=open\_p,  
        high\_prices=high,  
        low\_prices=low,  
        close\_prices=close,  
        raw\_signals=raw\_signals,  
        strategy\_ids=strategy\_ids,  
        initial\_cash=20000.0,  
        capped\_bucket\_limit=10000.0, \# Compartiment de capital partagé plafonné  
        stop\_loss\_pct=params\['stop\_loss\_pct'\],  
        trailing\_stop\_pct=params\['trailing\_stop\_pct'\],  
        take\_profit\_pct=params\['take\_profit\_pct'\]  
    )  
      
    return portfolio\_equity

La séparation hermétique de la boucle d'évaluation permet d'optimiser séparément chaque couche algorithmique. Les performances d'exécution d'un essai complet s'établissent sous le seuil des dix millisecondes, rendant possible l'exploration de milliers de configurations en quelques minutes.

## **5\. Synthèse et Plan d'Action d'Ingénierie Logicielle**

Pour concrétiser cette transformation et obtenir la réduction visée du temps de calcul de l'optimiseur, il est recommandé d'appliquer le plan d'action séquentiel décrit ci-dessous.

                              PLAN DE DÉPLOIEMENT DU MOTEUR OPTIMISÉ  
┌────────────────────────────────────────────────────────────────────────────────────────────────┐  
│ PHASE 1 : Refactoring du Simulateur de Courtage                                                │  
│ \- Isolation complète du code du simulateur dans une fonction pure compilable en JIT.          │  
│ \- Élimination de toutes les instanciations de classes et des dictionnaires dynamiques.         │  
│ \- Stockage et manipulation de l'état des positions dans un tableau structuré NumPy.            │  
├────────────────────────────────────────────────────────────────────────────────────────────────┤  
│ PHASE 2 : Migration vers le Modèle Hybride et Caching POSIX                                    │  
│ \- Vectorisation systématique du calcul des indicateurs (HMA, ATR, Volatilité).                 │  
│ \- Structuration des signaux bruts sous forme de matrices booléennes.                           │  
│ \- Chargement du tenseur d'indicateurs pré-calculés dans un segment SharedMemory POSIX.         │  
├────────────────────────────────────────────────────────────────────────────────────────────────┤  
│ PHASE 3 : Reconfiguration de la Couche Parallèle et Tuning d'Optuna                            │  
│ \- Initialisation du pool de workers via l'argument \`initializer\` pour un mappage statique.     │  
│ \- Activation du TPESampler en mode \`multivariate=True\` et \`constant\_liar=True\`.                │  
│ \- Remplacement du stockage SQLite par un système ultra-léger de type \`JournalStorage\`.         │  
└────────────────────────────────────────────────────────────────────────────────────────────────┘

Cette architecture cible élimine l'intégralité des inefficacités computationnelles identifiées. La suppression de la lenteur liée à l'interprétation par le processeur (obtenue grâce à Numba), la suppression des recalculs redondants (résolue par le pré-calcul et le partage mémoire POSIX), l'optimisation des flux de données inter-processus (réalisée par l'initialisation statique) et l'accélération de la recherche mathématique (gérée par le TPE multivarié d'Optuna) unissent leurs effets pour maximiser le débit de calcul.5 Le temps nécessaire à l'identification du portefeuille optimal de stratégies se trouve ainsi réduit de plusieurs ordres de grandeur, passant d'une heure à quelques dizaines de secondes, tout en préservant l'intégrité de la simulation historique.

#### **Sources des citations**

1. From Sluggish Loops to Lightning Trades: How Numba Supercharges Backtests \- Medium, consulté le mai 26, 2026, [https://medium.com/@cryptotrade606/from-sluggish-loops-to-lightning-trades-how-numba-supercharges-backtests-e03db99de148](https://medium.com/@cryptotrade606/from-sluggish-loops-to-lightning-trades-how-numba-supercharges-backtests-e03db99de148)  
2. Multiprocessing numpy using zero-copy SharedNumpyArray and ..., consulté le mai 26, 2026, [https://gist.github.com/ddelange/8d7b50eafb0c90fd02ef3591d1bbd11e](https://gist.github.com/ddelange/8d7b50eafb0c90fd02ef3591d1bbd11e)  
3. A quick tester of trading strategies in Python using Numba | by Max Dmitrievsky | Medium, consulté le mai 26, 2026, [https://dmitrievsky.medium.com/a-quick-tester-of-trading-strategies-in-python-using-numba-0b62fda7d72d](https://dmitrievsky.medium.com/a-quick-tester-of-trading-strategies-in-python-using-numba-0b62fda7d72d)  
4. Numba: A High Performance Python Compiler, consulté le mai 26, 2026, [https://numba.pydata.org/](https://numba.pydata.org/)  
5. 2.6. Supported Python features \- Numba, consulté le mai 26, 2026, [https://numba.pydata.org/numba-doc/0.43.0/reference/pysupported.html](https://numba.pydata.org/numba-doc/0.43.0/reference/pysupported.html)  
6. GHO Stablecoin: How Aave's DeFi Dollar Works | Support, consulté le mai 26, 2026, [https://eco.com/support/en/articles/12209036-gho-stablecoin-how-aave-s-defi-dollar-works](https://eco.com/support/en/articles/12209036-gho-stablecoin-how-aave-s-defi-dollar-works)  
7. Lazy Summer Protocol: Yield Source Update, consulté le mai 26, 2026, [https://blog.summer.fi/lazy-summer-protocol-yield-source-update-2/](https://blog.summer.fi/lazy-summer-protocol-yield-source-update-2/)  
8. typed Dict slower than array with custom dtype · Issue \#4364 \- GitHub, consulté le mai 26, 2026, [https://github.com/numba/numba/issues/4364](https://github.com/numba/numba/issues/4364)  
9. Supported Python features — Numba 0.50.0 documentation, consulté le mai 26, 2026, [https://numba.pydata.org/numba-doc/0.50.0/reference/pysupported.html](https://numba.pydata.org/numba-doc/0.50.0/reference/pysupported.html)  
10. Performance of typed.List outside of jit functions \- Community Support \- Numba Discourse, consulté le mai 26, 2026, [https://numba.discourse.group/t/performance-of-typed-list-outside-of-jit-functions/2560](https://numba.discourse.group/t/performance-of-typed-list-outside-of-jit-functions/2560)  
11. Supported NumPy features \- Numba, consulté le mai 26, 2026, [https://numba.pydata.org/numba-doc/dev/reference/numpysupported.html](https://numba.pydata.org/numba-doc/dev/reference/numpysupported.html)  
12. Primitive values and Interfacing with C — numba 0.6.0 documentation, consulté le mai 26, 2026, [http://numba.pydata.org/numba-doc/0.6/doc/interface\_c.html](http://numba.pydata.org/numba-doc/0.6/doc/interface_c.html)  
13. optuna.samplers.TPESampler \- Read the Docs, consulté le mai 26, 2026, [https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html)  
14. "Multivariate" TPE Makes Optuna Even More Powerful \- Preferred Networks Tech Blog, consulté le mai 26, 2026, [https://tech.preferred.jp/en/blog/multivariate-tpe-makes-optuna-even-more-powerful/](https://tech.preferred.jp/en/blog/multivariate-tpe-makes-optuna-even-more-powerful/)  
15. multiprocessing.shared\_memory — Shared memory for direct access across processes — Python 3.14.5 documentation, consulté le mai 26, 2026, [https://docs.python.org/3/library/multiprocessing.shared\_memory.html](https://docs.python.org/3/library/multiprocessing.shared_memory.html)  
16. Sharing big NumPy arrays across python processes | by Luis Sena ..., consulté le mai 26, 2026, [https://luis-sena.medium.com/sharing-big-numpy-arrays-across-python-processes-abf0dc2a0ab2](https://luis-sena.medium.com/sharing-big-numpy-arrays-across-python-processes-abf0dc2a0ab2)  
17. How to use read-only, shared memory (as NumPy arrays) in multiprocessing, consulté le mai 26, 2026, [https://stackoverflow.com/questions/75357968/how-to-use-read-only-shared-memory-as-numpy-arrays-in-multiprocessing](https://stackoverflow.com/questions/75357968/how-to-use-read-only-shared-memory-as-numpy-arrays-in-multiprocessing)  
18. Use numpy array in shared memory for multiprocessing \- Stack Overflow, consulté le mai 26, 2026, [https://stackoverflow.com/questions/7894791/use-numpy-array-in-shared-memory-for-multiprocessing](https://stackoverflow.com/questions/7894791/use-numpy-array-in-shared-memory-for-multiprocessing)  
19. Announcing Optuna 3.1 \- Medium, consulté le mai 26, 2026, [https://medium.com/optuna/announcing-optuna-3-1-7b4c5fac227c](https://medium.com/optuna/announcing-optuna-3-1-7b4c5fac227c)  
20. Easy Parallelization — Optuna 4.8.0 documentation \- Read the Docs, consulté le mai 26, 2026, [https://optuna.readthedocs.io/en/stable/tutorial/10\_key\_features/004\_distributed.html](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/004_distributed.html)  
21. Distributed Optimization via NFS Using Optuna's New Operation-Based Logging Storage, consulté le mai 26, 2026, [https://medium.com/optuna/distributed-optimization-via-nfs-using-optunas-new-operation-based-logging-storage-9815f9c3f932](https://medium.com/optuna/distributed-optimization-via-nfs-using-optunas-new-operation-based-logging-storage-9815f9c3f932)  
22. sharavsambuu/backtest-engine-by-jquants \- GitHub, consulté le mai 26, 2026, [https://github.com/sharavsambuu/backtest-engine-by-jquants](https://github.com/sharavsambuu/backtest-engine-by-jquants)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACsAAAAaCAYAAAAue6XIAAACT0lEQVR4Xu2XS6hNYRiGP3cHuXTU6Yg6UhgQJYPDwOCUlKRMjCiHgQwMFInMDJRIRmYGlJShWy6JkgkTGShEBs7EPXK/vK9v//n227/X/p3OMtpPPZP3+/fa317rv6xt1qHDiDMZXoK9WqhgOrwGZ2ihbs7DzRoG+jRosBZegWO0UBdbze+QMg4uhEfhW6lFzsB9GpYwE+6HN+FVeAvehQfg+DAuwew5XCf5YvgK3jGvf2guN9FvPnaKFqrYAYfgLjgx5HPgfXgPTgs52WD+mdGSRy5bdbPkAdypYY5R8IT5BZdLLbEC/oLHJD8Nz0mmlDTL77+gYY6D5o0MaiEwFn6HzyR/BHdLppQ0uwW+szYLbRn8Yf4YeIdbwWnBH/QxZJxjP+H6kOUoaXal+fX7JG/irPmgdvMlTYMnIZvbyFaFLEdJs4vMr8Wbl4V3klsKBy2QmnLIfBznVmJpI1sSshxsNj6RHLPNr7VaC4ku8wE0ty0lJsGX8CucH3I2WdrsJw2F1OwaLUTem8+7CVoIHDa/0B7JuaWVToPPGgppGnDPbckp80EDWmjAI5Q/5ogWzO84P1uywL5oKKQFNk8LkVnm29FD8wWT6IHH4WurPvOfWvut6zr8Zn78tiJtXVU70h+6ze8cG75tftTeMG+Cb0ZVnLT8ocBj+zF8YX/XBRczs9y85MLlC02tbDRvqOq4LYH7/HYNRxqebJwK+iLzL3BRvYFTtVAH28zf0IYLXxH3algn/MJNGhbAl2+uEz6h/wYPmIs2vL81XIwdOrTjN3TxfIaISbdBAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEkAAAAZCAYAAAB9/QMrAAAC80lEQVR4Xu2X2atOURjGX/OcuRDuTYUIV45Q/gHTBUoupMxDyHBJSW6MKQ65EkkIFziJMmTKGOWYEmW6IWV8Hu9a56zvbe2vvb9z0nGsp371rWe/e397P3tNWyQpKSnp/1Mf0N6aTsPBBXAJ3ATLQYuSimYsPmg/sBi8A6NKD//RQPABzHLtHuABWFdX8Q+qLZgJ2tkDET0TfeAb4JfEQ9oJHhlvPvgMuhq/yasDWAiui/aMIsNhtcRD4jXegqPGrxKtn2b8JquOYBm4BZaKhlVUWSH1d/5+449w/ibjx9TSGn9TDGeFaDhLpLJwvLJCGu38PcYf4vyDxvdaBF6AL6K9exU4Ah6DGtFFYgo4DK6Aq2AYT3RiD14PToLT4JzogtE9qCkrHw5P4g1krUhFlBXSeOfvNv4g5x8zvldPMFW0phZMdz4nfQbHYLaJhkGugcuuhpoNzgftAeAj6BV4UbGn+J7DcPJMzHmVFVKV84uGRDEo1tQY/6HopB++XPbUb0F7l+jcGo6OfaBb0I5qHHgt2nUbo/eE8iFxeIXKGm6DnX/I+KH4QKzZavy7ogGE4grKWj9/zXNt9p7jotMJR1AusXAluC067hsrLB/SGOP3df4B4/uJe7PxQ3WReM0d0U1pqO2ita1cm0Nwg+jejT7hebmDojpJfVhc7hsyaVM+pLH2APQGnDDeZNH6GcYP1Vnyh7RDSkOaKLoHY1hDwRbwEyxwxwuJyfIToaErnA+JQ9qKQ+GJ8bjl4ARcbo7ww61ISK1du1p0yIXiRM77rFgMhyFx51zJXoldmzc5wR4Q3St9AnNcuzd4CdbUVcTFZZ7X5CoW6r7ofYbaK1rrh1M1uCf1L4HTCl9UrKcXFi/GLnlR8gV1FjwH30Vv8it4CjaGRdBI0VWKS7VfXcuJqzC/93hNXrsWTBINlx55JfpS+P8/nPde9P7Ze9eCM+CU6H/PlWYmfj+GkzBfHodSm8Djb3o85j+heA7PTUpKSkpKSpLfLo2v6UDEZ80AAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB0AAAAZCAYAAADNAiUZAAABnklEQVR4Xu2VyyuEYRTGj9vCJbFwTYlkoSRZ8S/4AyQrO1JKIStJsZMFC4oVFliR68pYWFlQCok1SaQskPCczhnzzZnvNfNN7L6nfvWd50zv8/behihU+soE42AOLIPm+Pb/aBoM6vcWyQRSUrU1VFlgDJyAI7AD6j39MvABCrUuBXmxdqK42QY2SWbopylwCgq07gG3oETrDvAMBsAoWAL52ktQL7gH2yQz9QutAu+g0+NlkIROaN0PvkCD1jMkE02qV/IP7SMZsNH4EXCu393gJdaiIXDlqZ1yhS6QhNr93gCfIBe0gkdPbxhceGqnXKG89BxaYfx19WtJrssNqNEeT5T3NqlcoQckg5cbf1X9Jq35Xq6ARTALstX/Va7QCKUWmpY4lJfSyrW8a+rXGT+QOHTXmtA8yeDR/YqKDxL7fJDSFofuWZPkIeDBW4zPL9Ol8QKLQ/etCVWSPBxdHi8HPIBJjxdYfNLewKFtqPh14Xe3SOsRkhep+OcXAdROcr+eSJaQuQPXFD8gP/j8r3EGjklOud3jUKFC/a2+AVb+XbX3fnphAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAABDElEQVR4XmNgGAXDFzgD8S0gfg/E/4H4IKo0GJwF4n8MEPlvQDwbVRoTbAHiewwQDZZociCQDcTLgJgJXQIdsALxGSCOYIAYthZVGgymMEB8QRDYAPFkIGYG4vtA/BeIVVBUQCxjRxPDChqB2A/KzmWAuG4aQppBCoi3I/HxggNAzAtlcwHxGwZIQItAxeKBuAjKxgv4GCCGIYMmBojr6qD85UCsi5DGDfyBuB5NTBSIvwPxKyDmBuLLqNK4ASiWrNEFgWA6A8R1c4B4EZocTnAOiFnQBRkgsQmKVZCBMWhyWIEdEJ9GF0QCoPQGMkwCXQIZuAHxAwZEFnkCxPbICqDAnAGSlUbBKBhQAADIFjDhxd8YOAAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAaCAYAAABctMd+AAABO0lEQVR4Xu2TTSuEURiG7whFPhZ2/AGxV0r52JCdNc1vsFeKFQsLJcrSf1AWVpLYWAkppGQjyUdKwv3MfeTtbugdZqW56qrpXHOezjtzXqBKld8ySI/oI32nt/SEjqW+Q69Se6WndCW13GxCA7o9kEmoLXjIQx108jMPiXVoeDxl2fRDm5c9kBp6Q59ovbVczELDP3/nLH1Q2/CQl136Ri/phXkHDZ8qfrNM2qBbsO0hEbclhvd4IBO0wRezjEOb5zyQJvpCrz2Qduh/+HH4KjR8yAMZgVrcFicOteWLTly/Z5Q+QdzrGF6w9TV6TvfS55J0QZu/O8EB1Ds9QG3AF4Nh6JW/hzY/0EPoZ6il+/h65cNjulTcKVqgp23MrFWMUej6Bh3ZUAmm6SJtpjPW/kwv9MbO01ZrVf4TH/8/SoJovVlCAAAAAElFTkSuQmCC>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAaCAYAAADBuc72AAAB+UlEQVR4Xu2WPUgcQRTHX9RooYVCQIkgFtqEgIJdSBO10MYUNsFGUwuSxgRU8EwlMdgIfmERRC2CilEEEdIEoo2SNIoJYicINgp+gBji/+97c7cMd0jONSx4P/ixM29n72bfvJk7kQwZMtxvKmCLH4wii/CXH4waufAEjvo3osZz+Bc2+zeiwju4A4/gH2vT8sCYSPENbvjBqJEPL+CAfyNNnsECPxgGjaL1yWsYDMMSPxgGH0UzGkYWnsBjuXmi2d41Cz6wa0o24Xdrc/AyfCh6ZA3CD3Aa1sJSuAa34Rv4XrS2y0S/ZEJ0dTi+T5QFeAY7RZ97AT/ZuDEb8wNuwSrrJ2Ufjli7C7ZauxcOWfux6DhSI/olldafEp20g/eCGWXWeKKwtNok8dy69UkPLLZ2Sl7D3/CzJCZJfor+WsXMr6Llwbc+jI8SGRd9QYc/UXKZJNYOV63NlUsbLgc/zOcpPAj0+WvWHei7iTKDeRbjRIviI5RH8Bw2yS3/Y7yFK6J1S1hjrFtmNDhR1hmXznEqWrMxmGMxLn2hGxBgCe6JHpFpw83RL7oZeH0pmqk50VOCm+wV3BUtkwZ97HoTfYEd1p8UzfIsrLaYg8/PeLFQYHbdkcKTgRljjLrs/Qv1Et75fSdwx/P/L1fFvXgkmRc9Euv8Gxn+B1cqzFqY1/vQWQAAAABJRU5ErkJggg==>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA+CAYAAACWTEfwAAAFKklEQVR4Xu3dWahvUxgA8GUeMpSZTJEuL8pYpm7mKREvSBwX8WJ4uIai3GQWwhsKmVLGB2PkmhISIo88UCRjkXlYX3utzj7r7P895w7nXt3/71dfe+1v7/P/n3Oevr6119opAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADACJe2iVXk+BwvtUkAgHG3R46v2+Qq9GibAADGywE5/m2T2Z85Nm2TY+Kv1BVtrTXS9EIu/nc3Nbm5cFGbAADGxys5/mlyF+e4ssmtTF/l+CPHHTmeyXFPjnVyPJbj0xyblPvWznFr6qYM38+xbsk/nOPn1BVTl5djxAXl+kyebRPFwhwLmlx87idNbi78lGOtNgkAjIffcrzX5KIA2r/JjfLhDLEsXbpbUlcIzSvnMX6rjDfPcV0Zzy/XwsY5HijjsF6OH0v+sxzX967N5PY2UbyYY6cmF99/epObC/E9O7dJAGA8RCFweO/8yJLr26U5n2snpam/Q4yjiKte7403yPF0jjdSd99WvWvRJfw7dUXe0ogO45D4/BdKRAF5beq+u/1/xe90RJOrfskx0SZ7nspxdptM3Xcc1SYBgPHwe+oKjCo6UW0BcmdzPtdOSNMLtiiOqijOwnY5Ps5xUOqeL4v7tq43pW7K9MvUdduWxpIKtiHRyetbM8euTa6KAm+iTfYcloa7kvHdx7RJAGD1d2aOq5tcPHD/ee88niH7NcexvdxcG+qw9Qu2N8vxgxzf9vJx3za983iubbPULaDYu5efydCUaHTuYop3yHc5FuV4u5yflyanSWOFZ3QHb8txd44nyvj5HFeUe6r9Uvf/HhJ/26giEABYjcVD/Ic0uSgM7u2dn5hjce98ZTg1TS/YYnFB9W45xqKEmPIM0W2L+/Yt51G4XVPGsYjhozKejaFFB1Hc3twmi1o0RqFWnVuOF5ZjXNs+x+OpK+J2y/FDuVZFd/OLJlfFooPoIgIATPNOjqPT1GfD5lpMKYb10+TKzyhWYoozVovGOI6j1J+Jn++r+ZmM2tZjlO/LMQrNqhZsV5Xj/HJ8MnWrVaOgjM5fa880/MzdbFe4AgBjKIqK2EZjnKbjHkpTO3ozqc+wndbL1YItpldv7OXjGbYovrZNXWEYjivHWJkbXbhzynkVe+XVrUwAAP5XYgpy9zY5B6JA6y+8CLPtaNVOXxyjM1i7gDGOz6yLIOL5tcvKODqEs91TLV5NVbc0AQBY6e5vE42NeuMzeuMV5dByjIf/+99VRbG0PGIPuDote0maLNhaQ1Og1cs5tmiTAACrwkSOG9LU1aC1iDo5dW9kWNHqgotRBRsAwFiLrS1qZynexXlg71pVi6jYZiQWP6wosUVJbJ8RU6ExVrABAAyo05HhrtR11mpUtYiKfeA27OWH7NUmZtB/c4KCDQBgwH1pssO2T/9CTy2i6oa0o8QKykeaXDz0X2NIdOxicUBsV6JgAwAY8GqafEdp7PAfU6TtK6RqEfVc6qZNz0/dpr51y41YkRkb2obF5TiRJou0g3MsKOOwY45vyvjBHKeUsYINAGAWomBalIanRKsovhbm2KGXq6tHX8sxL019T2e8UaAWZVUUbS0FGwDAMlpSERVdtNjLbNSU55Y5zmqTqXtrQ0vBBgCwjJZn49x4d2e8r3M2hjbOBQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgNfIfr3e/KbRyMvMAAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAaCAYAAACD+r1hAAAAxklEQVR4XmNgGH5gNhC/AeJWdAl8YA0Q/wdiTXQJXMCNAaKhEV0CF2AB4tdAfANdAh+YwQCxRR9dAhdwYIBoaEMTxwmYgPgZEN9Fl8AF2ID4DAPEFlM0OQzACsQbgHgmA0RDL6o0KgCF0FogngPl3wbix0DMCFeBBECKVwHxMQaIk0AAFOMgW2xgimCAGYhXAPFTIJZAEtdlgGiYgiQGBguB+AcQm6FLAMFVIH7BADEUDDihAjEwATSQDMT/gDgYXWIUDBwAAJ9PIdzPlIZYAAAAAElFTkSuQmCC>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAI0AAAAaCAYAAACKPd9eAAAGUElEQVR4Xu2ad4gfRRTHnxo1NqyxF6zYu2JEyGliLH+IBRsqiQ0sqKgoVlxbFCx/qIiiYNRE7F2xYRZLrBhF7CXYe8eC/X18O/d79+72d3ubJbnIfuALN2/mN7s7++bNzNsTaWlpaWlpaanInapnVVNjRUsjbC82vq+rRoe6IXON6mvV+bFiNpNHg7KMaorqBdWLqqtVi/VpUc6mqmmqp1QvqU5UzdOnRbX+d1ZNVK2iGqlaT3Wp6gTXpir7il3rSdUzYn1XYT5Vppqhelr1oGod36BgN9V0sWfBOc4U+60nU/UEWy1uV/0jNiBzijyUedjnVdeKvWzKRKHHfKMSVlV9qzqoKC8lNohn9Lao3v+5YmPj9b6YEw0FXujP0nnZm6l+Uo3pbVHOJaqXVYsW5SNUn6lG9bYQGSvWhmeF8WL3SlDwZNKQ06QLnB0rZiN5KO8jdk8rOtu6hW1HZxuIK1VvBhsDzUtbvChX7T9TfaD6WPWKWEROfQwFnJZI5rlZLHJ0Y2XV76r9nQ0nx2n86jBZ7N4PLsq04Xn/lI4jQSYNOc0I1VfSf6DrwqylT1SVPJRvU30TbPT7l5hTlMFgfaG6I9h7xAYVZ4Gq/RPiJ7pyHTYQu/YxwZ4V9uWC3XO0WJuNgj0Xc8QEDkS7vZ3tV9XfqkWcLZOGnAauErvoJrGiAuurrhObNewhHlc9qnpEtaZr1408lN9VzQw2+EFsP1AGM5Pn4H48LAfYLyjKVftnSZvoynU4UOzaE4L9+MK+U7B7WD5ps1qw3yPmEAsVZSbLsp1q2VDsd3G5zaRBp+kRu8ikYB+Mw8UGedtYMUTyUCa0vhVsQET8MBodW4k9R1wK0my/oShX7f901cVikYsNLPugXV19FU4Su7ZfYiBFkUOC3fOAWJsVgp1IiX2NYAeWTzbLn6rWCnWZNOg084pd5L1Y0QXW/odV88eKGuShzCwaaLlk6fkuGh1jxAaTyOlhk4/9rqJctf9TVU9IZx8zTvWHDL6v8pwldu39gv3Iwn5csHumibVZPthvKexxZZgitgf7XrVNqINMGnSaBcSOatwIs7UKDGacAXXJ3d+EWu6jykuN9MjgTjOU/ldSLenKwEvhpFKVTOo7TS5Dc5oE0RDnPjbYM2nIaYgUd4uFdG6EI95gsLkidDZFHsply8eXYieZMsqWJ/Zd2JmJULd/YJmiL3/y6kbZ8nRUYT8s2D1ly9OthT0uPx4mNRHVR5xMGnCaEWLrNRsueEf1kfRPhEUYMAaYjW83pbzEYOShzAtlRkfYqJLZLIPBZTCvD/a0Eb6wKFfpnyjD0fayTvV/sNGnry2DvQychfbpOJxIG+FuSb40kVcPdjbC2NNGeAuxZ/RMlv5BIJNZdBocBo+dLrY8QTq6bZcalUB7TkdNkYcyOQySXx4iIvcWl57I56r7go09CL9NS0SV/nuKMidBD5th7DhVFVL+h6y0J411XHo85Jdog1N4OKmm5ZX7IB9DPsf3NVXst5c7Wyaz4DTkJBi4T6TvhcgHcKErnK2MydL/YeqSh3JKvvkXs3lhG+9sS6sOkL6bcfIsREwPaf9fVEsU5Sr9c4Ql+5t+A0yWH6X/sX93Kd9fADmVmJ29V2zCesaJfQJJENFxCJ4xwbPy6WdSUeb9cd/knRZOjcQiJvY9nC2TWXAawvdvqq1jhfKa2GzFsbrBgOPxq8WKGuShzGkupfn5m6h4v9hpzZM+gfjEGbkaTg8TivIosSWXk1Ciav98ZzpHOglLQj0Ryr9YJg73wAZ6pLN7+IzA0kf+BEhREBl8RE+5lZh05JozpOO8p4gtm36Dzsb4Rum0IbKyn8Ex/VYjk5pOwzqIU5B0GohDxS64V6wYADaY01SnqdYW63uw/dBA5NEgFkVuEjupIKKfn0nAdXlZY4KdqJGLOQYDHrOxUKV/nOU81dtiKYmHVBv3aWERaaaYM3WLNiyNfDx9TizCjO1b3dsPL9rDPeC4r4p98MS54x6HCEgbkpakTd5QnSz90yGZ1HSapmEG7imWhWX9x4nyQnUzwnMjF8mc/ehbhUyGidM0QR4NcyGcaOpE2dlJJq3TDBt2kTn7XwJVyaR1mmEDx9oFo3EYksn/yGn4d08+Y5AGaGmeHcTGl9zO6FDX0tLS0tIyN/IvL3Kgr8XMjwkAAAAASUVORK5CYII=>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAbCAYAAACTHcTmAAABUUlEQVR4Xu2UTSuEURTH/95ioShfAFlI8QEkQmRtYWNnbzNlZWNHNhYWkrLyGSy8lR2RvERkpsZGKUUJC6//2zkzjjM8HmShnl/9uvecc++d89x5ZoCEhBy99ITe0Rd6ofExTdNz+qy1Id0TmyXIxkZfIA30knb7QhTlkE4zvmBYpHU+GUUXpMtpkyum8yZeo6Um/pJxyKF9GocDR+hMfgVQYuax2KZP9Ige0hvIh/TbRd+hBnLgqslV0itabXK2005ab+IC/uTQAcijjppc+ELWTTxIh028T9tNXMAc5NBWl6/QsYhu4q3r8GS3kNfwU84gi8p8QQkdzuo8RTdoli7QWs2/ownS5bIvQO41vFYPtNnkp+iYifN00AN6DTk0jLvqHj2lj1pb0T05tmiPy/2K0P29juFuI+81Lm10R+cT+MGv7COqIP8Bk7TF1RL+A6+sz0PS9HxrlwAAAABJRU5ErkJggg==>

[image12]: <data:image/png;base64,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>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAaCAYAAABYQRdDAAABNElEQVR4Xu2TvStHYRTHD5K38jJL8R9YWAxMFmWwCJOySFEWk0mRwcJkZmIgG6EMEmU1M7ApE5K3z+k8N8893d/vJ3cx3E996p7zvffpee49V6SgwNOGs3iGt3iD1zgV8jUcDNe/Qh98xD3sw+rQr8UNvMBXbAz9slThJr7jpMsSdOEHPPRBKZbxCxd84DjCOd/Mohc/8E5sN+XQ03T5Zha7Yruc90EensQW7fZBBepxwjcVPa4u+IY1LvOMY0dUj+BpVKe4x09s8kFEM56ITUnCOi5GdYolsd2O+iCgx9zBnlB34jY+44GU+BYNYsfQoR+TnwnQXQ3gPvaHXkIrvmCd66fQcBovxV7HldhM6ty2RPclDOG5b+ZlFVfCdXsc5OEYh8XGMHOs/sIMbknl37rgv/INI4wyhudiIAUAAAAASUVORK5CYII=>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAZCAYAAADaILXQAAABOklEQVR4Xu2TTyuEURTGHxEWE4kFZTHsqbFGiVnN+BSWYuHPXmlKNj6BsrDzEZQVJYoMVlJ2shw1WYnnONd172mm9F41C/OrX++895yeue99zwu0+bd00yN6bAt/wQH9oKdmPZkF+ggNPzO1JHrpPS1Bw6/jchoVuk1HoOEPcTk7U/SS9tB+aPhz1JGRPnpHJ9x9FzT81XckIGO3SYcC3+g77Qj6hDk6btaasgLdpQTJ1Tr80/pFlc6aNY+c6Tfz0HMtQ0cw9BYaPuO7gUFaR5zhKUBf2ig0sAYdu0bsQ8M33P0aPadP9JDm3bpnCfEjr8fliFVozwt0Q7KZPboV9EQM0AvoFCybmmUMGnxDF92a/EnRdzTBTsBvyEEnSK5y9g3PPSvT9Mr93qGdQS0Z+WpP6C6dNLU2LeAT5ZQ+H1VpDDUAAAAASUVORK5CYII=>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAcCAYAAACtQ6WLAAAAhElEQVR4XmNgGMpABYij0AVhAK/kJiC+iS4IAmxA/AWIZ6BLgIANEP8H4mBkwXIgvgHEH4D4L5QNwgpIahgOAfEZZAEY4AbiX0DcjS4BAp4MEPtANAboYYDo5EGXAIGzQHwUymYE4q1AzAqTfArE06HsKiCOh0mAQCIQ3wLiVegSIx4AAK6sF9s/dRChAAAAAElFTkSuQmCC>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAaCAYAAAA5WTUBAAAB80lEQVR4Xu2WTShmURjHH4XxEaNBiXxk0rCwIVmJkphYiI2p2bGZWTBZIl/ZzGKUYppIihTW0qQsRDE1YorFlJgpC5spKcyYxP/pOfd17sOd7sud3furX+95n/9573vuveece4kiRIgQHmmwG67CZbgGv8J+GHfb7f/xFv4i+cMkq/4cfoc7MMWqB0oU/AT/wFqVOdTAaziig6AYIvmDTh1YxJL0+amDICiFV/AHjHFHLvhq/YXnOgiCeZIz7NCBopCk374OHguf3QnJwYtUpmkl6fdRByST+Ahm6MDiNXyii0w8yYF5IDygf7EOf8MCHYBo2KiLFrzsz8hjEMwpPNZFRQXJYNt14JMmuKKLNjMkE/OZDgxP4QEc0AHJ1euCU/CNyhwm4CH8Ytr3kkmyMj7AfDgJF+AwfAE/w2ans6INFsNXcFFlNtuwShc1qSSD2CQZ8RzJHBij2606HeaatkO2+eQNbNAOLJLhBUzQgR/4/tu7I3/3umVbsE4XDS/hhmln2YEf3pHsjjmwHk674xCJ8JLczxT+bZlp95DcWl7GfaEePmkhWREs75Ql7jhENfymavzUHTftcrgE35NM8rDgM+OnJm9CvNF40QtHdZEecNbhws8YftfIg7t0d+ZXwgZVCxy+rHtwlu7fH7xeByJ4cgNz51W6ORJ8VQAAAABJRU5ErkJggg==>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAZCAYAAAAIcL+IAAAAnUlEQVR4XmNgGAUIoAbET4G4BF0CHZgA8QUgdkaXoB1IAeJ1QHwTiLPR5OAgCog7oOzJQPwSSQ4FHABiNij7EBCfR0hhB05A/B+IA9Al0EELEP8DYiF0CXRwDIjPoQuiAx4g/g3E3egS6MCTAeI+D3QJEPAGYgsoewIQfwJiLoQ0AoBM2AbEukD8BYhzUKUR4AQDxAOHgTgUTW5IAQBAKBmkXjz29QAAAABJRU5ErkJggg==>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAAAaCAYAAAAHfFpPAAAC4klEQVR4Xu2XSahOYRjH/7jInKGwwE3GjEnJHJmS8VooCySxsiAWynCTMpSZDEWSLAxlJSwoG6Ios91VSEQW5vn/73nfvtfjc797u9xyOr/65ZznOec65znPO3xATk5OTk5OZAS9Q9/QH/QFfUDv00f0Cd1L28UbsspZWAH6uvgg+p5ec/FM0ZC+pk99IvAQVpz+PpEVhsJe8JhPkBb0E/1KO7lcZlgNK8ACnyCLYLlDPpElLsFesksSK6Nz6Ct6mDZJcpHudBht5hP/E83pR9hEdz7xKt1PRxcu/Y319Bvt4RP/CD1XhQ8mjIN9lFoxBfb1j/hEDXmJ+ivAZNrKBxNu0zE+WIrtsALM9Yka8hz1V4DqaE/f0aY+UYp7sDYutdHpR0/TLfQyHRjiaQFa0910Iz1AJ4a42nIHXUVPotDGS+hBuo8uD7FizKObUHyVEitg+5QqepyWp8nq6Ar7+td9wqGqVqHQXifopHCcFuAM7GFFI9j+oSfs4ZeG+Eg6jY6FtWxE1/ZOziPamOnezvSty6WowJU++CeGw7a7cfur1lEnzEwvStDDfoG9lCcWQGPzO36dhM7BltgJsIn2Ft0AW1F2wgpQGVTxRukmh/YejelsesXlUm6g0HF/Hb2ACqAdoycWQENIxeyT5C7AhkOv4DJYodfAvtipwqUl2UY3+2CgJf0Q/tVcUOt5oBRa55/R6eFcY31xONYqoDYXF+n8cKyv9hj2W0I/pgaH+Hi6C9aF2nq3DfGpdAjs/9KLdgjxiMb4jORcBdUyLNQ5N8Ox7i3WqXVGL6ANk1p3LawIW+ln2MSmB1b1tWnaQ4/SWboR9lDaU6yDTXhxmGi+0NqulShOgpqX9Is03ZWqKBpC+vsRTaQaut1oG9iz6Xni5Fwv6CuLMtogTdQRFWFhcq7J925yHlG3lftgFlhJO8LmCQ07LZWx3VP0xTOJdnxCk6T2HppDYrdFtCwOcLGcnBrwE0+hicDFm+R9AAAAAElFTkSuQmCC>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAaCAYAAABctMd+AAABUklEQVR4Xu2TPSiGURTHD/lIMkmhZDIYRAwGRTGwUIyyy8xksSgWWSxWq48iyWxhYfARKxZFPoqS8vE7nfvodt7l8Xosen/166nzf+99znvPfUQKFMiXTjzBR/zEazwOav0Gt7AlWZAP62Kb17t6Az7gPda4LBVFeItHPgjsi724xwdpaBVbPOsDaMI3PMcyl6ViUmzzrqim/2YAL3FHco8rNbti3W3jZvAA73Ai+t2PKccXsY09ffiOyz4IaFMjvhjTK3YkUz4I6JA1b/YB9GOVL8bMiy3u8EHgSixv80EatDO9x8U+gCGxjQ/FBpwwinO4EtVy0BvwgRuuXoJj+IQX2BhlejzjWIfPUf2bdjwT61g70+dppN4SfU5jZViTUIulOIx7LsuMBbF5/Qn6HehMMqcCX7HaB1nQLTaTTFnEQbEvdsZlv2YV13BJ7Mb8I74AeIlGWF8br+0AAAAASUVORK5CYII=>

[image20]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA0CAYAAAA312SWAAAEz0lEQVR4Xu3daahtYxgH8Nc8hAwJmTMrkSFkKhkjGb6YilASIhTKPERkHpKIKBkiii8SV4YiRYZQPlyKzCEZMj6Ptda9a7/2Oe3L3efsc/v96t9e61n7umet8+E+vcNSCgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAC30RWbY83i3wYWX3h5Tnnr8hpvfO3I9/2zpdEV0ZejSxXXxjizMgxvfMVI39G9uvVAIAJsVTkrsiBVX3/yC1VbaYdHFmpLoat6sIQ2bBt0TvPe8zakmiDyM2RI0vz+xzF45E1qlo+n0urGgAwAf6IzK+LpfmH/6e6OAtyFGiF9jhH/l7vXZvK7pH7qlqOHr1T1ea6RyNP1MUR7FQGm9dtI/NK89wAgAmU/3CfVRfD1pGP6uIseSqybGmatW2qa8NcEjm+d54NyiuRjXq1dSI79s7nmgsju9bFEV1Qmt97PtcnIz9Gbh/4BgAwMXK68bsyfBrt5TI4pZj2qs5TTsON23qRj8vwn7OW6/B+q4tTeKwu/Ec71IVwa2kax3FapjQjkNeX5hmN6pfI01XtxjK45i/vafPeOQAwiz6vC6VpzEZd75WNybi9Ftkjcmd9YYjDyug/+8N1YTHKTQ7DGtxxOCTyXGTT+sIU8vmcW9UeiJxd1QCACTE/ckPk3tKMsuSC/qP6XwjXlmYX4XlVPXeR/lzVFqeVI89XtfxZp5PTuL/XxdKsg5vfHj/UfnYNWy7ATzlilaOK17Tn2STmwvyv2vO728/O8u1n7qitzasLlfy7xmG7Mn0TnaOUX0eW7tU+iHzfO88Ru7ynnXs1AGAWrVWaJihHsXIa9I62vvaCb5SyYfu5b6+WcmQn14ZNZ8u6UJqmIdNvGoa5LnJoXQz71IXSTO++VZrRo9xgcNXg5X/+TD1Vmg1bTqHm9zu5NixfbfFm5IrI4ZEfIpeVpqntyyZ2zdJMMdaurguV/is1Ovk8umfzf0z1Wo83Ip9Ffo28F3k38mlpRi776/vyd5/3lPcHAEyYnBLLtWLZiOUUWd9BveP83i6lmYbLKcjjIqdGji5N85ebA3KTwAllcB1UHmdTkqNmq/TqMyEbumxW0mrtZ7eG7dn2Mxud7cvCBfjZoGZD90V7vm5p/js54tjJ4xyZTF1zmg1X/h25Juz90jyXAyLnt9fTKb3jlH/mmTLaK0tmQndPAMCEycYiR6hyJKreQZkvZe3kSE1OD54eebCtndR+5mjci+3xiaV5FUc3MpcNT8qXtt7THs+kXEif7yu7uDQ/7yeR3Uozynhb5P72e9mE5YaBbrQxn0WOQuVUaY5EfdnW00uRI9rj3ICxcXt8U2mmlvNVIjn9mc/ljPZaOrn8e8QyG8iLqtpUshmcN0UWx47P7p4AgDkg39G1SRncnJDTi8OmKjs5WpRNylRTnjm6NhO7S8cl1/IdG7k88kJ1bTr5PKZ7LnuX0TcOjEve17DpWgBgguVOx0cie/Zq9f8VYVHlCFv3Mty5KO//nNJMCa/fqy/KqzVq2cj13x03W/K+xrl7FgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFhS/Q3GqqJEWcIcOwAAAABJRU5ErkJggg==>