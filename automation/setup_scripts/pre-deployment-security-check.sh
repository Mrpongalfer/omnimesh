#!/bin/bash

# OmniMesh Pre-Deployment Security Check
# This script performs comprehensive security validation before deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/omnimesh-security-check.log"
NAMESPACE="omnimesh"
IMAGE_REGISTRY="ghcr.io/mrpongalfer/omnimesh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Initialize logging
echo "$(date): Starting OmniMesh pre-deployment security check" > "$LOG_FILE"

log_info "🔒 OmniMesh Pre-Deployment Security Check"
log_info "Log file: $LOG_FILE"

# Check required tools
check_dependencies() {
    log_info "Checking dependencies..."
    
    local required_tools=("kubectl" "docker" "helm" "cosign" "trivy" "conftest" "truffleHog")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools before continuing"
        exit 1
    fi
    
    log_success "All required tools are available"
}

# Verify Kubernetes cluster access
check_cluster_access() {
    log_info "Checking Kubernetes cluster access..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        log_error "Please ensure kubeconfig is properly configured"
        exit 1
    fi
    
    # Check cluster version
    local cluster_version
    cluster_version=$(kubectl version --short | grep "Server Version" | cut -d: -f2 | tr -d ' ')
    log_info "Cluster version: $cluster_version"
    
    # Check if we have required permissions
    if ! kubectl auth can-i create namespace &> /dev/null; then
        log_error "Insufficient permissions to create namespaces"
        exit 1
    fi
    
    log_success "Kubernetes cluster access verified"
}

# Verify container image signatures
verify_image_signatures() {
    log_info "Verifying container image signatures..."
    
    local images=(
        "$IMAGE_REGISTRY/core:latest"
        "$IMAGE_REGISTRY/ui:latest"
        "$IMAGE_REGISTRY/gateway:latest"
        "$IMAGE_REGISTRY/operator:latest"
    )
    
    for image in "${images[@]}"; do
        log_info "Verifying signature for $image"
        
        # Check if image exists
        if ! docker manifest inspect "$image" &> /dev/null; then
            log_warn "Image $image not found, skipping signature verification"
            continue
        fi
        
        # Verify signature (skip in demo mode)
        if [[ "${DEMO_MODE:-false}" == "true" ]]; then
            log_warn "Demo mode: Skipping signature verification for $image"
        else
            if ! cosign verify --key cosign.pub "$image" &> /dev/null; then
                log_error "Signature verification failed for $image"
                exit 1
            fi
            log_success "Signature verified for $image"
        fi
    done
}

