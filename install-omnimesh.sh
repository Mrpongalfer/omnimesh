#!/bin/bash

# 🌊 OMNIMESH Universal Installer
# Intelligent auto-setup script for the complete OMNIMESH ecosystem
# Architect's Absolute Dominion - One Script to Rule Them All

set -euo pipefail

# Global Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/install.log"
readonly CONFIG_FILE="${SCRIPT_DIR}/omni-config.yaml"
readonly INSTALL_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Colors and styling
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# System detection variables
OS_TYPE=""
ARCH=""
INSTALL_CMD=""
PKG_MGR_UPDATE_CMD=""
PYTHON_CMD=""
NODE_CMD=""
PACKAGE_MANAGER=""

# Installation options
INSTALL_BACKEND=true
INSTALL_FRONTEND=true
INSTALL_INFRASTRUCTURE=true
INSTALL_CONTROL_CENTER=true
INSTALL_DOCKER=true
INSTALL_KUBERNETES=false
INSTALL_AI=false
DEVELOPMENT_MODE=false
PRODUCTION_MODE=false

# Dependencies tracking
declare -A DEPENDENCIES_STATUS
declare -A OPTIONAL_DEPENDENCIES

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Banner and welcome
show_banner() {
    clear
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                     🌊 OMNIMESH UNIVERSAL INSTALLER                          ║${NC}"
    echo -e "${PURPLE}║                                                                              ║${NC}"
    echo -e "${PURPLE}║              Next-Generation Distributed AI Orchestration Platform          ║${NC}"
    echo -e "${PURPLE}║                        Architect's Absolute Dominion                        ║${NC}"
    echo -e "${PURPLE}║                                                                              ║${NC}"
    echo -e "${PURPLE}║  🚀 One Script to Install Everything  •  🧠 AI-Powered  •  🛡️ Secure      ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}Installation Log: ${LOG_FILE}${NC}"
    echo -e "${CYAN}Installation ID: ${INSTALL_TIMESTAMP}${NC}"
    echo
}

# System detection
detect_system() {
    log_info "🔍 Detecting system architecture..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS_TYPE="linux"
        log_info "Detected Linux system"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        log_info "Detected macOS system"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        OS_TYPE="windows"
        log_info "Detected Windows system"
    else
        log_error "Unsupported operating system: ${OSTYPE}"
        exit 1
    fi
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64|amd64) ARCH="x64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        armv7*) ARCH="arm" ;;
        *) log_warn "Unknown architecture: $ARCH, assuming x64" ; ARCH="x64" ;;
    esac
    
    log_info "System: ${OS_TYPE} ${ARCH}"
}

# Package manager detection and setup
setup_package_manager() {
    log_info "🔧 Setting up package manager..."
    
    case "$OS_TYPE" in
        "linux")
            if command -v apt &> /dev/null; then
                PACKAGE_MANAGER="apt"
                INSTALL_CMD="sudo apt-get install -y"
                PKG_MGR_UPDATE_CMD="sudo apt-get update"
            elif command -v yum &> /dev/null; then
                PACKAGE_MANAGER="yum"
                INSTALL_CMD="sudo yum install -y"
                PKG_MGR_UPDATE_CMD="sudo yum check-update"
            elif command -v dnf &> /dev/null; then
                PACKAGE_MANAGER="dnf"
                INSTALL_CMD="sudo dnf install -y"
                PKG_MGR_UPDATE_CMD="sudo dnf check-update"
            elif command -v pacman &> /dev/null; then
                PACKAGE_MANAGER="pacman"
                INSTALL_CMD="sudo pacman -S --noconfirm"
                PKG_MGR_UPDATE_CMD="sudo pacman -Sy"
            else
                log_error "No supported package manager found on Linux"
                exit 1
            fi
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            PACKAGE_MANAGER="brew"
            INSTALL_CMD="brew install"
            PKG_MGR_UPDATE_CMD="brew update"
            ;;
        "windows")
            if command -v choco &> /dev/null; then
                PACKAGE_MANAGER="chocolatey"
                INSTALL_CMD="choco install -y"
                PKG_MGR_UPDATE_CMD="choco upgrade all -y"
            elif command -v winget &> /dev/null; then
                PACKAGE_MANAGER="winget"
                INSTALL_CMD="winget install"
                PKG_MGR_UPDATE_CMD="winget upgrade --all"
            else
                log_error "No supported package manager found on Windows. Please install Chocolatey or use winget."
                exit 1
            fi
            ;;
    esac
    
    log_success "Package manager: ${PACKAGE_MANAGER}"
    
    # Update package manager
    log_info "Updating package manager..."
    if ! eval "${PKG_MGR_UPDATE_CMD}"; then
        log_warn "Failed to update package manager, continuing anyway..."
    fi
}

