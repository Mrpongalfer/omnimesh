#!/bin/bash

# UMCC System Stop Script
# Gracefully stops all UMCC components
# Timestamp: Wednesday, July 23, 2025 at 3:56:25 PM CDT in Moore, Oklahoma

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# UMCC Project Root
UMCC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UMCC_PROJECT_ROOT="${UMCC_ROOT}"

# PID directory for daemon management
PID_DIR="${UMCC_ROOT}/data/pids"

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if a process is running
is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to stop a daemon
stop_daemon() {
    local daemon_name="$1"
    local pid_file="${PID_DIR}/${daemon_name}.pid"

    if ! is_running "$pid_file"; then
        info "${daemon_name} is not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    info "Stopping ${daemon_name} (PID: $pid)..."

    # Try graceful shutdown first
    if kill -TERM "$pid" 2>/dev/null; then
        # Wait up to 10 seconds for graceful shutdown
        local count=0
        while [[ $count -lt 10 ]] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            ((count++))
        done

        # If still running, force kill
        if kill -0 "$pid" 2>/dev/null; then
            warn "Force killing ${daemon_name} (PID: $pid)"
            kill -KILL "$pid" 2>/dev/null || true
        fi
    fi

    # Clean up PID file
    rm -f "$pid_file"
    log "✅ ${daemon_name} stopped"
}

# Function to stop all daemons
stop_daemons() {
    log "🛑 Stopping UMCC daemon constellation..."

    # Stop daemons in reverse dependency order
    local daemons=("chimera_daemon" "midas_daemon" "logos_daemon" "chronos_daemon" "telos_engine_daemon" "noosphere_daemon" "sentinel_daemon" "oracle_daemon" "agent_ex_work")

    for daemon_name in "${daemons[@]}"; do
        stop_daemon "$daemon_name"
    done

    log "✅ All daemons stopped"
}

# Function to clean up resources
cleanup_resources() {
    log "🧹 Cleaning up UMCC resources..."

    # Remove PID files for any remaining processes
    if [[ -d "$PID_DIR" ]]; then
        rm -f "${PID_DIR}"/*.pid
    fi

    # Clean up any temporary files
    local temp_dirs=("${UMCC_ROOT}/data/temp" "${UMCC_ROOT}/data/smcep_staging")
    for temp_dir in "${temp_dirs[@]}"; do
        if [[ -d "$temp_dir" ]]; then
            rm -rf "$temp_dir"
            info "Cleaned temporary directory: $temp_dir"
        fi
    done

    log "✅ Resources cleaned up"
}

# Function to display final status
show_final_status() {
    log "📊 Final UMCC System Status:"
    echo

    # Check for any remaining processes
    local daemons=("agent_ex_work" "oracle_daemon" "sentinel_daemon" "noosphere_daemon" "telos_engine_daemon" "chronos_daemon" "logos_daemon" "midas_daemon" "chimera_daemon")
    local running_count=0

    for daemon in "${daemons[@]}"; do
        local pid_file="${PID_DIR}/${daemon}.pid"
        if is_running "$pid_file"; then
            local pid=$(cat "$pid_file")
            echo -e "  ${RED}●${NC} ${daemon} (PID: $pid) - STILL RUNNING"
            ((running_count++))
        else
            echo -e "  ${GREEN}●${NC} ${daemon} (stopped)"
        fi
    done

    echo
    if [[ $running_count -eq 0 ]]; then
        echo -e "${GREEN}✅ All UMCC components stopped successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  $running_count component(s) still running${NC}"
    fi
    echo
}

# Function to force kill all UMCC processes
force_kill_all() {
    warn "🔥 Force killing all UMCC processes..."

    # Kill processes by name pattern
    local process_patterns=("agent_ex_work" "telos_engine" "oracle_daemon" "sentinel_daemon" "noosphere_daemon" "chronos_daemon" "logos_daemon" "midas_daemon" "chimera_daemon")

    for pattern in "${process_patterns[@]}"; do
        local pids=$(pgrep -f "$pattern" || true)
        if [[ -n "$pids" ]]; then
            echo "Killing processes matching '$pattern': $pids"
            echo "$pids" | xargs -r kill -KILL
        fi
    done

    # Clean up all PID files
    rm -rf "$PID_DIR"
    mkdir -p "$PID_DIR"

    warn "🔥 Force kill completed"
}

# Main stop sequence
main() {
    local force_mode="${1:-}"

    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║    🛑 UMCC - Unfettered Mobile Command Center                 ║"
    echo "║    🏛️  The Architect's Digital Dominion Shutting Down...     ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [[ "$force_mode" == "--force" ]] || [[ "$force_mode" == "-f" ]]; then
        force_kill_all
    else
        stop_daemons
    fi

    cleanup_resources
    show_final_status

    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║    🏁 UMCC Shutdown Complete                                  ║"
    echo "║    😴 The Architect's Digital Dominion is at rest...         ║"
    echo "║                                                                ║"
    echo "║    To restart: ${UMCC_ROOT}/scripts/start_umcc.sh              ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Handle script arguments
case "${1:-stop}" in
    "stop"|"")
        main
        ;;
    "--force"|"-f"|"force")
        main --force
        ;;
    "status")
        show_final_status
        ;;
    "help"|"--help"|"-h")
        echo "UMCC System Stop Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  stop      Gracefully stop all UMCC components (default)"
        echo "  --force   Force kill all UMCC processes"
        echo "  -f        Alias for --force"
        echo "  force     Alias for --force"
        echo "  status    Show current system status"
        echo "  help      Show this help message"
        echo ""
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
