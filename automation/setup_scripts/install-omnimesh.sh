#!/bin/bash

# 🌊 OMNIMESH Universal Orchestrator & Natural Language CLI
# Intelligent conversational interface for the complete OMNIMESH ecosystem
# "Just tell me what you want, and I'll make it happen" - Architect's Absolute Dominion

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
INTERACTIVE_MODE=false
COMMAND_MODE=""

# Natural Language Processing flags
NLP_ENABLED=true
AUTO_PERMISSIONS=true
AUTO_SYMLINKS=true
AUTO_CONFIG=true

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
    
    # Configure frontend-backend connections
    log_info "🔗 Configuring frontend-backend connections..."
    
    if [[ -f "FRONTEND/ui-solidjs/.env.example" ]]; then
        # Copy environment template and configure endpoints
        cp "FRONTEND/ui-solidjs/.env.example" "FRONTEND/ui-solidjs/.env"
        
        # Update environment with detected endpoints
        if [[ -f "FRONTEND/ui-solidjs/.env" ]]; then
            sed -i 's|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://localhost:8080|' "FRONTEND/ui-solidjs/.env"
            sed -i 's|VITE_GRPC_ENDPOINT=.*|VITE_GRPC_ENDPOINT=http://localhost:50052|' "FRONTEND/ui-solidjs/.env"
            sed -i 's|VITE_NEXUS_CORE_URL=.*|VITE_NEXUS_CORE_URL=http://localhost:50053|' "FRONTEND/ui-solidjs/.env"
            log_success "Frontend environment configured with backend endpoints"
        fi
    fi
    
    # Verify control center dependencies
    if [[ "$PYTHON_CMD" ]]; then
        log_info "Installing C2 Center dependencies..."
        $PYTHON_CMD -m pip install textual rich gitpython pyyaml psutil requests
    fi
    
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

# 🧠 NATURAL LANGUAGE PROCESSING ENGINE
process_natural_language() {
    local input="$1"
    local input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    
    log_info "🧠 Processing: '$input'"
    
    # File Operations
    if [[ "$input_lower" =~ (make.*executable|chmod.*x|fix.*permissions?) ]]; then
        handle_make_executable "$input"
    elif [[ "$input_lower" =~ (create.*symlink|link.*to|symlink.*from) ]]; then
        handle_create_symlink "$input"
    elif [[ "$input_lower" =~ (create.*file|make.*file|new.*file) ]]; then
        handle_create_file "$input"
    elif [[ "$input_lower" =~ (edit.*file|open.*file|nano|vim) ]]; then
        handle_edit_file "$input"
        
    # Build Operations
    elif [[ "$input_lower" =~ (build|compile|make) ]]; then
        handle_build_operations "$input"
    elif [[ "$input_lower" =~ (install.*dependen|setup.*dependen|get.*dependen) ]]; then
        handle_install_dependencies "$input"
        
    # Server Operations  
    elif [[ "$input_lower" =~ (start.*server|run.*server|launch.*server) ]]; then
        handle_start_servers "$input"
    elif [[ "$input_lower" =~ (stop.*server|kill.*server|shutdown) ]]; then
        handle_stop_servers "$input"
        
    # System Operations
    elif [[ "$input_lower" =~ (status|health|check) ]]; then
        handle_system_status "$input"
    elif [[ "$input_lower" =~ (clean|cleanup|remove.*build) ]]; then
        handle_cleanup_operations "$input"
    elif [[ "$input_lower" =~ (deploy|publish|release) ]]; then
        handle_deployment_operations "$input"
        
    # Configuration
    elif [[ "$input_lower" =~ (config|configure|setup|initialize) ]]; then
        handle_configuration_operations "$input"
        
    # Help and Examples
    elif [[ "$input_lower" =~ (help|examples|how.*to) ]]; then
        handle_help_request "$input"
        
    else
        echo -e "${YELLOW}🤔 I'm not sure how to: '$input'${NC}"
        echo -e "${CYAN}💡 Try something like:${NC}"
        echo "  • 'make all files executable'"
        echo "  • 'create symlink from X to Y'"
        echo "  • 'build everything'"
        echo "  • 'start all servers'"
        echo "  • 'check system status'"
        echo
        echo -e "Or type '${BOLD}help examples${NC}' for more ideas!"
    fi
}

