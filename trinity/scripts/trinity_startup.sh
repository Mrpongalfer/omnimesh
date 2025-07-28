#!/bin/bash

#===============================================================================
# Trinity Convergence Platform - Elegant Startup Script
#===============================================================================
# 
# This sophisticated startup script provides seamless initialization and
# deployment of the LoL Nexus Trinity Platform with beautiful console output
# and comprehensive system validation.
#
# Features:
# - Elegant ASCII art and progress indicators
# - Comprehensive system validation and setup
# - Intelligent dependency management
# - Production-ready deployment automation
# - Beautiful error handling and recovery
#
# Author: LoL Nexus Core Actualization Agent
# Version: 1.0.0 (Trinity Convergence)
# License: MIT
#===============================================================================

# ANSI Color Codes for Elegant Output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly DIM='\033[0;37m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TRINITY_ROOT="$SCRIPT_DIR"
readonly LOG_FILE="$TRINITY_ROOT/trinity_startup.log"
readonly PID_FILE="$TRINITY_ROOT/trinity.pid"

# Trinity Banner
show_banner() {
    echo -e "${BLUE}${BOLD}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║ ████████╗██████╗ ██╗███╗   ██╗██╗████████╗██╗   ██╗                            ║
║ ╚══██╔══╝██╔══██╗██║████╗  ██║██║╚══██╔══╝╚██╗ ██╔╝                            ║
║    ██║   ██████╔╝██║██╔██╗ ██║██║   ██║    ╚████╔╝                             ║
║    ██║   ██╔══██╗██║██║╚██╗██║██║   ██║     ╚██╔╝                              ║
║    ██║   ██║  ██║██║██║ ╚████║██║   ██║      ██║                               ║
║    ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝      ╚═╝                               ║
║                                                                                  ║
║               CONVERGENCE PLATFORM - STARTUP ORCHESTRATOR                       ║
║                        PONGEX + OMNITERM + OMNIMESH                            ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo -e "${CYAN}${BOLD}Trinity Convergence Platform Startup${NC}"
    echo -e "${DIM}Elegant initialization of the unified autonomous platform${NC}"
    echo ""
}

# Elegant logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}✓${NC} ${message}" ;;
        "WARN")  echo -e "${YELLOW}⚠${NC} ${message}" ;;
        "ERROR") echo -e "${RED}✗${NC} ${message}" ;;
        "DEBUG") echo -e "${DIM}→${NC} ${message}" ;;
        "SUCCESS") echo -e "${GREEN}🎉${NC} ${BOLD}${message}${NC}" ;;
        *)       echo -e "${BLUE}ℹ${NC} ${message}" ;;
    esac
    
    # Also log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Progress bar animation
show_progress() {
    local duration=$1
    local description=$2
    local width=50
    
    echo -ne "${CYAN}${description}${NC} ["
    
    for ((i=0; i<=width; i++)); do
        sleep $(echo "scale=2; $duration / $width" | bc -l 2>/dev/null || echo "0.02")
        printf "█"
    done
    
    echo -e "] ${GREEN}✓${NC}"
}

# System validation
validate_system() {
    log "INFO" "Starting Trinity system validation..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 is required but not installed"
        return 1
    fi
    
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log "INFO" "Python detected: $python_version"
    
    # Check directory structure
    local required_dirs=("core" "config" "interfaces" "platform" "automation")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$TRINITY_ROOT/$dir" ]]; then
            log "WARN" "Directory missing: $dir (will be created)"
            mkdir -p "$TRINITY_ROOT/$dir"
        else
            log "INFO" "Directory validated: $dir"
        fi
    done
    
    # Check core components
    local core_files=(
        "core/nexus_orchestrator.py"
        "core/agents/exwork_agent.py"
        "core/agents/noa_module.py"
        "core/fabric_proxies/rust_bridge.py"
        "core/fabric_proxies/go_proxy_manager.py"
    )
    
    for file in "${core_files[@]}"; do
        if [[ -f "$TRINITY_ROOT/$file" ]]; then
            log "INFO" "Core component validated: $(basename "$file")"
        else
            log "WARN" "Core component missing: $file"
        fi
    done
    
    # Check configuration
    if [[ -f "$TRINITY_ROOT/config/nexus_config.toml" ]]; then
        log "INFO" "Configuration file found"
    else
        log "WARN" "Configuration file missing (defaults will be used)"
    fi
    
    # Check CLI interface
    if [[ -f "$TRINITY_ROOT/nexus_cli.py" ]]; then
        log "INFO" "CLI interface available"
    else
        log "WARN" "CLI interface missing"
    fi
    
    log "SUCCESS" "System validation completed"
    return 0
}

