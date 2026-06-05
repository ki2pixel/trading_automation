#!/bin/bash

# Script de gestion du backtest_engine et de son worker
# Auteur: Trading Automation v2
# Usage: ./start_backtest_engine.sh

set -e  # Arrêter le script en cas d'erreur

# Configuration
ACTION=""
HOST="127.0.0.1"
PORT="8765"
REPO_ROOT="."

# Redirect optimizer/backtest reports via BACKTEST_REPORTS_DIR env var
export BACKTEST_REPORTS_DIR="${BACKTEST_REPORTS_DIR:-/mnt/venv_ext4/trading_automation_v2/reports}"
export NUMBA_CPU_FEATURES="-avx512f,+avx2"
OUTPUT_DIR="$BACKTEST_REPORTS_DIR/local_optimizer"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour vérifier si un port est utilisé
is_port_in_use() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port utilisé
    else
        return 1  # Port libre
    fi
}

# Fonction pour arrêter le backtest_engine serve
stop_server() {
    log_info "Vérification du serveur backtest_engine sur le port $PORT..."
    
    if is_port_in_use $PORT; then
        log_warning "Le port $PORT est actuellement utilisé. Arrêt du processus existant..."
        
        # Arrêter le processus spécifique
        if pkill -f "python3 -m backtest_engine serve.*--port $PORT"; then
            log_success "Processus backtest_engine serve arrêté"
            sleep 2  # Attendre que le port se libère
        else
            log_error "Impossible d'arrêter le processus backtest_engine serve"
            return 1
        fi
        
        # Vérifier que le port est bien libéré
        if is_port_in_use $PORT; then
            log_error "Le port $PORT est toujours utilisé après tentative d'arrêt"
            log_info "Processus utilisant le port $PORT:"
            lsof -Pi :$PORT -sTCP:LISTEN
            return 1
        else
            log_success "Port $PORT libéré avec succès"
        fi
    else
        log_success "Le port $PORT est déjà disponible"
    fi
}

# Fonction pour démarrer le serveur backtest_engine
start_server() {
    log_info "Démarrage du serveur backtest_engine..."
    
    # Vérifier que le module backtest_engine existe
    if ! python3 -c "import backtest_engine" 2>/dev/null; then
        log_error "Module backtest_engine non trouvé. Vérifiez votre installation Python."
        return 1
    fi
    
    # Démarrer le serveur en arrière-plan
    python3 -m backtest_engine serve --host $HOST --port $PORT --output-dir "$OUTPUT_DIR" &
    SERVER_PID=$!
    
    log_info "Serveur démarré avec PID: $SERVER_PID"
    
    # Attendre que le serveur soit prêt
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if is_port_in_use $PORT; then
            log_success "Serveur backtest_engine prêt sur http://$HOST:$PORT"
            return 0
        else
            log_info "Attente du démarrage du serveur... (tentative $attempt/$max_attempts)"
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    log_error "Le serveur n'a pas démarré après $max_attempts tentatives"
    return 1
}

# Fonction utilitaire de nettoyage du superviseur
cleanup_supervisor() {
    log_warning "Superviseur: signal d'arrêt reçu."
    local supervisor_pid_file="$OUTPUT_DIR/supervisor.pid"
    local worker_pid_file="$OUTPUT_DIR/worker.pid"
    local worker_id_file="$OUTPUT_DIR/worker.id"
    
    if [ -f "$worker_pid_file" ]; then
        local w_pid=$(cat "$worker_pid_file" 2>/dev/null)
        if [ -n "$w_pid" ] && kill -0 "$w_pid" 2>/dev/null; then
            log_info "Superviseur: envoi de SIGTERM au worker (PID: $w_pid)..."
            kill "$w_pid" 2>/dev/null || true
        fi
    fi
    rm -f "$supervisor_pid_file" "$worker_pid_file" "$worker_id_file"
    exit 0
}