# 📁 FILE OPERATIONS HANDLERS
handle_make_executable() {
    local input="$1"
    
    echo -e "${GREEN}🔧 Making files executable...${NC}"
    
    # Smart detection of what to make executable
    if [[ "$input" =~ (all|everything) ]]; then
        find . -name "*.sh" -type f -exec chmod +x {} \;
        find . -name "*.py" -type f -exec chmod +x {} \;
        find . -name "omni*" -type f -exec chmod +x {} \;
        echo -e "✅ Made all scripts executable"
    elif [[ "$input" =~ python|py ]]; then
        find . -name "*.py" -type f -exec chmod +x {} \;
        echo -e "✅ Made all Python files executable"
    elif [[ "$input" =~ bash|shell|sh ]]; then
        find . -name "*.sh" -type f -exec chmod +x {} \;
        echo -e "✅ Made all shell scripts executable"
    else
        # Extract filename if mentioned
        local filename=$(echo "$input" | grep -oP '(?<=(make|file) )[^ ]+' | head -1)
        if [[ -n "$filename" && -f "$filename" ]]; then
            chmod +x "$filename"
            echo -e "✅ Made $filename executable"
        else
            # Default: make common files executable
            chmod +x *.sh *.py omni* 2>/dev/null
            echo -e "✅ Made common scripts executable"
        fi
    fi
}

handle_create_symlink() {
    local input="$1"
    
    echo -e "${GREEN}🔗 Creating symlink...${NC}"
    
    # Parse "create symlink from X to Y" or "link X to Y"
    local source target
    
    if [[ "$input" =~ from[[:space:]]+([^[:space:]]+)[[:space:]]+to[[:space:]]+([^[:space:]]+) ]]; then
        source="${BASH_REMATCH[1]}"
        target="${BASH_REMATCH[2]}"
    elif [[ "$input" =~ link[[:space:]]+([^[:space:]]+)[[:space:]]+to[[:space:]]+([^[:space:]]+) ]]; then
        source="${BASH_REMATCH[1]}"
        target="${BASH_REMATCH[2]}"
    elif [[ "$input" =~ symlink[[:space:]]+([^[:space:]]+)[[:space:]]+([^[:space:]]+) ]]; then
        source="${BASH_REMATCH[1]}"
        target="${BASH_REMATCH[2]}"
    else
        # Interactive prompting
        read -p "Source file/directory: " source
        read -p "Target location: " target
    fi
    
    if [[ -n "$source" && -n "$target" ]]; then
        # Make target directory if needed
        mkdir -p "$(dirname "$target")"
        
        # Create symlink
        if ln -sf "$(realpath "$source")" "$target"; then
            echo -e "✅ Created symlink: $target → $source"
        else
            echo -e "❌ Failed to create symlink"
        fi
    else
        echo -e "${YELLOW}❓ Please specify source and target${NC}"
        echo -e "Example: 'create symlink from omni-launcher.py to /usr/local/bin/omni'"
    fi
}

handle_create_file() {
    local input="$1"
    
    # Extract filename
    local filename=$(echo "$input" | grep -oP '(?<=(create|make|new) (file )?)[^ ]+' | head -1)
    
    if [[ -z "$filename" ]]; then
        read -p "Filename: " filename
    fi
    
    if [[ -n "$filename" ]]; then
        # Create directory if needed
        mkdir -p "$(dirname "$filename")"
        
        # Create file with appropriate template
        if [[ "$filename" =~ \.py$ ]]; then
            cat > "$filename" << 'EOF'
#!/usr/bin/env python3
"""
OMNIMESH Component
"""

def main():
    print("Hello from OMNIMESH!")

if __name__ == "__main__":
    main()
EOF
            chmod +x "$filename"
            echo -e "✅ Created Python file: $filename"
        elif [[ "$filename" =~ \.sh$ ]]; then
            cat > "$filename" << 'EOF'
#!/bin/bash
# OMNIMESH Script

set -euo pipefail

echo "Hello from OMNIMESH!"
EOF
            chmod +x "$filename"
            echo -e "✅ Created shell script: $filename"
        else
            touch "$filename"
            echo -e "✅ Created file: $filename"
        fi
        
        # Offer to edit
        read -p "Edit now? (y/N): " edit_choice
        if [[ "$edit_choice" =~ ^[Yy] ]]; then
            handle_edit_file "edit $filename"
        fi
    fi
}

