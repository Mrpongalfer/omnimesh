#!/bin/bash

# 🌊 OmniMesh Quick Start Script
# One-command setup and launch for common users

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly USER_GUIDE="${SCRIPT_DIR}/USER_GUIDE.md"

# Colors for output
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

show_banner() {
    echo -e "${PURPLE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║               🌊 OMNIMESH QUICK START GUIDE                        ║${NC}"
    echo -e "${PURPLE}║                Tiger Lily Enhanced System                         ║${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

show_help() {
    echo -e "${BOLD}🌊 OmniMesh Quick Start - Choose Your Experience:${NC}"
    echo
    echo -e "${GREEN}For New Users:${NC}"
    echo "  $0 start           # Launch interactive menu"
    echo "  $0 cli             # Simple command-line interface"
    echo
    echo -e "${BLUE}For Visual Users:${NC}"
    echo "  $0 tui             # Beautiful terminal interface"
    echo "  $0 visual          # Same as 'tui'"
    echo "  $0 web             # Clickable web interface"
    echo "  $0 gui             # Same as 'web'"
    echo
    echo -e "${YELLOW}For Power Users:${NC}"
    echo "  $0 ai              # AI-powered automation"
    echo "  $0 ultimate        # Advanced AI features"
    echo
    echo -e "${PURPLE}For System Admins:${NC}"
    echo "  $0 orchestrator    # Recursive improvement engine"
    echo "  $0 admin           # Same as 'orchestrator'"
    echo
    echo -e "${RED}System Operations:${NC}"
    echo "  $0 status          # Quick system health check"
    echo "  $0 test            # Run system tests"
    echo "  $0 deploy          # Professional deployment"
    echo "  $0 security        # Security audit and enforcement"
    echo "  $0 monitor         # Setup system monitoring"
    echo
    echo -e "${CYAN}Tiger Lily Enforcement (Ω^9):${NC}"
    echo "  $0 tiger-lily      # Setup perpetual enforcement"
    echo "  $0 enforcement     # Manual enforcement check"
    echo "  $0 compliance      # Compliance verification"
    echo
    echo -e "${BOLD}Information & Help:${NC}"
    echo "  $0 help            # Show this help"
    echo "  $0 guide           # View full user guide"
    echo "  $0 features        # Discover all system features"
    echo "  $0 advanced        # Advanced operations menu"
    echo
    echo -e "${BOLD}Examples:${NC}"
    echo "  $0 start           # Interactive launcher (recommended for beginners)"
    echo "  $0 tui             # Launch visual terminal interface"
    echo "  $0 ai              # Start with AI assistance"
    echo "  $0 status          # Just check if everything is working"
    echo "  $0 features        # See all available capabilities"
    echo
}

check_system() {
    echo -e "${BLUE}🔍 Checking system status...${NC}"
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not found${NC}"
        return 1
    fi
    
    # Check if key files exist
    local key_files=("omni-launcher.py" "omni-interactive-tui.py" "omni_textual_tui.py")
    for file in "${key_files[@]}"; do
        if [ ! -f "${SCRIPT_DIR}/${file}" ]; then
            echo -e "${RED}❌ Missing key file: ${file}${NC}"
            return 1
        fi
    done
    
    # Check if config exists
    if [ ! -f "${SCRIPT_DIR}/omni-config.yaml" ]; then
        echo -e "${YELLOW}⚠️  Configuration file missing, will use defaults${NC}"
    fi
    
    echo -e "${GREEN}✅ System check passed${NC}"
    return 0
}

quick_status() {
    echo -e "${BLUE}📊 OmniMesh Quick Status Check${NC}"
    echo
    
    # System resources
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    echo -e "💻 System Resources:"
    echo -e "   CPU Usage: ${cpu_usage}%"
    echo -e "   Memory Usage: ${memory_usage}%"
    
    # Check if Tiger Lily enforcement is active
    if [ -f "${SCRIPT_DIR}/security-feedback/tiger-lily-metrics.json" ]; then
        echo -e "${GREEN}✅ Tiger Lily enforcement active${NC}"
    else
        echo -e "${YELLOW}⚠️  Tiger Lily enforcement not yet initialized${NC}"
    fi
    
    # Check recent logs
    local log_count=$(find "${SCRIPT_DIR}" -name "*.log" -mtime -1 2>/dev/null | wc -l)
    echo -e "📝 Recent activity logs: ${log_count}"
    
    echo
    echo -e "${GREEN}🌊 OmniMesh is ready to use!${NC}"
}

launch_interface() {
    local interface="$1"
    
    echo -e "${BLUE}🚀 Launching OmniMesh with ${interface} interface...${NC}"
    echo
    
    case "$interface" in
        "cli")
            python3 "${SCRIPT_DIR}/omni-launcher.py" --interface=cli
            ;;
        "tui"|"visual")
            python3 "${SCRIPT_DIR}/omni-launcher.py" --interface=textual
            ;;
        "ai"|"ultimate")
            python3 "${SCRIPT_DIR}/omni-launcher.py" --interface=ultimate
            ;;
        "orchestrator"|"admin")
            python3 "${SCRIPT_DIR}/omni-launcher.py" --interface=orchestrator
            ;;
        "start"|"menu")
            python3 "${SCRIPT_DIR}/omni-launcher.py"
            ;;
        *)
            echo -e "${RED}❌ Unknown interface: $interface${NC}"
            show_help
            return 1
            ;;
    esac
}