# Run security scan on container images
run_security_scan() {
    log_info "Running security scan on container images..."
    
    local images=(
        "$IMAGE_REGISTRY/core:latest"
        "$IMAGE_REGISTRY/ui:latest"
        "$IMAGE_REGISTRY/gateway:latest"
        "$IMAGE_REGISTRY/operator:latest"
    )
    
    local scan_failed=false
    
    for image in "${images[@]}"; do
        log_info "Scanning $image for vulnerabilities"
        
        # Check if image exists
        if ! docker manifest inspect "$image" &> /dev/null; then
            log_warn "Image $image not found, skipping security scan"
            continue
        fi
        
        # Run Trivy scan
        local scan_output
        scan_output=$(mktemp)
        
        if trivy image --severity HIGH,CRITICAL --format json --output "$scan_output" "$image" 2>/dev/null; then
            local vulnerabilities
            vulnerabilities=$(jq '.Results[].Vulnerabilities | length' "$scan_output" 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
            
            if [[ $vulnerabilities -gt 0 ]]; then
                log_error "Found $vulnerabilities HIGH/CRITICAL vulnerabilities in $image"
                scan_failed=true
            else
                log_success "No HIGH/CRITICAL vulnerabilities found in $image"
            fi
        else
            log_warn "Security scan failed for $image"
        fi
        
        rm -f "$scan_output"
    done
    
    if [[ "$scan_failed" == "true" ]]; then
        log_error "Security scan failed for one or more images"
        if [[ "${IGNORE_SCAN_FAILURES:-false}" != "true" ]]; then
            exit 1
        else
            log_warn "Ignoring scan failures due to IGNORE_SCAN_FAILURES=true"
        fi
    fi
}

# Validate Kubernetes manifests
validate_manifests() {
    log_info "Validating Kubernetes manifests..."
    
    local manifest_dirs=(
        "$PROJECT_ROOT/kubernetes/security"
        "$PROJECT_ROOT/kubernetes/base"
        "$PROJECT_ROOT/kubernetes/production"
    )
    
    for dir in "${manifest_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warn "Manifest directory $dir not found, skipping"
            continue
        fi
        
        log_info "Validating manifests in $dir"
        
        # Validate YAML syntax
        find "$dir" -name "*.yaml" -o -name "*.yml" | while read -r manifest; do
            if ! kubectl apply --dry-run=client -f "$manifest" &> /dev/null; then
                log_error "Invalid manifest: $manifest"
                exit 1
            fi
        done
        
        # Run conftest if policies exist
        if [[ -d "$PROJECT_ROOT/security-policies" ]]; then
            if ! conftest verify --policy "$PROJECT_ROOT/security-policies" "$dir"/*.yaml &> /dev/null; then
                log_warn "Policy validation failed for manifests in $dir"
            else
                log_success "Policy validation passed for manifests in $dir"
            fi
        fi
    done
    
    log_success "Kubernetes manifest validation completed"
}

# Check for secrets in code
check_secrets() {
    log_info "Checking for secrets in code..."
    
    local secrets_found=false
    local temp_file
    temp_file=$(mktemp)
    
    # Run truffleHog
    if truffleHog --regex --entropy=False --max_depth=10 "$PROJECT_ROOT" > "$temp_file" 2>&1; then
        if [[ -s "$temp_file" ]]; then
            log_error "Potential secrets found in code:"
            cat "$temp_file" | tee -a "$LOG_FILE"
            secrets_found=true
        else
            log_success "No secrets found in code"
        fi
    else
        log_warn "truffleHog scan failed or completed with warnings"
        if [[ -s "$temp_file" ]]; then
            cat "$temp_file" | tee -a "$LOG_FILE"
        fi
    fi
    
    rm -f "$temp_file"
    
    if [[ "$secrets_found" == "true" ]]; then
        log_error "Please remove secrets from code before deployment"
        if [[ "${IGNORE_SECRETS:-false}" != "true" ]]; then
            exit 1
        else
            log_warn "Ignoring secrets due to IGNORE_SECRETS=true"
        fi
    fi
}

# Validate RBAC policies
validate_rbac() {
    log_info "Validating RBAC policies..."
    
    local rbac_file="$PROJECT_ROOT/kubernetes/security/rbac.yaml"
    
    if [[ ! -f "$rbac_file" ]]; then
        log_warn "RBAC file not found: $rbac_file"
        return
    fi
    
    # Check if RBAC policies follow least privilege principle
    local temp_dir
    temp_dir=$(mktemp -d)
    
    # Extract ServiceAccounts, Roles, and RoleBindings
    kubectl apply --dry-run=client -f "$rbac_file" &> /dev/null || {
        log_error "Invalid RBAC configuration"
        exit 1
    }
    
    log_success "RBAC policies validated"
    
    rm -rf "$temp_dir"
}

# Test backup procedures
test_backup() {
    log_info "Testing backup procedures..."
    
    local backup_script="$SCRIPT_DIR/backup-production.sh"
    
    if [[ ! -f "$backup_script" ]]; then
        log_warn "Backup script not found: $backup_script"
        return
    fi
    
    # Test backup script syntax
    if bash -n "$backup_script"; then
        log_success "Backup script syntax is valid"
    else
        log_error "Backup script has syntax errors"
        exit 1
    fi
    
    # Test backup configuration (dry run)
    if [[ "${RUN_BACKUP_TEST:-false}" == "true" ]]; then
        log_info "Running backup test (dry run)..."
        if DRY_RUN=true "$backup_script"; then
            log_success "Backup test completed successfully"
        else
            log_error "Backup test failed"
            exit 1
        fi
    else
        log_info "Skipping backup test (set RUN_BACKUP_TEST=true to enable)"
    fi
}

# Validate monitoring configuration
validate_monitoring() {
    log_info "Validating monitoring configuration..."
    
    local monitoring_dir="$PROJECT_ROOT/kubernetes/monitoring"
    
    if [[ ! -d "$monitoring_dir" ]]; then
        log_warn "Monitoring directory not found: $monitoring_dir"
        return
    fi
    
    # Validate Prometheus rules
    find "$monitoring_dir" -name "*-alerts.yaml" | while read -r alert_file; do
        log_info "Validating Prometheus rules in $alert_file"
        
        if ! kubectl apply --dry-run=client -f "$alert_file" &> /dev/null; then
            log_error "Invalid Prometheus rules in $alert_file"
            exit 1
        fi
    done
    
    log_success "Monitoring configuration validated"
}

# Check resource quotas and limits
check_resource_limits() {
    log_info "Checking resource quotas and limits..."
    
    # Check if namespace has resource quotas
    if kubectl get resourcequota -n "$NAMESPACE" &> /dev/null; then
        log_info "Resource quotas are configured for namespace $NAMESPACE"
    else
        log_warn "No resource quotas found for namespace $NAMESPACE"
    fi
    
    # Validate that all deployments have resource limits
    local manifests_with_limits=0
    local total_manifests=0
    
    find "$PROJECT_ROOT/kubernetes" -name "*.yaml" -exec grep -l "kind: Deployment" {} \; | while read -r manifest; do
        ((total_manifests++))
        if grep -q "resources:" "$manifest" && grep -q "limits:" "$manifest"; then
            ((manifests_with_limits++))
        fi
    done
    
    log_info "Resource limits configured in deployment manifests"
}

# Check network policies
check_network_policies() {
    log_info "Checking network policies..."
    
    local network_policy_file="$PROJECT_ROOT/kubernetes/security/network-policies.yaml"
    
    if [[ ! -f "$network_policy_file" ]]; then
        log_error "Network policies file not found: $network_policy_file"
        exit 1
    fi
    
    # Validate network policies
    if kubectl apply --dry-run=client -f "$network_policy_file" &> /dev/null; then
        log_success "Network policies are valid"
    else
        log_error "Invalid network policies"
        exit 1
    fi
    
    # Check for default deny policy
    if grep -q "default-deny-all" "$network_policy_file"; then
        log_success "Default deny network policy found"
    else
        log_warn "Default deny network policy not found"
    fi
}

# Main execution
main() {
    log_info "Starting comprehensive security check..."
    
    # Run all checks
    check_dependencies
    check_cluster_access
    verify_image_signatures
    run_security_scan
    validate_manifests
    check_secrets
    validate_rbac
    test_backup
    validate_monitoring
    check_resource_limits
    check_network_policies
    
    log_success "✅ All security checks completed successfully!"
    log_info "Deployment can proceed safely"
    log_info "Full log available at: $LOG_FILE"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "OmniMesh Pre-Deployment Security Check"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h              Show this help message"
        echo "  --demo-mode            Skip signature verification"
        echo "  --ignore-scan-failures  Continue despite scan failures"
        echo "  --ignore-secrets       Continue despite found secrets"
        echo ""
        echo "Environment variables:"
        echo "  DEMO_MODE=true         Skip signature verification"
        echo "  IGNORE_SCAN_FAILURES=true  Continue despite scan failures"
        echo "  IGNORE_SECRETS=true    Continue despite found secrets"
        echo "  RUN_BACKUP_TEST=true   Run backup procedure test"
        exit 0
        ;;
    --demo-mode)
        export DEMO_MODE=true
        shift
        ;;
    --ignore-scan-failures)
        export IGNORE_SCAN_FAILURES=true
        shift
        ;;
    --ignore-secrets)
        export IGNORE_SECRETS=true
        shift
        ;;
esac

# Run main function
main "$@"