handle_edit_file() {
    local input="$1"
    
    # Extract filename
    local filename=$(echo "$input" | grep -oP '(?<=(edit|open) )[^ ]+' | head -1)
    
    if [[ -z "$filename" ]]; then
        read -p "File to edit: " filename
    fi
    
    if [[ -f "$filename" ]]; then
        # Use best available editor
        if command -v code &> /dev/null; then
            code "$filename"
            echo -e "✅ Opened $filename in VS Code"
        elif command -v nano &> /dev/null; then
            nano "$filename"
        elif command -v vim &> /dev/null; then
            vim "$filename"
        else
            echo -e "${YELLOW}No editor found. Install VS Code, nano, or vim${NC}"
        fi
    else
        echo -e "${YELLOW}File not found: $filename${NC}"
        read -p "Create it? (y/N): " create_choice
        if [[ "$create_choice" =~ ^[Yy] ]]; then
            handle_create_file "create file $filename"
        fi
    fi
}

# 🏗️ BUILD OPERATIONS HANDLERS
handle_build_operations() {
    local input="$1"
    
    echo -e "${GREEN}🏗️ Building components...${NC}"
    
    if [[ "$input" =~ (everything|all) ]]; then
        echo -e "🔄 Building all components..."
        build_all_components
    elif [[ "$input" =~ (backend|rust|cargo) ]]; then
        echo -e "🦀 Building Rust backend..."
        build_backend_components
    elif [[ "$input" =~ (frontend|solidjs|ui) ]]; then
        echo -e "🎨 Building SolidJS frontend..."
        build_frontend_components
    elif [[ "$input" =~ (go|golang|proxy) ]]; then
        echo -e "🐹 Building Go components..."
        build_go_components
    else
        echo -e "🔄 Building detected components..."
        auto_detect_and_build
    fi
}

build_all_components() {
    local build_status=0
    
    # Ensure all dependencies are installed first
    detect_system
    setup_package_manager
    setup_python
    [[ "$INSTALL_FRONTEND" == true ]] && setup_nodejs
    [[ "$INSTALL_BACKEND" == true ]] && setup_rust
    [[ "$INSTALL_BACKEND" == true ]] && setup_go
    
    # Frontend
    if [[ -d "FRONTEND/ui-solidjs" ]]; then
        echo -e "📦 Building SolidJS frontend..."
        cd "FRONTEND/ui-solidjs"
        if pnpm install && pnpm run build; then
            echo -e "✅ Frontend built successfully"
        else
            echo -e "❌ Frontend build failed"
            build_status=1
        fi
        cd "$SCRIPT_DIR"
    fi
    
    # Backend Rust
    if [[ -d "BACKEND/nexus-prime-core" ]]; then
        echo -e "🦀 Building Rust backend..."
        cd "BACKEND/nexus-prime-core"
        if cargo build --release; then
            echo -e "✅ Rust backend built successfully"
        else
            echo -e "❌ Rust backend build failed"
            build_status=1
        fi
        cd "$SCRIPT_DIR"
    fi
    
    # Go Proxies
    if [[ -d "BACKEND/go-node-proxies" ]]; then
        echo -e "🐹 Building Go proxies..."
        cd "BACKEND/go-node-proxies"
        if go mod tidy && go build -o bin/proxy; then
            echo -e "✅ Go proxies built successfully"
        else
            echo -e "❌ Go proxies build failed"
            build_status=1
        fi
        cd "$SCRIPT_DIR"
    fi
    
    # Python dependencies
    echo -e "🐍 Installing Python dependencies..."
    if source venv/bin/activate && pip install -r requirements.txt; then
        echo -e "✅ Python dependencies installed"
    else
        echo -e "❌ Python dependencies failed"
        build_status=1
    fi
    
    # Make all scripts executable
    find . -name "*.py" -type f -exec chmod +x {} \;
    find . -name "*.sh" -type f -exec chmod +x {} \;
    
    if [[ $build_status -eq 0 ]]; then
        echo -e "${GREEN}🎉 All components built successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️ Some builds failed. Check logs above.${NC}"
    fi
}