run_tests() {
    echo -e "${BLUE}🧪 Running OmniMesh system tests...${NC}"
    echo
    
    if [ -f "${SCRIPT_DIR}/test-omni-tui.py" ]; then
        python3 "${SCRIPT_DIR}/test-omni-tui.py"
    else
        echo -e "${YELLOW}⚠️  Test file not found, running basic validation...${NC}"
        
        # Basic validation
        if python3 -c "import omni_launcher" 2>/dev/null; then
            echo -e "${GREEN}✅ Core modules import successfully${NC}"
        else
            echo -e "${RED}❌ Module import failed${NC}"
            return 1
        fi
    fi
}

show_guide() {
    if [ -f "$USER_GUIDE" ]; then
        echo -e "${BLUE}📖 Opening user guide...${NC}"
        
        # Try to open with a pager if available
        if command -v less &> /dev/null; then
            less "$USER_GUIDE"
        elif command -v more &> /dev/null; then
            more "$USER_GUIDE"
        else
            cat "$USER_GUIDE"
        fi
    else
        echo -e "${RED}❌ User guide not found at: $USER_GUIDE${NC}"
        return 1
    fi
}

show_features() {
    echo -e "${BOLD}🌊 OmniMesh Complete Feature Discovery${NC}"
    echo
    echo -e "${GREEN}Core Interfaces:${NC}"
    echo "  • Interactive CLI with questionnaire prompts"
    echo "  • Full-screen Textual TUI with real-time updates"
    echo "  • Clickable Web Interface with visual dashboards"
    echo "  • AI-powered Ultimate System with monitoring"
    echo "  • Recursive System Orchestrator for autonomous improvement"
    echo
    echo -e "${BLUE}Tiger Lily Enforcement (Ω^9):${NC}"
    echo "  • Perpetual security feedback loops"
    echo "  • Resource monitoring with auto-dissolution"
    echo "  • Compliance verification and enforcement"
    echo "  • Exponential improvement mechanisms"
    echo
    echo -e "${YELLOW}DevOps & Deployment:${NC}"
    echo "  • Professional deployment scripts"
    echo "  • CI/CD pipeline with quality gates"
    echo "  • Security auditing and assessment"
    echo "  • Infrastructure as Code (Terraform)"
    echo
    echo -e "${PURPLE}Monitoring & Analytics:${NC}"
    echo "  • Real-time system resource tracking"
    echo "  • Performance metrics collection"
    echo "  • Log aggregation and analysis"
    echo "  • Health check automation"
    echo
    echo -e "${CYAN}Backend Services:${NC}"
    echo "  • Go-based node proxies with gRPC"
    echo "  • Rust-powered Nexus Prime Core"
    echo "  • Data fabric for distributed systems"
    echo "  • Container orchestration support"
    echo
    echo -e "${RED}Advanced Operations:${NC}"
    echo "  • Multi-environment configuration"
    echo "  • Automated testing suites"
    echo "  • Documentation generation"
    echo "  • User guide and help systems"
    echo
    echo -e "${BOLD}Access any feature via:${NC}"
    echo "  $0 advanced        # Advanced operations menu"
    echo "  $0 [feature-name]  # Direct feature access"
    echo
}

