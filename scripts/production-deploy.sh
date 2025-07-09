#!/bin/bash

# OmniMesh Production Deployment Script
# Comprehensive security-first deployment with full audit trail
# Version: 2.0.0-secure

set -euo pipefail

# Configuration
readonly SCRIPT_VERSION="2.0.0-secure"
readonly DEPLOYMENT_ENV="${1:-production}"
readonly NAMESPACE="omnimesh"
readonly TIMEOUT="600s"
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/omnimesh"
readonly BACKUP_DIR="/var/backups/omnimesh"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly DEPLOYMENT_ID="deploy_${TIMESTAMP}_$$"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Logging setup
readonly LOG_FILE="${LOG_DIR}/deployment-${TIMESTAMP}.log"
readonly AUDIT_LOG="${LOG_DIR}/audit-${TIMESTAMP}.log"

# Create log directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

log_critical() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] 🚨 CRITICAL: $1${NC}" | tee -a "$LOG_FILE"
}

log_audit() {
    local event="$1"
    local details="$2"
    local metadata="${3:-}"
    
    {
        echo "$(date --iso-8601=seconds) AUDIT [$event] $details"
        if [[ -n "$metadata" ]]; then
            echo "  Metadata: $metadata"
        fi
    } >> "$AUDIT_LOG"
}

# Deployment banner
show_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                 🚀 OmniMesh Production Deployment                 ║${NC}"
    echo -e "${PURPLE}║                         Version $SCRIPT_VERSION                         ║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║ Environment: ${DEPLOYMENT_ENV}                                           ║${NC}"
    echo -e "${PURPLE}║ Namespace: ${NAMESPACE}                                              ║${NC}"
    echo -e "${PURPLE}║ Deployment ID: ${DEPLOYMENT_ID}                        ║${NC}"
    echo -e "${PURPLE}║ Timestamp: $(date)                              ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Pre-deployment checks
