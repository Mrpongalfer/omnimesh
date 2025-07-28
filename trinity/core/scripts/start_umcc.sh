#!/bin/bash

# UMCC System Startup Script
# Starts all UMCC components in the correct order
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
mkdir -p "$PID_DIR"

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

# Function to start a daemon
start_daemon() {
    local daemon_name="$1"
    local daemon_path="$2"
    local pid_file="${PID_DIR}/${daemon_name}.pid"

    if is_running "$pid_file"; then
        warn "${daemon_name} is already running (PID: $(cat "$pid_file"))"
        return 0
    fi

    info "Starting ${daemon_name}..."
    cd "$daemon_path"

    if [[ -f "main.go" ]]; then
        # Go daemon
        go run main.go > "${UMCC_ROOT}/logs/${daemon_name}.log" 2>&1 &
        local pid=$!
        echo $pid > "$pid_file"
        log "✅ ${daemon_name} started (PID: $pid)"
    elif [[ -f "main.py" ]] || [[ -f "${daemon_name}.py" ]]; then
        # Python daemon
        if [[ -f "pyproject.toml" ]]; then
            poetry run python main.py > "${UMCC_ROOT}/logs/${daemon_name}.log" 2>&1 &
        else
            python3 main.py > "${UMCC_ROOT}/logs/${daemon_name}.log" 2>&1 &
        fi
        local pid=$!
        echo $pid > "$pid_file"
        log "✅ ${daemon_name} started (PID: $pid)"
    else
        error "No executable found for ${daemon_name}"
        return 1
    fi

    sleep 2  # Give daemon time to initialize
}

# Function to check prerequisites
check_prerequisites() {
    log "🔍 Checking UMCC prerequisites..."

    # Check if binaries exist or can be built
    if [[ ! -d "${UMCC_ROOT}/bin" ]]; then
        warn "Binary directory not found. Running build script first..."
        "${UMCC_ROOT}/scripts/build.sh"
    fi

    # Check configuration
    if [[ ! -f "${UMCC_ROOT}/config/config.toml" ]]; then
        error "Configuration file not found: ${UMCC_ROOT}/config/config.toml"
        exit 1
    fi

    # Create log directory
    mkdir -p "${UMCC_ROOT}/logs"

    log "✅ Prerequisites checked"
}

# Function to start Agent Ex-Work (Python)
start_agent_ex_work() {
    local agent_path="${UMCC_ROOT}/agent_ex_work"
    local pid_file="${PID_DIR}/agent_ex_work.pid"

    if is_running "$pid_file"; then
        warn "Agent Ex-Work is already running (PID: $(cat "$pid_file"))"
        return 0
    fi

    info "Starting Agent Ex-Work v3.0 (The Genesis Agent)..."
    cd "$agent_path"

    if [[ -f "pyproject.toml" ]]; then
        poetry run python agent_ex_work.py > "${UMCC_ROOT}/logs/agent_ex_work.log" 2>&1 &
    else
        python3 agent_ex_work.py > "${UMCC_ROOT}/logs/agent_ex_work.log" 2>&1 &
    fi

    local pid=$!
    echo $pid > "$pid_file"
    log "✅ Agent Ex-Work started (PID: $pid)"

    sleep 3  # Give Agent Ex-Work time to initialize
}

# Function to start all daemons
start_daemons() {
    log "🚀 Starting UMCC daemon constellation..."

    # Start daemons in dependency order
    local daemons=(
        "oracle_daemon:${UMCC_ROOT}/daemons/oracle_daemon"
        "sentinel_daemon:${UMCC_ROOT}/daemons/sentinel_daemon"
        "noosphere_daemon:${UMCC_ROOT}/daemons/noosphere_daemon"
        "telos_engine_daemon:${UMCC_ROOT}/daemons/telos_engine_daemon"
        "chronos_daemon:${UMCC_ROOT}/daemons/chronos_daemon"
        "logos_daemon:${UMCC_ROOT}/daemons/logos_daemon"
        "midas_daemon:${UMCC_ROOT}/daemons/midas_daemon"
        "chimera_daemon:${UMCC_ROOT}/daemons/chimera_daemon"
    )

    for daemon_spec in "${daemons[@]}"; do
        IFS=':' read -r daemon_name daemon_path <<< "$daemon_spec"
        if [[ -d "$daemon_path" ]]; then
            start_daemon "$daemon_name" "$daemon_path"
        else
            warn "Daemon directory not found: $daemon_path (skipping)"
        fi
    done

    log "✅ Daemon constellation started"
}

# Function to display system status
show_status() {
    log "📊 UMCC System Status:"
    echo

    # Show running processes
    local daemons=("agent_ex_work" "oracle_daemon" "sentinel_daemon" "noosphere_daemon" "telos_engine_daemon" "chronos_daemon" "logos_daemon" "midas_daemon" "chimera_daemon")

    for daemon in "${daemons[@]}"; do
        local pid_file="${PID_DIR}/${daemon}.pid"
        if is_running "$pid_file"; then
            local pid=$(cat "$pid_file")
            echo -e "  ${GREEN}●${NC} ${daemon} (PID: $pid)"
        else
            echo -e "  ${RED}●${NC} ${daemon} (stopped)"
        fi
    done

    echo
    echo -e "${BLUE}📁 Project Root:${NC} ${UMCC_ROOT}"
    echo -e "${BLUE}📋 Log Directory:${NC} ${UMCC_ROOT}/logs"
    echo -e "${BLUE}📈 Data Directory:${NC} ${UMCC_ROOT}/data"
    echo -e "${BLUE}⚙️  Configuration:${NC} ${UMCC_ROOT}/config/config.toml"
    echo
}

# Function to start the console (if available)
start_console() {
    local console_bin="${UMCC_ROOT}/bin/umcc_console"

    if [[ -f "$console_bin" ]]; then
        log "🖥️  Starting Architect's Console..."
        "$console_bin"
    else
        warn "Console binary not found. Build the system first: ./scripts/build.sh"
        info "You can monitor the system via log files in: ${UMCC_ROOT}/logs/"
    fi
}

# Main startup sequence
main() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║    🏛️  UMCC - Unfettered Mobile Command Center               ║"
    echo "║    🧠 The Architect's Digital Dominion Initializing...       ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_prerequisites

    log "🎯 Initiating UMCC Genesis Sequence..."

    # Start core components
    start_agent_ex_work
    start_daemons

    # Show system status
    show_status

    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║    🎉 UMCC Genesis Complete!                                  ║"
    echo "║    🏆 The Architect's Digital Dominion is OPERATIONAL        ║"
    echo "║                                                                ║"
    echo "║    Next Steps:                                                 ║"
    echo "║    • Monitor logs: tail -f ${UMCC_ROOT}/logs/*.log             ║"
    echo "║    • Access Console: ${UMCC_ROOT}/bin/umcc_console             ║"
    echo "║    • Stop System: ${UMCC_ROOT}/scripts/stop_umcc.sh            ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # If --console flag is provided, start the console
    if [[ "${1:-}" == "--console" ]]; then
        start_console
    fi
}

# Handle script arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "status")
        show_status
        ;;
    "console")
        start_console
        ;;
    "--console")
        main --console
        ;;
    "help"|"--help"|"-h")
        echo "UMCC System Control Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     Start all UMCC components (default)"
        echo "  status    Show system status"
        echo "  console   Start the Architect's Console"
        echo "  --console Start system and launch console"
        echo "  help      Show this help message"
        echo ""
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