build_backend_components() {
    echo -e "🦀 Building Rust backend components..."
    
    if [[ -d "BACKEND/nexus-prime-core" ]]; then
        cd "BACKEND/nexus-prime-core"
        cargo build --release
        cd "$SCRIPT_DIR"
    fi
    
    if [[ -d "BACKEND/go-node-proxies" ]]; then
        cd "BACKEND/go-node-proxies"
        go mod tidy && go build -o bin/proxy
        cd "$SCRIPT_DIR"
    fi
}

build_frontend_components() {
    echo -e "🎨 Building SolidJS frontend..."
    
    if [[ -d "FRONTEND/ui-solidjs" ]]; then
        cd "FRONTEND/ui-solidjs"
        pnpm install && pnpm run build
        cd "$SCRIPT_DIR"
    fi
}

build_go_components() {
    echo -e "🐹 Building Go components..."
    
    if [[ -d "BACKEND/go-node-proxies" ]]; then
        cd "BACKEND/go-node-proxies"
        go mod tidy && go build -o bin/proxy
        cd "$SCRIPT_DIR"
    fi
}

# 🚀 SERVER OPERATIONS HANDLERS
handle_start_servers() {
    local input="$1"
    
    echo -e "${GREEN}🚀 Starting servers...${NC}"
    
    if [[ "$input" =~ (all|everything) ]]; then
        start_all_servers
    elif [[ "$input" =~ (frontend|ui|web) ]]; then
        start_frontend_server
    elif [[ "$input" =~ (backend|api|rust) ]]; then
        start_backend_server
    elif [[ "$input" =~ (control|c2|center) ]]; then
        start_control_center
    else
        # Interactive selection
        echo "Which servers would you like to start?"
        echo "1) All servers"
        echo "2) Frontend only"
        echo "3) Backend only"
        echo "4) Control Center"
        read -p "Choice [1]: " choice
        choice=${choice:-1}
        
        case $choice in
            1) start_all_servers ;;
            2) start_frontend_server ;;
            3) start_backend_server ;;
            4) start_control_center ;;
        esac
    fi
}

start_all_servers() {
    echo -e "🔄 Starting all OMNIMESH servers..."
    
    # Kill existing processes
    pkill -f "nexus-prime-core" 2>/dev/null || true
    pkill -f "pnpm.*dev" 2>/dev/null || true
    pkill -f "omni-c2-center" 2>/dev/null || true
    
    # Start backend in background
    if [[ -f "BACKEND/nexus-prime-core/target/release/nexus-prime-core" ]]; then
        echo -e "🦀 Starting Rust backend..."
        cd "BACKEND/nexus-prime-core"
        nohup ./target/release/nexus-prime-core > "$SCRIPT_DIR/backend.log" 2>&1 &
        echo $! > "$SCRIPT_DIR/backend.pid"
        cd "$SCRIPT_DIR"
        echo -e "✅ Backend started (PID: $(cat backend.pid))"
    fi
    
    # Start frontend dev server
    if [[ -d "FRONTEND/ui-solidjs" ]]; then
        echo -e "🎨 Starting frontend dev server..."
        cd "FRONTEND/ui-solidjs"
        nohup pnpm run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
        echo $! > "$SCRIPT_DIR/frontend.pid"
        cd "$SCRIPT_DIR"
        echo -e "✅ Frontend started (PID: $(cat frontend.pid))"
    fi
    
    # Start control center
    echo -e "🎮 Starting Control Center..."
    source venv/bin/activate
    nohup python omni-c2-center.py > "$SCRIPT_DIR/c2center.log" 2>&1 &
    echo $! > "$SCRIPT_DIR/c2center.pid"
    echo -e "✅ Control Center started (PID: $(cat c2center.pid))"
    
    echo -e "${GREEN}🎉 All servers started successfully!${NC}"
    echo -e "${CYAN}Logs: backend.log, frontend.log, c2center.log${NC}"
    echo -e "${CYAN}Use 'check status' to see running services${NC}"
}