# Boucle de supervision du worker en arrière-plan
supervise_worker_loop() {
    local supervisor_pid_file="$OUTPUT_DIR/supervisor.pid"
    local worker_pid_file="$OUTPUT_DIR/worker.pid"
    local worker_id_file="$OUTPUT_DIR/worker.id"

    # Enregistrer le PID du superviseur
    echo $$ > "$supervisor_pid_file"

    # Trap pour relayer les signaux d'arrêt au worker enfant
    trap cleanup_supervisor INT TERM

    log_info "Superviseur démarré avec le PID $$"

    while true; do
        # Générer un worker_id unique
        local worker_id="worker_$(date +%Y%m%d_%H%M%S)_$((100 + RANDOM % 900))"
        local log_file="$OUTPUT_DIR/worker_$(date +%Y%m%d_%H%M%S).log"

        echo "$worker_id" > "$worker_id_file"
        log_info "Démarrage du worker ($worker_id)..."
        log_info "Logs redirigés vers: $log_file"

        # Lancer le worker en arrière-plan
        python3 -m backtest_engine worker --repo-root "$REPO_ROOT" --output-dir "$OUTPUT_DIR" --worker-id "$worker_id" > "$log_file" 2>&1 &
        local worker_pid=$!
        echo "$worker_pid" > "$worker_pid_file"

        # Attendre le processus du worker (compatible avec set -e)
        local exit_code
        wait "$worker_pid" && exit_code=0 || exit_code=$?

        # Supprimer le fichier PID du worker car il a fini
        rm -f "$worker_pid_file"

        if [ $exit_code -eq 0 ]; then
            log_success "Le worker ($worker_id) s'est arrêté normalement (exit code 0)."
            break
        else
            log_error "Le worker ($worker_id) a crashé avec le code de sortie: $exit_code"
            case $exit_code in
                137)
                    log_error "Détail du crash: Arrêt brutal (OOM / SIGKILL)."
                    ;;
                139)
                    log_error "Détail du crash: Erreur de segmentation (Segfault / SIGSEGV)."
                    ;;
                *)
                    log_error "Détail du crash: Exception Python ou signal d'arrêt externe."
                    ;;
            esac

            # Nettoyer les tâches IN_PROGRESS du worker crashé
            log_warning "Nettoyage des jobs IN_PROGRESS pour le worker crashé ($worker_id)..."
            python3 -m backtest_engine --repo-root "$REPO_ROOT" mark-crashed --output-dir "$OUTPUT_DIR" --worker-id "$worker_id" --exit-code "$exit_code" || true

            log_info "Attente de 5 secondes avant de redémarrer le worker..."
            sleep 5
        fi
    done

    # Nettoyage à la sortie propre de la boucle
    rm -f "$supervisor_pid_file" "$worker_id_file"
}

# Fonction pour démarrer le worker
start_worker() {
    log_info "Démarrage du superviseur du worker backtest_engine..."
    
    # Vérifier que le répertoire de sortie existe
    if [ ! -d "$OUTPUT_DIR" ]; then
        log_info "Création du répertoire de sortie: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
    
    # Lancer la boucle de supervision en arrière-plan
    supervise_worker_loop &
    SUPERVISOR_PID=$!
    
    log_success "Superviseur du worker lancé en arrière-plan (PID: $SUPERVISOR_PID)"
}

# Fonction pour afficher l'état des processus
show_status() {
    log_info "État des processus :"
    
    echo
    echo "=== SERVEUR ==="
    if is_port_in_use $PORT; then
        local server_pid=$(lsof -ti:$PORT -sTCP:LISTEN)
        echo -e "✅ Serveur backtest_engine: ${GREEN}EN MARCHE${NC} (PID: $server_pid, Port: $PORT)"
        echo "   URL: http://$HOST:$PORT"
        echo "   API Docs: http://$HOST:$PORT/docs"
    else
        echo -e "❌ Serveur backtest_engine: ${RED}ARRÊTÉ${NC}"
    fi
    
    echo
    echo "=== SUPERVISEUR ==="
    local supervisor_pid_file="$OUTPUT_DIR/supervisor.pid"
    local supervisor_running=false
    if [ -f "$supervisor_pid_file" ]; then
        local sup_pid=$(cat "$supervisor_pid_file" 2>/dev/null)
        if [ -n "$sup_pid" ] && kill -0 "$sup_pid" 2>/dev/null; then
            echo -e "✅ Superviseur du worker: ${GREEN}EN MARCHE${NC} (PID: $sup_pid)"
            supervisor_running=true
        fi
    fi
    if [ "$supervisor_running" = false ]; then
        echo -e "❌ Superviseur du worker: ${RED}ARRÊTÉ${NC}"
    fi
    
    echo
    echo "=== WORKER ==="
    if pgrep -f "python3 -m backtest_engine worker" > /dev/null; then
        local worker_pids=$(pgrep -f "python3 -m backtest_engine worker")
        local worker_id_file="$OUTPUT_DIR/worker.id"
        local worker_id_str=""
        if [ -f "$worker_id_file" ]; then
            worker_id_str=" (ID: $(cat "$worker_id_file" 2>/dev/null))"
        fi
        echo -e "✅ Worker backtest_engine: ${GREEN}EN MARCHE${NC}${worker_id_str} (PIDs: $worker_pids)"
        echo "   Répertoire de sortie: $OUTPUT_DIR"
    else
        echo -e "❌ Worker backtest_engine: ${RED}ARRÊTÉ${NC}"
    fi
    echo
}