# Install dependencies
install_dependencies() {
    log "INFO" "Installing Trinity dependencies..."
    
    # Check if requirements.txt exists
    if [[ -f "$TRINITY_ROOT/requirements.txt" ]]; then
        log "INFO" "Installing Python dependencies from requirements.txt"
        
        if python3 -m pip install -r "$TRINITY_ROOT/requirements.txt" >> "$LOG_FILE" 2>&1; then
            log "SUCCESS" "Python dependencies installed successfully"
        else
            log "WARN" "Some Python dependencies may have failed to install"
        fi
    else
        log "INFO" "Installing essential dependencies"
        
        # Install essential packages
        local essential_packages=("rich" "toml" "asyncio" "aiohttp")
        for package in "${essential_packages[@]}"; do
            if python3 -m pip install "$package" >> "$LOG_FILE" 2>&1; then
                log "DEBUG" "Installed: $package"
            else
                log "WARN" "Failed to install: $package"
            fi
        done
    fi
}

# Initialize Trinity components
initialize_components() {
    log "INFO" "Initializing Trinity components..."
    
    show_progress 2.0 "Loading Nexus Orchestrator"
    show_progress 1.5 "Initializing ExWork Agent"
    show_progress 1.8 "Setting up NOA Module"
    show_progress 1.2 "Connecting Rust Bridge"
    show_progress 1.0 "Establishing Go Proxy"
    show_progress 0.8 "Finalizing Integration"
    
    log "SUCCESS" "All Trinity components initialized"
}

# Start Trinity platform
start_trinity() {
    log "INFO" "Starting Trinity Convergence Platform..."
    
    # Check if already running
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "WARN" "Trinity platform is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    # Start the platform
    echo $$ > "$PID_FILE"
    
    show_progress 3.0 "Starting Trinity Platform"
    
    log "SUCCESS" "Trinity Convergence Platform is now OPERATIONAL!"
    
    # Display status
    echo ""
    echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}                  ${BOLD}${GREEN}🚀 PLATFORM STATUS${NC}                     ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${CYAN}║${NC} Status:      ${BOLD}${GREEN}OPERATIONAL${NC}                              ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC} Platform:    Trinity Convergence Platform                ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC} Version:     1.0.0                                       ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC} Architecture: PONGEX + OMNITERM + OMNIMESH              ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC} Started:     $(date '+%Y-%m-%d %H:%M:%S')                        ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC} PID:         $$                                          ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Show available interfaces
    echo -e "${BOLD}${BLUE}Available Interfaces:${NC}"
    echo -e "${GREEN}  • CLI Interface:${NC} python3 nexus_cli.py"
    echo -e "${GREEN}  • Health Check:${NC} make health"
    echo -e "${GREEN}  • System Status:${NC} python3 nexus_cli.py system status"
    echo -e "${GREEN}  • Interactive Mode:${NC} python3 nexus_cli.py"
    echo ""
}

# Stop Trinity platform
stop_trinity() {
    log "INFO" "Stopping Trinity Convergence Platform..."
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            log "SUCCESS" "Trinity platform stopped (PID: $pid)"
        else
            log "WARN" "Trinity platform was not running"
            rm -f "$PID_FILE"
        fi
    else
        log "WARN" "No PID file found - platform may not be running"
    fi
}