start_frontend_server() {
    if [[ -d "FRONTEND/ui-solidjs" ]]; then
        echo -e "🎨 Starting SolidJS frontend..."
        cd "FRONTEND/ui-solidjs"
        pnpm run dev
        cd "$SCRIPT_DIR"
    else
        echo -e "${YELLOW}Frontend directory not found${NC}"
    fi
}

start_backend_server() {
    if [[ -f "BACKEND/nexus-prime-core/target/release/nexus-prime-core" ]]; then
        echo -e "🦀 Starting Rust backend..."
        cd "BACKEND/nexus-prime-core"
        ./target/release/nexus-prime-core
        cd "$SCRIPT_DIR"
    else
        echo -e "${YELLOW}Backend not built. Try 'build backend' first${NC}"
    fi
}

start_control_center() {
    echo -e "🎮 Starting OMNIMESH Control Center..."
    source venv/bin/activate
    python omni-c2-center.py
}

handle_stop_servers() {
    local input="$1"
    
    echo -e "${GREEN}🛑 Stopping servers...${NC}"
    
    # Stop all servers
    if [[ -f "backend.pid" ]]; then
        kill "$(cat backend.pid)" 2>/dev/null && echo -e "✅ Backend stopped" || echo -e "⚠️ Backend already stopped"
        rm -f backend.pid
    fi
    
    if [[ -f "frontend.pid" ]]; then
        kill "$(cat frontend.pid)" 2>/dev/null && echo -e "✅ Frontend stopped" || echo -e "⚠️ Frontend already stopped"
        rm -f frontend.pid
    fi
    
    if [[ -f "c2center.pid" ]]; then
        kill "$(cat c2center.pid)" 2>/dev/null && echo -e "✅ Control Center stopped" || echo -e "⚠️ Control Center already stopped"
        rm -f c2center.pid
    fi
    
    # Kill any remaining processes
    pkill -f "nexus-prime-core" 2>/dev/null || true
    pkill -f "pnpm.*dev" 2>/dev/null || true
    pkill -f "omni-c2-center" 2>/dev/null || true
    
    echo -e "✅ All servers stopped"
}

# 📊 STATUS AND HEALTH HANDLERS
handle_system_status() {
    local input="$1"
    
    if [[ "$input" =~ (detailed|comprehensive|full) ]]; then
        run_comprehensive_health_check
    else
        run_quick_health_check
    fi
    
    # Show running processes
    echo
    echo -e "${BOLD}🔄 Running Services:${NC}"
    
    if [[ -f "backend.pid" ]] && kill -0 "$(cat backend.pid)" 2>/dev/null; then
        echo -e "✅ Backend (PID: $(cat backend.pid))"
    else
        echo -e "❌ Backend not running"
    fi
    
    if [[ -f "frontend.pid" ]] && kill -0 "$(cat frontend.pid)" 2>/dev/null; then
        echo -e "✅ Frontend (PID: $(cat frontend.pid))"
    else
        echo -e "❌ Frontend not running"
    fi
    
    if [[ -f "c2center.pid" ]] && kill -0 "$(cat c2center.pid)" 2>/dev/null; then
        echo -e "✅ Control Center (PID: $(cat c2center.pid))"
    else
        echo -e "❌ Control Center not running"
    fi
    
    echo
    echo -e "${BOLD}🌐 Network Endpoints:${NC}"
    echo -e "Frontend: http://localhost:5173"
    echo -e "Backend API: http://localhost:8080"
    echo -e "Nexus Core: http://localhost:50053"
}