pre_deployment_checks() {
    log "🔍 Running pre-deployment security checks..."
    
    # Check if kubectl is available and configured
    if ! command -v kubectl &> /dev/null; then
        log_critical "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_critical "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check required tools
    local required_tools=("helm" "docker" "git" "jq" "yq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_critical "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Run comprehensive security check
    log "Running comprehensive security audit..."
    if [[ -f "$PROJECT_ROOT/scripts/pre-deployment-security-check.sh" ]]; then
        bash "$PROJECT_ROOT/scripts/pre-deployment-security-check.sh"
    else
        log_warn "Pre-deployment security check script not found"
    fi
    
    log_success "Pre-deployment checks completed"
    log_audit "PRE_DEPLOYMENT_CHECKS" "All pre-deployment checks passed" "deployment_id=$DEPLOYMENT_ID"
}

# Create secure backup
create_backup() {
    log "📦 Creating deployment backup..."
    
    local backup_path="${BACKUP_DIR}/backup-${TIMESTAMP}"
    mkdir -p "$backup_path"
    
    # Backup current Kubernetes resources
    kubectl get all,configmaps,secrets,pvc -n "$NAMESPACE" -o yaml > "$backup_path/kubernetes-resources.yaml" 2>/dev/null || true
    
    # Backup persistent volumes
    kubectl get pv -o yaml > "$backup_path/persistent-volumes.yaml" 2>/dev/null || true
    
    # Backup ArgoCD applications
    kubectl get applications -n argocd -o yaml > "$backup_path/argocd-applications.yaml" 2>/dev/null || true
    
    # Create encrypted archive
    tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "backup-${TIMESTAMP}"
    
    # Encrypt backup
    if command -v gpg &> /dev/null; then
        gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output "$backup_path.tar.gz.gpg" "$backup_path.tar.gz"
        rm "$backup_path.tar.gz"
        log_success "Encrypted backup created: $backup_path.tar.gz.gpg"
    else
        log_warn "GPG not available, backup is not encrypted"
    fi
    
    # Clean up temporary files
    rm -rf "$backup_path"
    
    log_audit "BACKUP_CREATED" "Deployment backup created" "backup_path=$backup_path.tar.gz.gpg"
}

# Deploy security policies
deploy_security_policies() {
    log "🔒 Deploying security policies..."
    
    # Create namespace with security labels
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace "$NAMESPACE" security-policy=strict --overwrite
    kubectl label namespace "$NAMESPACE" deployment-id="$DEPLOYMENT_ID" --overwrite
    
    # Apply security policies
    if [[ -d "$PROJECT_ROOT/kubernetes/security" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/security/"
        log_success "Security policies applied"
    else
        log_warn "Security policies directory not found"
    fi
    
    # Apply network policies
    if [[ -f "$PROJECT_ROOT/kubernetes/security/network-policies.yaml" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/security/network-policies.yaml"
        log_success "Network policies applied"
    fi
    
    # Apply pod security policies
    if [[ -f "$PROJECT_ROOT/kubernetes/security/pod-security-policies.yaml" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/security/pod-security-policies.yaml"
        log_success "Pod security policies applied"
    fi
    
    log_audit "SECURITY_POLICIES_DEPLOYED" "Security policies applied to namespace" "namespace=$NAMESPACE"
}

# Deploy infrastructure
deploy_infrastructure() {
    log "🏗️  Deploying infrastructure components..."
    
    # Deploy infrastructure components
    if [[ -d "$PROJECT_ROOT/kubernetes/infrastructure" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/infrastructure/"
        log_success "Infrastructure components deployed"
    fi
    
    # Deploy monitoring
    if [[ -d "$PROJECT_ROOT/kubernetes/monitoring" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/monitoring/"
        log_success "Monitoring components deployed"
    fi
    
    # Deploy logging
    if [[ -d "$PROJECT_ROOT/kubernetes/logging" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/logging/"
        log_success "Logging components deployed"
    fi
    
    log_audit "INFRASTRUCTURE_DEPLOYED" "Infrastructure components deployed" "namespace=$NAMESPACE"
}

# Deploy applications
deploy_applications() {
    log "🚀 Deploying applications..."
    
    # Deploy with ArgoCD if available
    if [[ -d "$PROJECT_ROOT/kubernetes/argocd/applications" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/argocd/applications/"
        log_success "ArgoCD applications deployed"
    elif [[ -d "$PROJECT_ROOT/kubernetes/applications" ]]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/applications/"
        log_success "Applications deployed directly"
    else
        log_warn "No application manifests found"
    fi
    
    log_audit "APPLICATIONS_DEPLOYED" "Applications deployed" "namespace=$NAMESPACE"
}

# Wait for deployment completion
wait_for_deployment() {
    log "⏳ Waiting for deployment to complete..."
    
    # Wait for core deployments
    local deployments=(
        "omnimesh-core"
        "omnimesh-ui"
        "omnimesh-api"
        "omnimesh-gateway"
    )
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &> /dev/null; then
            log "Waiting for deployment: $deployment"
            kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="$TIMEOUT" || {
                log_error "Deployment failed: $deployment"
                return 1
            }
        else
            log_warn "Deployment not found: $deployment"
        fi
    done
    
    log_success "All deployments completed successfully"
}

# Post-deployment validation
post_deployment_validation() {
    log "🔍 Running post-deployment validation..."
    
    # Check pod status
    local failed_pods
    failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o name | wc -l)
    
    if [[ $failed_pods -gt 0 ]]; then
        log_error "Found $failed_pods failed pods"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed
        return 1
    fi
    
    # Check service endpoints
    local services
    services=$(kubectl get services -n "$NAMESPACE" -o json | jq -r '.items[].metadata.name')
    
    for service in $services; do
        local endpoints
        endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o json | jq -r '.subsets[].addresses[]?.ip' | wc -l)
        
        if [[ $endpoints -eq 0 ]]; then
            log_warn "Service $service has no endpoints"
        else
            log "Service $service has $endpoints endpoints"
        fi
    done
    
    # Run health checks
    if [[ -f "$PROJECT_ROOT/scripts/health-check.sh" ]]; then
        bash "$PROJECT_ROOT/scripts/health-check.sh"
    fi
    
    log_success "Post-deployment validation completed"
    log_audit "POST_DEPLOYMENT_VALIDATION" "Post-deployment validation completed" "namespace=$NAMESPACE"
}

# Security posture check
security_posture_check() {
    log "🛡️  Running security posture check..."
    
    # Check for privileged containers
    local privileged_pods
    privileged_pods=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[] | select(.spec.securityContext.privileged == true or .spec.containers[].securityContext.privileged == true) | .metadata.name' | wc -l)
    
    if [[ $privileged_pods -gt 0 ]]; then
        log_error "Found $privileged_pods privileged pods"
        return 1
    fi
    
    # Check for containers running as root
    local root_containers
    root_containers=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[] | select(.spec.securityContext.runAsUser == 0 or .spec.containers[].securityContext.runAsUser == 0) | .metadata.name' | wc -l)
    
    if [[ $root_containers -gt 0 ]]; then
        log_error "Found $root_containers containers running as root"
        return 1
    fi
    
    # Check resource limits
    local pods_without_limits
    pods_without_limits=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.name' | wc -l)
    
    if [[ $pods_without_limits -gt 0 ]]; then
        log_warn "Found $pods_without_limits pods without resource limits"
    fi
    
    log_success "Security posture check completed"
    log_audit "SECURITY_POSTURE_CHECK" "Security posture validated" "namespace=$NAMESPACE"
}

# Rollback function
rollback_deployment() {
    log_error "🔄 Initiating rollback procedure..."
    
    # Find the latest backup
    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -name "backup-*.tar.gz.gpg" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -n "$latest_backup" ]]; then
        log "Restoring from backup: $latest_backup"
        
        # Decrypt and restore backup
        if command -v gpg &> /dev/null; then
            gpg --decrypt "$latest_backup" | tar -xzf - -C "$BACKUP_DIR"
            
            # Restore Kubernetes resources
            local backup_dir="${latest_backup%.tar.gz.gpg}"
            if [[ -f "$backup_dir/kubernetes-resources.yaml" ]]; then
                kubectl apply -f "$backup_dir/kubernetes-resources.yaml"
                log_success "Kubernetes resources restored"
            fi
        else
            log_error "GPG not available for backup decryption"
        fi
    else
        log_error "No backup found for rollback"
    fi
    
    log_audit "ROLLBACK_INITIATED" "Deployment rollback initiated" "deployment_id=$DEPLOYMENT_ID"
}

# Cleanup function
cleanup() {
    log "🧹 Cleaning up temporary files..."
    
    # Remove temporary files
    find /tmp -name "omnimesh-*" -type f -mtime +1 -delete 2>/dev/null || true
    
    # Archive logs
    if [[ -f "$LOG_FILE" ]]; then
        gzip "$LOG_FILE"
        log_success "Logs archived"
    fi
    
    log_audit "CLEANUP_COMPLETED" "Deployment cleanup completed" "deployment_id=$DEPLOYMENT_ID"
}

# Main deployment function
main() {
    # Set up signal handlers
    trap rollback_deployment ERR
    trap cleanup EXIT
    
    show_banner
    
    log "🚀 Starting OmniMesh deployment to $DEPLOYMENT_ENV"
    log_audit "DEPLOYMENT_STARTED" "Deployment initiated" "environment=$DEPLOYMENT_ENV,deployment_id=$DEPLOYMENT_ID"
    
    # Deployment steps
    pre_deployment_checks
    create_backup
    deploy_security_policies
    deploy_infrastructure
    deploy_applications
    wait_for_deployment
    post_deployment_validation
    security_posture_check
    
    log_success "🎉 Deployment completed successfully!"
    log_audit "DEPLOYMENT_COMPLETED" "Deployment completed successfully" "deployment_id=$DEPLOYMENT_ID"
    
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 DEPLOYMENT SUCCESSFUL! 🎉                    ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║ Environment: ${DEPLOYMENT_ENV}                                             ║${NC}"
    echo -e "${GREEN}║ Namespace: ${NAMESPACE}                                                ║${NC}"
    echo -e "${GREEN}║ Deployment ID: ${DEPLOYMENT_ID}                          ║${NC}"
    echo -e "${GREEN}║ Log File: ${LOG_FILE}                                      ║${NC}"
    echo -e "${GREEN}║ Audit Log: ${AUDIT_LOG}                                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  ${BLUE}1.${NC} Monitor deployment: ${YELLOW}kubectl get pods -n $NAMESPACE -w${NC}"
    echo -e "  ${BLUE}2.${NC} Check logs: ${YELLOW}kubectl logs -n $NAMESPACE -l app=omnimesh${NC}"
    echo -e "  ${BLUE}3.${NC} Access application: ${YELLOW}kubectl port-forward -n $NAMESPACE svc/omnimesh-ui 8080:80${NC}"
    echo -e "  ${BLUE}4.${NC} View metrics: ${YELLOW}kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090${NC}"
    echo
}

# Execute main function
main "$@"