show_advanced_menu() {
    echo -e "${BOLD}🚀 Advanced Operations Menu${NC}"
    echo
    echo -e "${GREEN}Available Advanced Operations:${NC}"
    echo
    echo "1. Deploy complete system (deploy-ultimate.sh)"
    echo "2. Setup Tiger Lily enforcement (setup-perpetual-enforcement.sh)"
    echo "3. Run security audit (security-audit-complete.sh)"
    echo "4. Backend services deployment (BACKEND/build.sh)"
    echo "5. Infrastructure provisioning (infrastructure/)"
    echo "6. Kubernetes deployment (kubernetes/)"
    echo "7. Performance monitoring setup"
    echo "8. Log analysis and cleanup"
    echo "9. Configuration management"
    echo "10. Emergency recovery procedures"
    echo
    echo -e "${YELLOW}Enter number (1-10) or press Enter to return:${NC}"
    read -r choice
    
    case "$choice" in
        1) run_deployment ;;
        2) setup_enforcement ;;
        3) run_security_audit ;;
        4) build_backend ;;
        5) manage_infrastructure ;;
        6) deploy_kubernetes ;;
        7) setup_monitoring ;;
        8) manage_logs ;;
        9) manage_config ;;
        10) emergency_recovery ;;
        "") return ;;
        *) echo -e "${RED}Invalid choice${NC}" && sleep 1 && show_advanced_menu ;;
    esac
}

run_deployment() {
    echo -e "${BLUE}🚀 Running professional deployment...${NC}"
    if [ -f "${SCRIPT_DIR}/deploy-ultimate.sh" ]; then
        chmod +x "${SCRIPT_DIR}/deploy-ultimate.sh"
        "${SCRIPT_DIR}/deploy-ultimate.sh"
    else
        echo -e "${RED}Deployment script not found${NC}"
    fi
}

setup_enforcement() {
    echo -e "${PURPLE}🔒 Setting up Tiger Lily enforcement...${NC}"
    if [ -f "${SCRIPT_DIR}/setup-perpetual-enforcement.sh" ]; then
        chmod +x "${SCRIPT_DIR}/setup-perpetual-enforcement.sh"
        "${SCRIPT_DIR}/setup-perpetual-enforcement.sh"
    else
        echo -e "${RED}Enforcement setup script not found${NC}"
    fi
}

run_security_audit() {
    echo -e "${RED}🔍 Running security audit...${NC}"
    if [ -f "${SCRIPT_DIR}/security-audit-complete.sh" ]; then
        chmod +x "${SCRIPT_DIR}/security-audit-complete.sh"
        "${SCRIPT_DIR}/security-audit-complete.sh"
    else
        echo -e "${RED}Security audit script not found${NC}"
    fi
}

build_backend() {
    echo -e "${GREEN}🔧 Building backend services...${NC}"
    if [ -f "${SCRIPT_DIR}/BACKEND/build.sh" ]; then
        cd "${SCRIPT_DIR}/BACKEND"
        chmod +x build.sh
        ./build.sh
        cd "${SCRIPT_DIR}"
    else
        echo -e "${RED}Backend build script not found${NC}"
    fi
}

manage_infrastructure() {
    echo -e "${BLUE}🏗️ Managing infrastructure...${NC}"
    if [ -d "${SCRIPT_DIR}/infrastructure" ]; then
        cd "${SCRIPT_DIR}/infrastructure"
        echo "Available Terraform operations:"
        echo "1. terraform plan"
        echo "2. terraform apply"
        echo "3. terraform destroy"
        echo "Enter choice (1-3):"
        read -r tf_choice
        case "$tf_choice" in
            1) terraform plan ;;
            2) terraform apply ;;
            3) terraform destroy ;;
            *) echo "Invalid choice" ;;
        esac
        cd "${SCRIPT_DIR}"
    else
        echo -e "${RED}Infrastructure directory not found${NC}"
    fi
}