# Python detection and setup
setup_python() {
    log_info "🐍 Setting up Python environment..."
    
    # Find Python command
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_info "Installing Python..."
        case "$PACKAGE_MANAGER" in
            "apt") eval "$INSTALL_CMD python3 python3-pip python3-venv" ;;
            "yum"|"dnf") eval "$INSTALL_CMD python3 python3-pip python3-venv" ;;
            "pacman") eval "$INSTALL_CMD python python-pip" ;;
            "brew") eval "$INSTALL_CMD python@3.11" ;;
            "chocolatey") eval "$INSTALL_CMD python" ;;
            "winget") eval "$INSTALL_CMD Python.Python.3.11" ;;
        esac
        PYTHON_CMD="python3"
    fi
    
    # Verify Python version
    local python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    local major_version=$(echo "$python_version" | cut -d'.' -f1)
    local minor_version=$(echo "$python_version" | cut -d'.' -f2)
    
    if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
        log_error "Python 3.8+ required, found: $python_version"
        exit 1
    fi
    
    log_success "Python: $python_version ($PYTHON_CMD)"
    
    # Setup virtual environment
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    if [[ "$OS_TYPE" == "windows" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
}

# Node.js detection and setup
setup_nodejs() {
    log_info "📦 Setting up Node.js environment..."
    
    # Check for Node.js
    if command -v node &> /dev/null; then
        NODE_CMD="node"
        local node_version=$(node --version | sed 's/v//')
        local major_version=$(echo "$node_version" | cut -d'.' -f1)
        
        if [[ $major_version -lt 18 ]]; then
            log_warn "Node.js 18+ recommended, found: $node_version"
        else
            log_success "Node.js: $node_version"
        fi
    else
        log_info "Installing Node.js..."
        case "$PACKAGE_MANAGER" in
            "apt") 
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                eval "$INSTALL_CMD nodejs"
                ;;
            "yum"|"dnf") 
                curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
                eval "$INSTALL_CMD nodejs npm"
                ;;
            "pacman") eval "$INSTALL_CMD nodejs npm" ;;
            "brew") eval "$INSTALL_CMD node" ;;
            "chocolatey") eval "$INSTALL_CMD nodejs" ;;
            "winget") eval "$INSTALL_CMD OpenJS.NodeJS" ;;
        esac
        NODE_CMD="node"
    fi
    
    # Setup pnpm (preferred package manager)
    if ! command -v pnpm &> /dev/null; then
        log_info "Installing pnpm..."
        npm install -g pnpm
    fi
    
    log_success "Node.js environment ready"
}

# Rust detection and setup
setup_rust() {
    log_info "🦀 Setting up Rust environment..."
    
    if ! command -v cargo &> /dev/null; then
        log_info "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    local rust_version=$(rustc --version | cut -d' ' -f2)
    log_success "Rust: $rust_version"
    
    # Install required Rust components
    rustup component add clippy rustfmt
}

# Go detection and setup
setup_go() {
    log_info "🐹 Setting up Go environment..."
    
    if ! command -v go &> /dev/null; then
        log_info "Installing Go..."
        case "$PACKAGE_MANAGER" in
            "apt"|"yum"|"dnf") eval "$INSTALL_CMD golang-go" ;;
            "pacman") eval "$INSTALL_CMD go" ;;
            "brew") eval "$INSTALL_CMD go" ;;
            "chocolatey") eval "$INSTALL_CMD golang" ;;
            "winget") eval "$INSTALL_CMD GoLang.Go" ;;
        esac
    fi
    
    local go_version=$(go version | cut -d' ' -f3)
    log_success "Go: $go_version"
}