# 🧹 CLEANUP OPERATIONS
handle_cleanup_operations() {
    local input="$1"
    
    echo -e "${GREEN}🧹 Cleaning up...${NC}"
    
    if [[ "$input" =~ (everything|all) ]]; then
        echo -e "🔄 Full cleanup..."
        # Build artifacts
        find . -name "target" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        rm -f *.log *.pid 2>/dev/null || true
        echo -e "✅ Cleaned all build artifacts"
    elif [[ "$input" =~ (rust|cargo|backend) ]]; then
        find . -name "target" -type d -exec rm -rf {} + 2>/dev/null || true
        echo -e "✅ Cleaned Rust build artifacts"
    elif [[ "$input" =~ (node|frontend|npm) ]]; then
        find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
        echo -e "✅ Cleaned Node.js build artifacts"
    elif [[ "$input" =~ (python|py) ]]; then
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        echo -e "✅ Cleaned Python cache files"
    fi
}

# 🚚 DEPLOYMENT HANDLERS  
handle_deployment_operations() {
    local input="$1"
    
    echo -e "${GREEN}🚚 Deployment operations...${NC}"
    
    if [[ "$input" =~ (production|prod) ]]; then
        deploy_production
    elif [[ "$input" =~ (docker|container) ]]; then
        deploy_with_docker
    elif [[ "$input" =~ (kubernetes|k8s) ]]; then
        deploy_with_kubernetes
    else
        echo "Select deployment target:"
        echo "1) Production environment"
        echo "2) Docker containers"
        echo "3) Kubernetes cluster"
        read -p "Choice: " choice
        
        case $choice in
            1) deploy_production ;;
            2) deploy_with_docker ;;
            3) deploy_with_kubernetes ;;
        esac
    fi
}

deploy_production() {
    echo -e "🏭 Deploying to production..."
    
    # Build everything first
    echo -e "📦 Building for production..."
    build_all_components
    
    # Create production config
    cat > .env.production << EOF
NODE_ENV=production
OMNIMESH_ENV=production
RUST_LOG=info
DATABASE_URL=postgresql://omnimesh:secure@localhost/omnimesh_prod
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=$(openssl rand -base64 32)
API_PORT=8080
FRONTEND_PORT=80
EOF
    
    echo -e "✅ Production deployment configured"
    echo -e "${CYAN}Next steps: Configure your production server and deploy the built artifacts${NC}"
}

deploy_with_docker() {
    echo -e "🐳 Deploying with Docker..."
    
    # Create comprehensive Dockerfile
    cat > Dockerfile << 'EOF'
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY FRONTEND/ui-solidjs/package*.json ./
RUN npm install
COPY FRONTEND/ui-solidjs ./
RUN npm run build

FROM rust:1.75 AS backend-build
WORKDIR /app/backend
COPY BACKEND/nexus-prime-core/Cargo.toml BACKEND/nexus-prime-core/Cargo.lock ./
RUN cargo fetch
COPY BACKEND/nexus-prime-core/src ./src
RUN cargo build --release

FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built artifacts
COPY --from=frontend-build /app/frontend/dist ./static
COPY --from=backend-build /app/backend/target/release/nexus-prime-core ./bin/
COPY . .

# Make scripts executable
RUN chmod +x *.py *.sh

EXPOSE 8080 5173 50053

CMD ["python", "omni_ultimate_system.py"]
EOF
    
    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  omnimesh:
    build: .
    ports:
      - "8080:8080"
      - "5173:5173"
      - "50053:50053"
    environment:
      - OMNIMESH_ENV=production
      - RUST_LOG=info
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: omnimesh
      POSTGRES_USER: omnimesh
      POSTGRES_PASSWORD: secure
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
EOF
    
    echo -e "✅ Docker configuration created"
    echo -e "${CYAN}Run: docker-compose up -d${NC}"
}

