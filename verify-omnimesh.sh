#!/bin/bash

# 🔍 OMNIMESH Installation Verification Script
# Comprehensive health check and diagnostic tool

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CHECK_LOG="${SCRIPT_DIR}/verification.log"

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Status tracking
declare -A CHECK_RESULTS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Logging
log_check() {
    local status="$1"
    local component="$2"
    local message="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${status}] ${component}: ${message}" >> "${CHECK_LOG}"
    
    case "$status" in
        "PASS")
            echo -e "  ✅ ${GREEN}${component}${NC}: ${message}"
            ((PASSED_CHECKS++))
            ;;
        "FAIL")
            echo -e "  ❌ ${RED}${component}${NC}: ${message}"
            ((FAILED_CHECKS++))
            ;;
        "WARN")
            echo -e "  ⚠️  ${YELLOW}${component}${NC}: ${message}"
            ((WARNING_CHECKS++))
            ;;
        "INFO")
            echo -e "  ℹ️  ${CYAN}${component}${NC}: ${message}"
            ;;
    esac
    
    CHECK_RESULTS["$component"]="$status"
    ((TOTAL_CHECKS++))
}

# Banner
show_banner() {
    clear
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    🔍 OMNIMESH VERIFICATION SYSTEM                          ║${NC}"
    echo -e "${PURPLE}║                                                                              ║${NC}"
    echo -e "${PURPLE}║               Comprehensive Installation Health Check                        ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}Verification Log: ${CHECK_LOG}${NC}"
    echo
}

# Check system information
check_system_info() {
    echo -e "${BOLD}🖥️ System Information${NC}"
    
    local os_info=$(uname -s)
    local arch_info=$(uname -m)
    local kernel_info=$(uname -r)
    
    log_check "INFO" "Operating System" "$os_info $arch_info"
    log_check "INFO" "Kernel Version" "$kernel_info"
    
    if command -v lsb_release &> /dev/null; then
        local distro_info=$(lsb_release -d | cut -f2)
        log_check "INFO" "Distribution" "$distro_info"
    fi
    
    echo
}