# Docker setup
setup_docker() {
    if [[ "$INSTALL_DOCKER" != true ]]; then
        return 0
    fi
    
    log_info "🐳 Setting up Docker environment..."
    
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        case "$OS_TYPE" in
            "linux")
                curl -fsSL https://get.docker.com | sh
                sudo usermod -aG docker $USER
                log_warn "Please log out and back in to use Docker without sudo"
                ;;
            "macos")
                log_info "Please install Docker Desktop for macOS from https://docker.com/products/docker-desktop"
                ;;
            "windows")
                eval "$INSTALL_CMD docker-desktop"
                ;;
        esac
    fi
    
    # Start Docker service on Linux
    if [[ "$OS_TYPE" == "linux" ]]; then
        sudo systemctl enable docker
        sudo systemctl start docker
    fi
    
    log_success "Docker environment ready"
}

# Kubernetes setup
setup_kubernetes() {
    if [[ "$INSTALL_KUBERNETES" != true ]]; then
        return 0
    fi
    
    log_info "☸️ Setting up Kubernetes tools..."
    
    # Install kubectl
    if ! command -v kubectl &> /dev/null; then
        log_info "Installing kubectl..."
        case "$OS_TYPE" in
            "linux")
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
                rm kubectl
                ;;
            "macos")
                eval "$INSTALL_CMD kubectl"
                ;;
            "windows")
                eval "$INSTALL_CMD kubernetes-cli"
                ;;
        esac
    fi
    
    # Install kind for local clusters
    if ! command -v kind &> /dev/null; then
        log_info "Installing kind..."
        case "$OS_TYPE" in
            "linux"|"macos")
                curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
                chmod +x ./kind
                sudo mv ./kind /usr/local/bin/kind
                ;;
            "windows")
                eval "$INSTALL_CMD kind"
                ;;
        esac
    fi
    
    log_success "Kubernetes tools ready"
}

# Backend setup
setup_backend() {
    if [[ "$INSTALL_BACKEND" != true ]]; then
        return 0
    fi
    
    log_info "🏗️ Setting up Backend components..."
    
    cd "${SCRIPT_DIR}/BACKEND"
    
    # Build Nexus Prime Core (Rust)
    if [[ -d "nexus-prime-core" ]]; then
        log_info "Building Nexus Prime Core..."
        cd nexus-prime-core
        cargo build --release
        cd ..
    fi
    
    # Build Go Node Proxies
    if [[ -d "go-node-proxies" ]]; then
        log_info "Building Go Node Proxies..."
        cd go-node-proxies
        go mod tidy
        go build -o bin/node-proxy
        cd ..
    fi
    
    cd "${SCRIPT_DIR}"
    log_success "Backend components built"
}

# Frontend setup
setup_frontend() {
    if [[ "$INSTALL_FRONTEND" != true ]]; then
        return 0
    fi
    
    log_info "🎨 Setting up Frontend components..."
    
    # Setup SolidJS Control Panel
    if [[ -d "FRONTEND/ui-solidjs" ]]; then
        cd "FRONTEND/ui-solidjs"
        log_info "Installing SolidJS Control Panel dependencies..."
        pnpm install
        log_info "Building production frontend..."
        pnpm run build
        cd "${SCRIPT_DIR}"
    fi
    
    log_success "Frontend components ready"
}

# Control Center setup
setup_control_center() {
    if [[ "$INSTALL_CONTROL_CENTER" != true ]]; then
        return 0
    fi
    
    log_info "🎮 Setting up Control Center..."
    
    # Make all Python scripts executable
    chmod +x omni_*.py
    chmod +x omni-*.py
    chmod +x quick-start.sh
    
    # Make C2 Center executable
    chmod +x omni-c2-center.py
    
    # Install additional C2 Center dependencies
    log_info "Installing C2 Center dependencies..."
    pip install gitpython pyyaml psutil requests
    
    # Create desktop shortcuts (Linux/macOS)
    if [[ "$OS_TYPE" != "windows" ]]; then
        create_desktop_shortcuts
    fi
    
    log_success "Control Center ready"
}