deploy_with_kubernetes() {
    echo -e "☸️ Deploying with Kubernetes..."
    
    mkdir -p k8s
    
    # Create Kubernetes deployment
    cat > k8s/omnimesh-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: omnimesh
  labels:
    app: omnimesh
spec:
  replicas: 3
  selector:
    matchLabels:
      app: omnimesh
  template:
    metadata:
      labels:
        app: omnimesh
    spec:
      containers:
      - name: omnimesh
        image: omnimesh:latest
        ports:
        - containerPort: 8080
        - containerPort: 5173
        - containerPort: 50053
        env:
        - name: OMNIMESH_ENV
          value: "production"
        - name: RUST_LOG
          value: "info"
---
apiVersion: v1
kind: Service
metadata:
  name: omnimesh-service
spec:
  selector:
    app: omnimesh
  ports:
  - name: api
    port: 8080
    targetPort: 8080
  - name: frontend
    port: 5173
    targetPort: 5173
  - name: nexus
    port: 50053
    targetPort: 50053
  type: LoadBalancer
EOF
    
    echo -e "✅ Kubernetes configuration created"
    echo -e "${CYAN}Run: kubectl apply -f k8s/${NC}"
}

# ⚙️ CONFIGURATION HANDLERS
handle_configuration_operations() {
    local input="$1"
    
    if [[ "$input" =~ (reset|restore) ]]; then
        echo -e "🔄 Resetting configuration..."
        create_default_config
        setup_configuration
        echo -e "✅ Configuration reset to defaults"
    elif [[ "$input" =~ (backup) ]]; then
        echo -e "💾 Backing up configuration..."
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "✅ Configuration backed up"
    else
        echo -e "⚙️ Configuring system..."
        setup_configuration
    fi
}

# 📚 HELP HANDLERS
handle_help_request() {
    local input="$1"
    
    if [[ "$input" =~ examples ]]; then
        show_command_examples
    elif [[ "$input" =~ deploy ]]; then
        show_deployment_help
    else
        show_general_help
    fi
}

handle_install_dependencies() {
    local input="$1"
    
    echo -e "${GREEN}📦 Installing dependencies...${NC}"
    
    detect_system
    setup_package_manager
    
    if [[ "$input" =~ (python|py) ]]; then
        setup_python
    elif [[ "$input" =~ (node|npm|frontend) ]]; then
        setup_nodejs
    elif [[ "$input" =~ (rust|cargo) ]]; then
        setup_rust
    elif [[ "$input" =~ (go|golang) ]]; then
        setup_go
    else
        # Install all dependencies
        setup_python
        setup_nodejs
        setup_rust
        setup_go
        [[ "$INSTALL_DOCKER" == true ]] && setup_docker
    fi
}

# 🧠 SMART AUTO-DETECTION
auto_detect_and_build() {
    echo -e "🔍 Auto-detecting components to build..."
    
    # Ensure dependencies are installed
    detect_system
    setup_package_manager
    
    # Check what exists and build accordingly
    if [[ -f "Cargo.toml" ]] || find . -name "Cargo.toml" | grep -q .; then
        echo -e "🦀 Found Rust projects"
        setup_rust
        build_backend_components
    fi
    
    if [[ -f "package.json" ]] || find . -name "package.json" | grep -q .; then
        echo -e "📦 Found Node.js projects"
        setup_nodejs
        build_frontend_components
    fi
    
    if [[ -f "go.mod" ]] || find . -name "go.mod" | grep -q .; then
        echo -e "🐹 Found Go projects"
        setup_go
        build_go_components
    fi
    
    if [[ -f "requirements.txt" ]]; then
        echo -e "🐍 Found Python requirements"
        setup_python
    fi
}

# 💬 INTERACTIVE CONVERSATION MODE
interactive_conversation_mode() {
    echo -e "${PURPLE}🌊 OMNIMESH Interactive Mode${NC}"
    echo -e "${CYAN}Just tell me what you want to do in natural language!${NC}"
    echo -e "${YELLOW}Type 'exit' or 'quit' to leave${NC}"
    echo
    
    while true; do
        read -p "🌊 > " user_input
        
        case "$user_input" in
            "exit"|"quit"|"bye")
                echo -e "${GREEN}👋 Goodbye!${NC}"
                break
                ;;
            "help"|"?")
                show_general_help
                ;;
            "")
                continue
                ;;
            *)
                process_natural_language "$user_input"
                echo
                ;;
        esac
    done
}

# Help and examples system
show_general_help() {
    echo -e "${CYAN}🌊 OMNIMESH Universal Orchestrator${NC}"
    echo -e "${BOLD}Natural Language Command Interface${NC}"
    echo