# Check Python environment
check_python_environment() {
    echo -e "${BOLD}🐍 Python Environment${NC}"
    
    # Check Python installation
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        local major_version=$(echo "$python_version" | cut -d'.' -f1)
        local minor_version=$(echo "$python_version" | cut -d'.' -f2)
        
        if [[ $major_version -ge 3 && $minor_version -ge 8 ]]; then
            log_check "PASS" "Python Version" "$python_version (meets requirement ≥3.8)"
        else
            log_check "FAIL" "Python Version" "$python_version (requires ≥3.8)"
        fi
    else
        log_check "FAIL" "Python Installation" "Python3 not found"
    fi
    
    # Check virtual environment
    if [[ -d "venv" ]]; then
        log_check "PASS" "Virtual Environment" "Found at venv/"
        
        # Check if we can activate it
        if source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; then
            log_check "PASS" "Virtual Environment" "Successfully activated"
            
            # Check pip
            if command -v pip &> /dev/null; then
                local pip_version=$(pip --version | cut -d' ' -f2)
                log_check "PASS" "Pip Version" "$pip_version"
            else
                log_check "FAIL" "Pip Installation" "pip not found in virtual environment"
            fi
            
            # Check required packages
            local missing_packages=()
            while IFS= read -r package; do
                if [[ "$package" =~ ^[a-zA-Z] ]]; then
                    local pkg_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'[' -f1)
                    if ! pip show "$pkg_name" &> /dev/null; then
                        missing_packages+=("$pkg_name")
                    fi
                fi
            done < requirements.txt
            
            if [[ ${#missing_packages[@]} -eq 0 ]]; then
                log_check "PASS" "Python Dependencies" "All required packages installed"
            else
                log_check "FAIL" "Python Dependencies" "Missing: ${missing_packages[*]}"
            fi
            
            deactivate 2>/dev/null || true
        else
            log_check "FAIL" "Virtual Environment" "Cannot activate virtual environment"
        fi
    else
        log_check "FAIL" "Virtual Environment" "venv/ directory not found"
    fi
    
    echo
}

# Check Node.js environment
check_nodejs_environment() {
    echo -e "${BOLD}📦 Node.js Environment${NC}"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version | sed 's/v//')
        local major_version=$(echo "$node_version" | cut -d'.' -f1)
        
        if [[ $major_version -ge 18 ]]; then
            log_check "PASS" "Node.js Version" "$node_version (meets requirement ≥18)"
        else
            log_check "WARN" "Node.js Version" "$node_version (recommended ≥18)"
        fi
    else
        log_check "FAIL" "Node.js Installation" "Node.js not found"
        return
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        log_check "PASS" "npm Version" "$npm_version"
    else
        log_check "FAIL" "npm Installation" "npm not found"
    fi
    
    # Check pnpm
    if command -v pnpm &> /dev/null; then
        local pnpm_version=$(pnpm --version)
        log_check "PASS" "pnpm Version" "$pnpm_version"
    else
        log_check "WARN" "pnpm Installation" "pnpm not found (recommended for frontend)"
    fi
    
    echo
}

# Check Rust environment
check_rust_environment() {
    echo -e "${BOLD}🦀 Rust Environment${NC}"
    
    # Check Rust installation
    if command -v rustc &> /dev/null; then
        local rust_version=$(rustc --version | cut -d' ' -f2)
        log_check "PASS" "Rust Version" "$rust_version"
        
        # Check Cargo
        if command -v cargo &> /dev/null; then
            local cargo_version=$(cargo --version | cut -d' ' -f2)
            log_check "PASS" "Cargo Version" "$cargo_version"
        else
            log_check "FAIL" "Cargo Installation" "cargo not found"
        fi
        
        # Check rustfmt
        if command -v rustfmt &> /dev/null; then
            log_check "PASS" "rustfmt Component" "Available"
        else
            log_check "WARN" "rustfmt Component" "Not installed (run: rustup component add rustfmt)"
        fi
        
        # Check clippy
        if command -v cargo-clippy &> /dev/null; then
            log_check "PASS" "clippy Component" "Available"
        else
            log_check "WARN" "clippy Component" "Not installed (run: rustup component add clippy)"
        fi
    else
        log_check "FAIL" "Rust Installation" "Rust not found"
    fi
    
    echo
}

# Check Go environment
check_go_environment() {
    echo -e "${BOLD}🐹 Go Environment${NC}"
    
    if command -v go &> /dev/null; then
        local go_version=$(go version | cut -d' ' -f3 | sed 's/go//')
        local major_version=$(echo "$go_version" | cut -d'.' -f1)
        local minor_version=$(echo "$go_version" | cut -d'.' -f2)
        
        if [[ $major_version -eq 1 && $minor_version -ge 20 ]]; then
            log_check "PASS" "Go Version" "$go_version (meets requirement ≥1.20)"
        else
            log_check "WARN" "Go Version" "$go_version (recommended ≥1.20)"
        fi
        
        # Check GOPATH and GOROOT
        local gopath=$(go env GOPATH)
        local goroot=$(go env GOROOT)
        log_check "INFO" "GOPATH" "$gopath"
        log_check "INFO" "GOROOT" "$goroot"
    else
        log_check "FAIL" "Go Installation" "Go not found"
    fi
    
    echo
}

# Check Docker environment
check_docker_environment() {
    echo -e "${BOLD}🐳 Docker Environment${NC}"
    
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        log_check "PASS" "Docker Version" "$docker_version"
        
        # Check if Docker daemon is running
        if docker info &> /dev/null; then
            log_check "PASS" "Docker Daemon" "Running and accessible"
            
            # Check Docker Compose
            if docker compose version &> /dev/null; then
                local compose_version=$(docker compose version | cut -d' ' -f4)
                log_check "PASS" "Docker Compose" "$compose_version"
            else
                log_check "WARN" "Docker Compose" "Not available or old version"
            fi
        else
            log_check "FAIL" "Docker Daemon" "Not running or not accessible"
        fi
    else
        log_check "FAIL" "Docker Installation" "Docker not found"
    fi
    
    echo
}

# Check Kubernetes tools
check_kubernetes_tools() {
    echo -e "${BOLD}☸️ Kubernetes Tools${NC}"
    
    # Check kubectl
    if command -v kubectl &> /dev/null; then
        local kubectl_version=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 | sed 's/v//')
        log_check "PASS" "kubectl Version" "$kubectl_version"
        
        # Check cluster connectivity
        if kubectl cluster-info &> /dev/null; then
            log_check "PASS" "Cluster Connectivity" "Connected to Kubernetes cluster"
        else
            log_check "WARN" "Cluster Connectivity" "No cluster connection"
        fi
    else
        log_check "WARN" "kubectl Installation" "kubectl not found (optional)"
    fi
    
    # Check kind
    if command -v kind &> /dev/null; then
        local kind_version=$(kind --version | cut -d' ' -f3)
        log_check "PASS" "kind Version" "$kind_version"
    else
        log_check "WARN" "kind Installation" "kind not found (optional for local development)"
    fi
    
    echo
}