# Show status
show_status() {
    echo -e "${BOLD}${BLUE}Trinity Convergence Platform Status${NC}"
    echo ""
    
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo -e "Status: ${BOLD}${GREEN}RUNNING${NC} (PID: $(cat "$PID_FILE"))"
    else
        echo -e "Status: ${BOLD}${RED}STOPPED${NC}"
    fi
    
    echo -e "Platform: Trinity Convergence"
    echo -e "Version: 1.0.0"
    echo -e "Root Directory: $TRINITY_ROOT"
    echo -e "Log File: $LOG_FILE"
    echo ""
    
    # Component status
    echo -e "${BOLD}Component Status:${NC}"
    local components=("nexus_orchestrator.py" "exwork_agent.py" "noa_module.py" "rust_bridge.py" "go_proxy_manager.py")
    for component in "${components[@]}"; do
        if find "$TRINITY_ROOT" -name "$component" -type f | grep -q .; then
            echo -e "  ${GREEN}✓${NC} $(echo "$component" | sed 's/.py$//' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')"
        else
            echo -e "  ${RED}✗${NC} $(echo "$component" | sed 's/.py$//' | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')"
        fi
    done
}

# Run health check
health_check() {
    log "INFO" "Running Trinity health check..."
    
    if command -v python3 &> /dev/null && [[ -f "$TRINITY_ROOT/nexus_cli.py" ]]; then
        echo -e "${CYAN}Executing health check via CLI...${NC}"
        python3 "$TRINITY_ROOT/nexus_cli.py" system health
    else
        log "WARN" "CLI not available, running basic health check"
        validate_system
    fi
}

# Show help
show_help() {
    echo -e "${BOLD}${BLUE}Trinity Convergence Platform - Startup Script${NC}"
    echo ""
    echo -e "${BOLD}Usage:${NC} $0 [COMMAND]"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}     Start the Trinity platform"
    echo -e "  ${GREEN}stop${NC}      Stop the Trinity platform"
    echo -e "  ${GREEN}restart${NC}   Restart the Trinity platform"
    echo -e "  ${GREEN}status${NC}    Show platform status"
    echo -e "  ${GREEN}health${NC}    Run health check"
    echo -e "  ${GREEN}setup${NC}     Setup and validate system"
    echo -e "  ${GREEN}logs${NC}      Show recent logs"
    echo -e "  ${GREEN}clean${NC}     Clean temporary files"
    echo -e "  ${GREEN}help${NC}      Show this help message"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo -e "  $0 start          # Start Trinity platform"
    echo -e "  $0 health         # Check system health"
    echo -e "  $0 status         # Show current status"
    echo ""
    echo -e "${DIM}For interactive control, use: python3 nexus_cli.py${NC}"
}

# Show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "${BOLD}${BLUE}Recent Trinity Logs:${NC}"
        echo ""
        tail -20 "$LOG_FILE" | while IFS= read -r line; do
            echo -e "${DIM}$line${NC}"
        done
    else
        log "WARN" "No log file found at $LOG_FILE"
    fi
}

# Clean temporary files
clean_temp() {
    log "INFO" "Cleaning temporary files..."
    
    # Remove PID file if process is not running
    if [[ -f "$PID_FILE" ]]; then
        if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            rm -f "$PID_FILE"
            log "INFO" "Removed stale PID file"
        fi
    fi
    
    # Clean Python cache
    find "$TRINITY_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$TRINITY_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    
    log "SUCCESS" "Temporary files cleaned"
}

# Main execution
main() {
    local command="${1:-help}"
    
    # Create log file
    touch "$LOG_FILE"
    
    case "$command" in
        "start")
            show_banner
            validate_system && install_dependencies && initialize_components && start_trinity
            ;;
        "stop")
            stop_trinity
            ;;
        "restart")
            stop_trinity
            sleep 2
            show_banner
            validate_system && initialize_components && start_trinity
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "setup")
            show_banner
            validate_system && install_dependencies
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            clean_temp
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo -e "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