# Create desktop shortcuts
create_desktop_shortcuts() {
    local desktop_dir=""
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        desktop_dir="$HOME/Desktop"
        mkdir -p "$desktop_dir"
        
        cat > "$desktop_dir/OMNIMESH.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=OMNIMESH Control Center
Comment=Next-Generation AI Orchestration Platform
Exec=$SCRIPT_DIR/quick-start.sh
Icon=$SCRIPT_DIR/assets/omnimesh-icon.png
Terminal=true
Categories=Development;System;
EOF
        chmod +x "$desktop_dir/OMNIMESH.desktop"
    fi
}

# Configuration setup
setup_configuration() {
    log_info "⚙️ Setting up configuration..."
    
    # Create configuration if it doesn't exist
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_info "Creating default configuration..."
        create_default_config
    fi
    
    # Set up environment variables
    cat > .env << EOF
# OMNIMESH Environment Configuration
OMNIMESH_HOME=${SCRIPT_DIR}
OMNIMESH_ENV=${DEVELOPMENT_MODE:+development}${PRODUCTION_MODE:+production}
OMNIMESH_LOG_LEVEL=info
OMNIMESH_CONFIG_FILE=${CONFIG_FILE}

# Backend Configuration
NEXUS_CORE_HOST=localhost
NEXUS_CORE_PORT=50053
NODE_PROXY_PORT=9090

# Frontend Configuration
FRONTEND_PORT=5173
BACKEND_API_URL=http://localhost:8080

# AI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY:-}
AI_ENABLED=${INSTALL_AI}

# Docker Configuration
DOCKER_ENABLED=${INSTALL_DOCKER}
KUBERNETES_ENABLED=${INSTALL_KUBERNETES}
EOF
    
    log_success "Configuration setup complete"
}

# Create default configuration
create_default_config() {
    cat > "$CONFIG_FILE" << 'EOF'
# OMNIMESH Default Configuration
environment:
  current: "development"
  available: ["development", "staging", "production"]

services:
  nexus_core:
    image: "nexus-prime-core:latest"
    ports: [8080, 8443, 50053]
    health_check: "/health"
  
  go_proxies:
    image: "go-node-proxies:latest"
    ports: [9090, 9443]
    replicas: 3

  frontend:
    image: "omnimesh-frontend:latest"
    ports: [5173, 4173]
    build_command: "pnpm run build"

ai:
  provider: "openai"
  model: "gpt-4"
  features:
    - "natural_language_commands"
    - "predictive_scaling"
    - "anomaly_detection"
  enabled: false

monitoring:
  prometheus:
    enabled: true
    port: 9090
  grafana:
    enabled: true
    port: 3000
  jaeger:
    enabled: true
    port: 16686

security:
  tls_enabled: true
  certificate_path: "/etc/ssl/certs/omnimesh"
  secret_encryption: "aes-256-gcm"
  tiger_lily_enforcement: true

logging:
  level: "info"
  format: "json"
  file: "omnimesh.log"
EOF
}

# Service management
setup_services() {
    log_info "🔧 Setting up system services..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        # Create systemd service for OMNIMESH
        cat > /tmp/omnimesh.service << EOF
[Unit]
Description=OMNIMESH Control Center
After=network.target
Wants=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/quick-start.sh orchestrator
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        if [[ "$PRODUCTION_MODE" == true ]]; then
            sudo mv /tmp/omnimesh.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable omnimesh
            log_success "OMNIMESH service installed and enabled"
        fi
    fi
}

# Health check
run_health_check() {
    log_info "🩺 Running system health check..."
    
    local health_status=0
    
    # Check Python environment
    if source venv/bin/activate 2>/dev/null && python -c "import textual, rich, pydantic" 2>/dev/null; then
        log_success "✅ Python environment healthy"
    else
        log_error "❌ Python environment issues detected"
        health_status=1
    fi
    
    # Check Node.js environment
    if [[ "$INSTALL_FRONTEND" == true ]]; then
        if command -v node &> /dev/null && command -v pnpm &> /dev/null; then
            log_success "✅ Node.js environment healthy"
        else
            log_error "❌ Node.js environment issues detected"
            health_status=1
        fi
    fi
    
    # Check Rust environment
    if [[ "$INSTALL_BACKEND" == true ]]; then
        if command -v cargo &> /dev/null; then
            log_success "✅ Rust environment healthy"
        else
            log_error "❌ Rust environment issues detected"
            health_status=1
        fi
    fi
    
    # Check Docker
    if [[ "$INSTALL_DOCKER" == true ]]; then
        if command -v docker &> /dev/null && docker info &> /dev/null; then
            log_success "✅ Docker environment healthy"
        else
            log_warn "⚠️ Docker environment needs attention"
        fi
    fi
    
    return $health_status
}