# Check OMNIMESH components
check_omnimesh_components() {
    echo -e "${BOLD}🌊 OMNIMESH Components${NC}"
    
    # Check configuration file
    if [[ -f "omni-config.yaml" ]]; then
        log_check "PASS" "Configuration File" "omni-config.yaml found"
        
        # Validate YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('omni-config.yaml'))" 2>/dev/null; then
            log_check "PASS" "Configuration Syntax" "Valid YAML"
        else
            log_check "FAIL" "Configuration Syntax" "Invalid YAML in omni-config.yaml"
        fi
    else
        log_check "FAIL" "Configuration File" "omni-config.yaml not found"
    fi
    
    # Check Python TUI scripts
    local tui_scripts=(
        "omni_launcher.py"
        "omni_ultimate_system.py"
        "omni_system_orchestrator.py"
        "omni_textual_tui.py"
        "omni-interactive-tui.py"
    )
    
    for script in "${tui_scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if [[ -x "$script" ]]; then
                log_check "PASS" "TUI Script: $script" "Executable"
            else
                log_check "WARN" "TUI Script: $script" "Not executable (run: chmod +x $script)"
            fi
        else
            log_check "FAIL" "TUI Script: $script" "Not found"
        fi
    done
    
    # Check quick-start script
    if [[ -f "quick-start.sh" ]]; then
        if [[ -x "quick-start.sh" ]]; then
            log_check "PASS" "Quick Start Script" "Executable"
        else
            log_check "WARN" "Quick Start Script" "Not executable (run: chmod +x quick-start.sh)"
        fi
    else
        log_check "FAIL" "Quick Start Script" "quick-start.sh not found"
    fi
    
    echo
}

# Check Backend components
check_backend_components() {
    echo -e "${BOLD}🏗️ Backend Components${NC}"
    
    if [[ -d "BACKEND" ]]; then
        log_check "PASS" "Backend Directory" "BACKEND/ found"
        
        # Check Nexus Prime Core
        if [[ -d "BACKEND/nexus-prime-core" ]]; then
            log_check "PASS" "Nexus Prime Core" "Directory found"
            
            if [[ -f "BACKEND/nexus-prime-core/Cargo.toml" ]]; then
                log_check "PASS" "Rust Project" "Cargo.toml found"
                
                # Check if binary exists
                if [[ -f "BACKEND/nexus-prime-core/target/release/nexus-prime-core" ]]; then
                    log_check "PASS" "Nexus Binary" "Built release binary found"
                elif [[ -f "BACKEND/nexus-prime-core/target/debug/nexus-prime-core" ]]; then
                    log_check "WARN" "Nexus Binary" "Debug binary found (run: cargo build --release)"
                else
                    log_check "WARN" "Nexus Binary" "No binary found (run: cargo build)"
                fi
            else
                log_check "FAIL" "Rust Project" "Cargo.toml not found"
            fi
        else
            log_check "FAIL" "Nexus Prime Core" "Directory not found"
        fi
        
        # Check Go Node Proxies
        if [[ -d "BACKEND/go-node-proxies" ]]; then
            log_check "PASS" "Go Node Proxies" "Directory found"
            
            if [[ -f "BACKEND/go-node-proxies/go.mod" ]]; then
                log_check "PASS" "Go Module" "go.mod found"
                
                # Check if binary exists
                if [[ -f "BACKEND/go-node-proxies/bin/node-proxy" ]]; then
                    log_check "PASS" "Node Proxy Binary" "Built binary found"
                else
                    log_check "WARN" "Node Proxy Binary" "No binary found (run: go build -o bin/node-proxy)"
                fi
            else
                log_check "FAIL" "Go Module" "go.mod not found"
            fi
        else
            log_check "FAIL" "Go Node Proxies" "Directory not found"
        fi
    else
        log_check "FAIL" "Backend Directory" "BACKEND/ not found"
    fi
    
    echo
}