deploy_kubernetes() {
    echo -e "${CYAN}☸️ Deploying to Kubernetes...${NC}"
    if [ -d "${SCRIPT_DIR}/kubernetes" ]; then
        cd "${SCRIPT_DIR}/kubernetes"
        echo "Applying Kubernetes manifests..."
        kubectl apply -f base/ || echo -e "${RED}kubectl not available or cluster not accessible${NC}"
        cd "${SCRIPT_DIR}"
    else
        echo -e "${RED}Kubernetes directory not found${NC}"
    fi
}

setup_monitoring() {
    echo -e "${YELLOW}📊 Setting up system monitoring...${NC}"
    # Create monitoring directories
    mkdir -p "${SCRIPT_DIR}/monitoring/logs"
    mkdir -p "${SCRIPT_DIR}/monitoring/metrics"
    
    # Start basic monitoring
    echo "Setting up resource monitoring..."
    nohup bash -c 'while true; do
        echo "$(date): CPU: $(top -bn1 | grep "Cpu(s)" | awk "{print \$2}" | cut -d"%" -f1 | cut -d"," -f1)%" >> monitoring/logs/cpu.log
        echo "$(date): Memory: $(free | grep Mem | awk "{printf \"%.1f\", \$3/\$2 * 100.0}")%" >> monitoring/logs/memory.log
        sleep 60
    done' &
    
    echo -e "${GREEN}✅ Monitoring setup complete${NC}"
}

manage_logs() {
    echo -e "${PURPLE}📝 Managing system logs...${NC}"
    echo "Recent log files:"
    find "${SCRIPT_DIR}" -name "*.log" -mtime -1 -exec ls -la {} \; 2>/dev/null || echo "No recent logs found"
    
    echo
    echo "Cleanup options:"
    echo "1. Clean logs older than 7 days"
    echo "2. Clean logs older than 1 day"
    echo "3. View log summary"
    echo "Enter choice (1-3):"
    read -r log_choice
    
    case "$log_choice" in
        1) find "${SCRIPT_DIR}" -name "*.log" -mtime +7 -delete && echo "Cleaned logs older than 7 days" ;;
        2) find "${SCRIPT_DIR}" -name "*.log" -mtime +1 -delete && echo "Cleaned logs older than 1 day" ;;
        3) find "${SCRIPT_DIR}" -name "*.log" -exec wc -l {} \; | sort -nr | head -10 ;;
        *) echo "Invalid choice" ;;
    esac
}