# Interactive installation wizard
interactive_wizard() {
    echo -e "${CYAN}🧙 Installation Wizard${NC}"
    echo
    
    # Installation type
    echo -e "${BOLD}Select installation type:${NC}"
    echo "1) 🖥️  Development (Full stack for developers)"
    echo "2) 🎮 User (Control Center + Frontend only)"
    echo "3) 🏭 Production (All components + services)"
    echo "4) 🎯 Custom (Choose components)"
    read -p "Choice [1]: " install_type
    install_type=${install_type:-1}
    
    case $install_type in
        1) # Development
            DEVELOPMENT_MODE=true
            INSTALL_DOCKER=true
            ;;
        2) # User
            INSTALL_BACKEND=false
            INSTALL_INFRASTRUCTURE=false
            ;;
        3) # Production
            PRODUCTION_MODE=true
            INSTALL_KUBERNETES=true
            INSTALL_DOCKER=true
            ;;
        4) # Custom
            echo
            read -p "Install Backend? [Y/n]: " choice
            [[ "$choice" != "n" && "$choice" != "N" ]] || INSTALL_BACKEND=false
            
            read -p "Install Frontend? [Y/n]: " choice
            [[ "$choice" != "n" && "$choice" != "N" ]] || INSTALL_FRONTEND=false
            
            read -p "Install Docker? [Y/n]: " choice
            [[ "$choice" != "n" && "$choice" != "N" ]] || INSTALL_DOCKER=false
            
            read -p "Install Kubernetes tools? [y/N]: " choice
            [[ "$choice" == "y" || "$choice" == "Y" ]] && INSTALL_KUBERNETES=true
            
            read -p "Enable AI features? [y/N]: " choice
            [[ "$choice" == "y" || "$choice" == "Y" ]] && INSTALL_AI=true
            ;;
    esac
    
    # AI configuration
    if [[ "$INSTALL_AI" == true ]]; then
        echo
        echo -e "${YELLOW}AI features require an OpenAI API key.${NC}"
        read -s -p "Enter OpenAI API key (optional): " OPENAI_API_KEY
        echo
        export OPENAI_API_KEY
    fi
    
    echo
    echo -e "${GREEN}Installation configuration complete!${NC}"
    echo
}

# Command line argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev|--development)
                DEVELOPMENT_MODE=true
                INSTALL_DOCKER=true
                ;;
            --prod|--production)
                PRODUCTION_MODE=true
                INSTALL_KUBERNETES=true
                INSTALL_DOCKER=true
                ;;
            --no-backend)
                INSTALL_BACKEND=false
                ;;
            --no-frontend)
                INSTALL_FRONTEND=false
                ;;
            --no-docker)
                INSTALL_DOCKER=false
                ;;
            --kubernetes)
                INSTALL_KUBERNETES=true
                ;;
            --ai)
                INSTALL_AI=true
                ;;
            --openai-key)
                OPENAI_API_KEY="$2"
                INSTALL_AI=true
                shift
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
}

# Help message
show_help() {
    echo -e "${BOLD}OMNIMESH Universal Installer${NC}"
    echo
    echo -e "${CYAN}USAGE:${NC}"
    echo "  $0 [OPTIONS]"
    echo
    echo -e "${CYAN}OPTIONS:${NC}"
    echo "  --dev, --development     Install development environment"
    echo "  --prod, --production     Install production environment"
    echo "  --no-backend            Skip backend installation"
    echo "  --no-frontend           Skip frontend installation"
    echo "  --no-docker             Skip Docker installation"
    echo "  --kubernetes            Install Kubernetes tools"
    echo "  --ai                    Enable AI features"
    echo "  --openai-key KEY        Set OpenAI API key"
    echo "  --non-interactive       Run without prompts"
    echo "  --help, -h              Show this help message"
    echo
    echo -e "${CYAN}EXAMPLES:${NC}"
    echo "  $0                      # Interactive installation"
    echo "  $0 --dev              # Development setup"
    echo "  $0 --prod --ai        # Production with AI"
    echo "  $0 --no-backend       # Frontend only"
}