# Check Frontend components
check_frontend_components() {
    echo -e "${BOLD}🎨 Frontend Components${NC}"
    
    if [[ -d "FRONTEND" ]]; then
        log_check "PASS" "Frontend Directory" "FRONTEND/ found"
        
        # Check SolidJS UI
        if [[ -d "FRONTEND/ui-solidjs" ]]; then
            log_check "PASS" "SolidJS UI" "Directory found"
            
            if [[ -f "FRONTEND/ui-solidjs/package.json" ]]; then
                log_check "PASS" "Package Config" "package.json found"
                
                # Check node_modules
                if [[ -d "FRONTEND/ui-solidjs/node_modules" ]]; then
                    log_check "PASS" "Dependencies" "node_modules found"
                else
                    log_check "WARN" "Dependencies" "node_modules not found (run: pnpm install)"
                fi
                
                # Check build output
                if [[ -d "FRONTEND/ui-solidjs/dist" ]]; then
                    log_check "PASS" "Build Output" "dist/ found"
                else
                    log_check "WARN" "Build Output" "dist/ not found (run: pnpm run build)"
                fi
            else
                log_check "FAIL" "Package Config" "package.json not found"
            fi
        else
            log_check "FAIL" "SolidJS UI" "Directory not found"
        fi
    else
        log_check "WARN" "Frontend Directory" "FRONTEND/ not found (optional)"
    fi
    
    echo
}

# Check Infrastructure components
check_infrastructure_components() {
    echo -e "${BOLD}☁️ Infrastructure Components${NC}"
    
    if [[ -d "infrastructure" ]]; then
        log_check "PASS" "Infrastructure Directory" "infrastructure/ found"
        
        # Check Terraform
        if [[ -f "infrastructure/main.tf" ]]; then
            log_check "PASS" "Terraform Config" "main.tf found"
            
            if command -v terraform &> /dev/null; then
                local tf_version=$(terraform --version | head -n1 | cut -d' ' -f2)
                log_check "PASS" "Terraform CLI" "$tf_version"
            else
                log_check "WARN" "Terraform CLI" "terraform command not found"
            fi
        else
            log_check "FAIL" "Terraform Config" "main.tf not found"
        fi
    else
        log_check "WARN" "Infrastructure Directory" "infrastructure/ not found (optional)"
    fi
    
    # Check Kubernetes manifests
    if [[ -d "kubernetes" ]]; then
        log_check "PASS" "Kubernetes Directory" "kubernetes/ found"
        
        if [[ -f "kubernetes/argocd-applications.yaml" ]]; then
            log_check "PASS" "ArgoCD Config" "argocd-applications.yaml found"
        else
            log_check "WARN" "ArgoCD Config" "argocd-applications.yaml not found"
        fi
    else
        log_check "WARN" "Kubernetes Directory" "kubernetes/ not found (optional)"
    fi
    
    echo
}

# Check AI components
check_ai_components() {
    echo -e "${BOLD}🧠 AI Components${NC}"
    
    # Check OpenAI configuration
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        log_check "PASS" "OpenAI API Key" "Environment variable set"
    else
        log_check "WARN" "OpenAI API Key" "OPENAI_API_KEY not set (AI features disabled)"
    fi
    
    # Check AI dependencies in Python
    if source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; then
        if pip show openai &> /dev/null; then
            local openai_version=$(pip show openai | grep Version | cut -d' ' -f2)
            log_check "PASS" "OpenAI Python Library" "$openai_version"
        else
            log_check "WARN" "OpenAI Python Library" "openai package not installed"
        fi
        deactivate 2>/dev/null || true
    fi
    
    echo
}

# Check security components
check_security_components() {
    echo -e "${BOLD}🛡️ Security Components${NC}"
    
    # Check security scripts
    if [[ -f "tiger-lily-enforcement.sh" ]]; then
        log_check "PASS" "Tiger Lily Enforcement" "Script found"
    else
        log_check "WARN" "Tiger Lily Enforcement" "tiger-lily-enforcement.sh not found"
    fi
    
    if [[ -f "security-audit-complete.sh" ]]; then
        log_check "PASS" "Security Audit" "Script found"
    else
        log_check "WARN" "Security Audit" "security-audit-complete.sh not found"
    fi
    
    # Check SSL/TLS configuration
    if [[ -d "/etc/ssl/certs" ]]; then
        log_check "PASS" "SSL Certificates Directory" "/etc/ssl/certs exists"
    else
        log_check "WARN" "SSL Certificates Directory" "/etc/ssl/certs not found"
    fi
    
    echo
}