# Fonction de nettoyage lors de l'arrêt du script
cleanup() {
    if [ "$ACTION" = "start" ]; then
        echo
        log_warning "Arrêt du script de supervision interactif..."
        log_info "Les processus serveur et worker continuent de tourner en arrière-plan."
        log_info "Utilisez './start_backtest_engine.sh stop' pour tout arrêter."
        log_info "Utilisez './start_backtest_engine.sh status' pour vérifier l'état."
    fi
}

# Fonction pour arrêter tous les processus
stop_all() {
    log_info "Arrêt de tous les processus backtest_engine..."
    
    # Arrêter le superviseur s'il est présent
    local supervisor_pid_file="$OUTPUT_DIR/supervisor.pid"
    if [ -f "$supervisor_pid_file" ]; then
        local sup_pid=$(cat "$supervisor_pid_file" 2>/dev/null)
        if [ -n "$sup_pid" ]; then
            log_info "Arrêt du superviseur (PID: $sup_pid)..."
            # Envoyer SIGTERM au superviseur. Le trap du superviseur enverra SIGTERM au worker.
            kill "$sup_pid" 2>/dev/null || true
            sleep 2
        fi
        rm -f "$supervisor_pid_file"
    fi

    # Arrêter le serveur
    if pkill -f "python3 -m backtest_engine serve" 2>/dev/null; then
        log_success "Serveur backtest_engine arrêté"
    fi
    
    # Tuer tout worker restant par sécurité
    if pkill -f "python3 -m backtest_engine worker" 2>/dev/null; then
        log_success "Worker backtest_engine résiduel arrêté"
    fi

    # Nettoyer les fichiers pid/id restants par précaution
    rm -f "$OUTPUT_DIR/worker.pid" "$OUTPUT_DIR/worker.id"
    
    log_success "Tous les processus backtest_engine ont été arrêtés"
}

# Gestion des signaux
trap cleanup INT TERM

# Fonction principale
main() {
    ACTION="${1:-start}"
    case "$ACTION" in
        "start")
            log_info "Démarrage complet du système backtest_engine..."
            echo
            
            stop_server
            start_server
            start_worker
            
            echo
            log_success "Système backtest_engine démarré avec succès!"
            show_status
            
            echo
            log_info "Utilisez Ctrl+C pour arrêter ce script (les processus continueront)"
            log_info "Utilisez '$0 stop' pour arrêter tous les processus"
            log_info "Utilisez '$0 status' pour vérifier l'état"
            
            # Garder le script en vie pour superviser et afficher l'état
            while true; do
                sleep 10
                # Vérifier périodiquement que les processus tournent toujours
                if ! is_port_in_use $PORT; then
                    log_error "Le serveur a crashé! Redémarrage..."
                    start_server
                fi
                
                local supervisor_pid_file="$OUTPUT_DIR/supervisor.pid"
                local supervisor_running=false
                if [ -f "$supervisor_pid_file" ]; then
                    local sup_pid=$(cat "$supervisor_pid_file" 2>/dev/null)
                    if [ -n "$sup_pid" ] && kill -0 "$sup_pid" 2>/dev/null; then
                        supervisor_running=true
                    fi
                fi
                
                if [ "$supervisor_running" = false ]; then
                    log_error "Le superviseur du worker a crashé ou est arrêté! Redémarrage..."
                    start_worker
                fi
            done
            ;;
            
        "stop")
            stop_all
            ;;
            
        "status")
            show_status
            ;;
            
        "restart")
            stop_all
            sleep 2
            main "start"
            ;;
            
        "help"|"-h"|"--help")
            echo "Usage: $0 [start|stop|restart|status|help]"
            echo
            echo "Commandes:"
            echo "  start    - Arrête les processus existants puis démarre le serveur et le worker (défaut)"
            echo "  stop     - Arrête tous les processus backtest_engine"
            echo "  restart  - Redémarre tous les processus"
            echo "  status   - Affiche l'état actuel des processus"
            echo "  help     - Affiche cette aide"
            echo
            echo "Configuration:"
            echo "  Host: $HOST"
            echo "  Port: $PORT"
            echo "  Repo Root: $REPO_ROOT"
            echo "  Output Dir: $OUTPUT_DIR"
            ;;
            
        *)
            log_error "Commande inconnue: $1"
            echo "Utilisez '$0 help' pour voir les commandes disponibles"
            exit 1
            ;;
    esac
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "backtest_engine/__main__.py" ]; then
    log_error "Ce script doit être exécuté depuis la racine du projet trading_automation_v2"
    log_error "Fichier manquant: backtest_engine/__main__.py"
    exit 1
fi

# Rendre le script exécutable
chmod +x "$0"

# Lancer la fonction principale
main "$@"