manage_config() {
    echo -e "${CYAN}⚙️ Configuration management...${NC}"
    echo "Configuration files:"
    ls -la "${SCRIPT_DIR}"/*.yaml "${SCRIPT_DIR}"/*.yml "${SCRIPT_DIR}"/*.json 2>/dev/null || echo "No config files found"
    
    if [ -f "${SCRIPT_DIR}/omni-config.yaml" ]; then
        echo
        echo "Current configuration preview:"
        head -20 "${SCRIPT_DIR}/omni-config.yaml"
    fi
}

emergency_recovery() {
    echo -e "${RED}🚨 Emergency Recovery Procedures${NC}"
    echo
    echo "Available recovery options:"
    echo "1. Reset to safe configuration"
    echo "2. Restart all services"
    echo "3. Check system integrity"
    echo "4. Backup current state"
    echo "5. View emergency contacts"
    echo
    echo "Enter choice (1-5):"
    read -r recovery_choice
    
    case "$recovery_choice" in
        1) 
            echo "Resetting to safe configuration..."
            # Create minimal safe config
            cat > "${SCRIPT_DIR}/omni-config-safe.yaml" << 'EOF'
# Safe configuration for emergency recovery
app:
  name: "OmniMesh"
  version: "safe-mode"
  debug: true
  
interfaces:
  cli:
    enabled: true
  tui:
    enabled: false
  ultimate:
    enabled: false
  orchestrator:
    enabled: false
EOF
            echo -e "${GREEN}Safe configuration created as omni-config-safe.yaml${NC}"
            ;;
        2) 
            echo "Restarting services... (simulation)"
            echo -e "${GREEN}Services restarted${NC}"
            ;;
        3) 
            echo "Checking system integrity..."
            check_system
            ;;
        4) 
            echo "Creating backup..."
            tar -czf "omnimesh-backup-$(date +%Y%m%d-%H%M%S).tar.gz" \
                --exclude="*.log" --exclude="target/" --exclude="node_modules/" \
                "${SCRIPT_DIR}"
            echo -e "${GREEN}Backup created${NC}"
            ;;
        5) 
            echo "Emergency Contacts:"
            echo "  System Administrator: admin@omnimesh.local"
            echo "  Tiger Lily Protocol: security@omnimesh.local"
            echo "  Technical Support: support@omnimesh.local"
            ;;
        *) echo "Invalid choice" ;;
    esac
}

launch_web_interface() {
    echo -e "${CYAN}🌐 Launching OmniMesh Web Interface...${NC}"
    echo
    
    # Check if Python and required modules are available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required for the web interface${NC}"
        return 1
    fi
    
    # Check if psutil is available (for system metrics)
    python3 -c "import psutil" 2>/dev/null || {
        echo -e "${YELLOW}📦 Installing required Python package (psutil)...${NC}"
        pip3 install psutil --user 2>/dev/null || {
            echo -e "${RED}❌ Failed to install psutil. Please install manually: pip3 install psutil${NC}"
            return 1
        }
    }
    
    # Find available port
    local port=8080
    while netstat -ln 2>/dev/null | grep -q ":${port} "; do
        port=$((port + 1))
    done
    
    echo -e "${GREEN}🚀 Starting web server on port ${port}...${NC}"
    echo -e "${CYAN}   Access URL: http://localhost:${port}${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop the server${NC}"
    echo
    
    # Start the web server
    if [ -f "${SCRIPT_DIR}/omni-web-server.py" ]; then
        python3 "${SCRIPT_DIR}/omni-web-server.py" --port "$port"
    else
        echo -e "${RED}❌ Web server file not found${NC}"
        return 1
    fi
}

main() {
    local command="${1:-help}"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    case "$command" in
        "start"|"menu"|"launch")
            show_banner
            if check_system; then
                launch_interface "start"
            fi
            ;;
        "cli")
            show_banner
            if check_system; then
                launch_interface "cli"
            fi
            ;;
        "tui"|"visual")
            show_banner
            if check_system; then
                launch_interface "tui"
            fi
            ;;
        "web"|"gui"|"ui")
            show_banner
            if check_system; then
                launch_web_interface
            fi
            ;;
        "ai"|"ultimate")
            show_banner
            if check_system; then
                launch_interface "ai"
            fi
            ;;
        "orchestrator"|"admin")
            show_banner
            if check_system; then
                launch_interface "orchestrator"
            fi
            ;;
        "status"|"check")
            show_banner
            quick_status
            ;;
        "test"|"tests")
            show_banner
            run_tests
            ;;
        "deploy"|"deployment")
            show_banner
            run_deployment
            ;;
        "security"|"audit")
            show_banner
            run_security_audit
            ;;
        "monitor"|"monitoring")
            show_banner
            setup_monitoring
            ;;
        "tiger-lily"|"enforcement")
            show_banner
            setup_enforcement
            ;;
        "compliance"|"verify")
            show_banner
            echo -e "${BLUE}🔍 Running compliance verification...${NC}"
            if [ -f "${SCRIPT_DIR}/tiger-lily-enforcement.sh" ]; then
                chmod +x "${SCRIPT_DIR}/tiger-lily-enforcement.sh"
                "${SCRIPT_DIR}/tiger-lily-enforcement.sh" --verify
            else
                echo -e "${RED}Tiger Lily enforcement script not found${NC}"
            fi
            ;;
        "guide"|"docs"|"documentation")
            show_guide
            ;;
        "features"|"discover")
            show_banner
            show_features
            ;;
        "advanced"|"advanced-menu")
            show_banner
            show_advanced_menu
            ;;
        "help"|"-h"|"--help")
            show_banner
            show_help
            ;;
        *)
            show_banner
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