# Performance test
run_performance_test() {
    echo -e "${BOLD}⚡ Performance Test${NC}"
    
    # Test Python TUI startup time
    if [[ -f "omni_launcher.py" ]]; then
        local start_time=$(date +%s%N)
        if timeout 10s python3 omni_launcher.py --help &> /dev/null; then
            local end_time=$(date +%s%N)
            local duration=$(( (end_time - start_time) / 1000000 ))
            
            if [[ $duration -lt 2000 ]]; then
                log_check "PASS" "TUI Startup Time" "${duration}ms (excellent)"
            elif [[ $duration -lt 5000 ]]; then
                log_check "PASS" "TUI Startup Time" "${duration}ms (good)"
            else
                log_check "WARN" "TUI Startup Time" "${duration}ms (slow)"
            fi
        else
            log_check "FAIL" "TUI Startup Test" "Failed to run omni_launcher.py --help"
        fi
    fi
    
    echo
}

# Generate summary report
generate_summary() {
    echo -e "${BOLD}📊 Verification Summary${NC}"
    echo
    echo -e "  📈 Total Checks: ${TOTAL_CHECKS}"
    echo -e "  ✅ Passed: ${GREEN}${PASSED_CHECKS}${NC}"
    echo -e "  ⚠️  Warnings: ${YELLOW}${WARNING_CHECKS}${NC}"
    echo -e "  ❌ Failed: ${RED}${FAILED_CHECKS}${NC}"
    echo
    
    local success_rate=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    
    if [[ $success_rate -ge 90 ]]; then
        echo -e "  🎉 ${GREEN}Overall Status: EXCELLENT${NC} (${success_rate}%)"
        echo -e "  🚀 ${GREEN}OMNIMESH is ready for production use!${NC}"
    elif [[ $success_rate -ge 75 ]]; then
        echo -e "  👍 ${BLUE}Overall Status: GOOD${NC} (${success_rate}%)"
        echo -e "  🔧 ${BLUE}Minor issues detected, but system is functional${NC}"
    elif [[ $success_rate -ge 50 ]]; then
        echo -e "  ⚠️  ${YELLOW}Overall Status: NEEDS ATTENTION${NC} (${success_rate}%)"
        echo -e "  🔨 ${YELLOW}Several issues need to be resolved${NC}"
    else
        echo -e "  ❌ ${RED}Overall Status: CRITICAL ISSUES${NC} (${success_rate}%)"
        echo -e "  🆘 ${RED}Major problems detected, please review installation${NC}"
    fi
    
    echo
    echo -e "${CYAN}💡 Recommendations:${NC}"
    
    if [[ $FAILED_CHECKS -gt 0 ]]; then
        echo -e "  • Review failed checks and install missing components"
        echo -e "  • Run the installer script: ./install-omnimesh.sh"
    fi
    
    if [[ $WARNING_CHECKS -gt 0 ]]; then
        echo -e "  • Address warnings for optimal performance"
        echo -e "  • Consider installing optional components"
    fi
    
    echo -e "  • Check the verification log: ${CHECK_LOG}"
    echo -e "  • Run './quick-start.sh --help' for usage instructions"
    echo
}

# Main function
main() {
    show_banner
    
    echo -e "${CYAN}Starting comprehensive verification...${NC}"
    echo
    
    # Initialize log
    echo "OMNIMESH Verification Report - $(date)" > "${CHECK_LOG}"
    echo "=======================================" >> "${CHECK_LOG}"
    
    # Run all checks
    check_system_info
    check_python_environment
    check_nodejs_environment
    check_rust_environment
    check_go_environment
    check_docker_environment
    check_kubernetes_tools
    check_omnimesh_components
    check_backend_components
    check_frontend_components
    check_infrastructure_components
    check_ai_components
    check_security_components
    run_performance_test
    
    # Generate summary
    generate_summary
    
    echo -e "${PURPLE}🔍 Verification complete! Check ${CHECK_LOG} for detailed results.${NC}"
}

# Run main function
main "$@"