# Post-installation summary and next steps
show_summary() {
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                        🎉 INSTALLATION COMPLETE!                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BOLD}📋 Installation Summary:${NC}"
    echo -e "  📅 Installation ID: ${INSTALL_TIMESTAMP}"
    echo -e "  📂 Installation Path: ${SCRIPT_DIR}"
    echo -e "  📋 Log File: ${LOG_FILE}"
    echo
    echo -e "${BOLD}🚀 Quick Start Commands:${NC}"
    echo -e "  ${CYAN}# Launch Control Center${NC}"
    echo -e "  ./quick-start.sh"
    echo
    echo -e "  ${CYAN}# Launch Web Interface${NC}"
    echo -e "  ./quick-start.sh web"
    echo
    echo -e "  ${CYAN}# Launch Ultimate System${NC}"
    echo -e "  ./quick-start.sh ultimate"
    echo
    if [[ "$INSTALL_BACKEND" == true ]]; then
        echo -e "${BOLD}🏗️ Backend Services:${NC}"
        echo -e "  ${CYAN}# Start Nexus Prime Core${NC}"
        echo -e "  cd BACKEND/nexus-prime-core && cargo run --release"
        echo
        echo -e "  ${CYAN}# Start Node Proxies${NC}"
        echo -e "  cd BACKEND/go-node-proxies && ./bin/node-proxy"
        echo
    fi
    if [[ "$INSTALL_FRONTEND" == true ]]; then
        echo -e "${BOLD}🎨 Frontend Development:${NC}"
        echo -e "  ${CYAN}# Start Development Server${NC}"
        echo -e "  cd FRONTEND/ui-solidjs && pnpm run dev"
        echo
    fi
    echo -e "${BOLD}📚 Documentation:${NC}"
    echo -e "  • User Guide: ${SCRIPT_DIR}/USER_GUIDE.md"
    echo -e "  • System Status: ${SCRIPT_DIR}/SYSTEM_STATUS_ULTIMATE.md"
    echo -e "  • Security Guide: ${SCRIPT_DIR}/SECURITY_FRAMEWORK.md"
    echo
    echo -e "${YELLOW}⚠️ Important Notes:${NC}"
    if [[ "$INSTALL_DOCKER" == true && "$OS_TYPE" == "linux" ]]; then
        echo -e "  • Please log out and back in to use Docker without sudo"
    fi
    if [[ "$INSTALL_AI" == true && -z "$OPENAI_API_KEY" ]]; then
        echo -e "  • Set OPENAI_API_KEY environment variable to enable AI features"
    fi
    echo -e "  • Run './quick-start.sh --help' for all available options"
    echo
    echo -e "${PURPLE}🌊 Welcome to the OMNIMESH ecosystem! 🌊${NC}"
}

# Main installation flow
main() {
    # Initialize
    show_banner
    log_info "Starting OMNIMESH installation..."
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Run interactive wizard if not in non-interactive mode
    if [[ "${NON_INTERACTIVE:-false}" != true ]]; then
        interactive_wizard
    fi
    
    # System setup
    detect_system
    setup_package_manager
    
    # Language environments
    setup_python
    [[ "$INSTALL_FRONTEND" == true ]] && setup_nodejs
    [[ "$INSTALL_BACKEND" == true ]] && setup_rust
    [[ "$INSTALL_BACKEND" == true ]] && setup_go
    
    # Infrastructure
    setup_docker
    setup_kubernetes
    
    # OMNIMESH components
    setup_backend
    setup_frontend
    setup_control_center
    
    # Configuration and services
    setup_configuration
    [[ "$PRODUCTION_MODE" == true ]] && setup_services
    
    # Final checks
    if run_health_check; then
        log_success "All health checks passed!"
    else
        log_warn "Some health checks failed, but installation completed"
    fi
    
    # Show summary
    show_summary
    
    log_success "OMNIMESH installation completed successfully!"
}

# Trap for cleanup
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
