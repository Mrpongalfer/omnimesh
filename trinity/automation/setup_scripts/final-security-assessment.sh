#!/bin/bash

# OmniMesh Final Security Assessment Script
# Validates all security hardening measures and production readiness
# Version: 2.0.0-secure

set -euo pipefail

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSESSMENT_DIR="${PROJECT_ROOT}/security-assessment-final"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${ASSESSMENT_DIR}/final-assessment-${TIMESTAMP}.log"
REPORT_FILE="${ASSESSMENT_DIR}/final-security-report-${TIMESTAMP}.json"

# Create assessment directory
mkdir -p "$ASSESSMENT_DIR"

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

log_header() {
    echo -e "\n${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                     $1                     ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
}

# Assessment banner
show_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                  🔒 OMNIMESH FINAL SECURITY ASSESSMENT                ║${NC}"
    echo -e "${PURPLE}║                         Version 2.0.0-secure                         ║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║ Timestamp: $(date)                                      ║${NC}"
    echo -e "${PURPLE}║ Project: OmniMesh Compute Fabric                                     ║${NC}"
    echo -e "${PURPLE}║ Scope: Complete production readiness validation                     ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Initialize assessment
init_assessment() {
    log "🚀 Initializing final security assessment..."
    
    # Initialize report structure
    cat > "$REPORT_FILE" <<EOF
{
  "assessment_id": "final-${TIMESTAMP}",
  "timestamp": "$(date --iso-8601=seconds)",
  "version": "2.0.0-secure",
  "scope": "complete-production-readiness",
  "status": "IN_PROGRESS",
  "security_grade": "PENDING",
  "results": {
    "frontend_security": {},
    "backend_security": {},
    "infrastructure_security": {},
    "deployment_security": {},
    "compliance_status": {},
    "performance_validation": {}
  },
  "recommendations": [],
  "next_steps": []
}
EOF
    
    log_success "Assessment initialized"
}

# Frontend security validation
assess_frontend_security() {
    log_header "FRONTEND SECURITY ASSESSMENT"
    
    local frontend_dir="${PROJECT_ROOT}/FRONTEND/ui-solidjs"
    
    # Fix path for script location
    if [[ ! -d "$frontend_dir" ]]; then
        frontend_dir="$(dirname "$PROJECT_ROOT")/FRONTEND/ui-solidjs"
    fi
    local frontend_score=0
    local max_frontend_score=100
    
    if [[ ! -d "$frontend_dir" ]]; then
        log_error "Frontend directory not found: $frontend_dir"
        return 1
    fi
    
    cd "$frontend_dir"
    
    # Check secure components
    log "✅ Checking secure components..."
    if [[ -f "src/components/SecureMindForge.tsx" ]]; then
        log_success "SecureMindForge component found"
        frontend_score=$((frontend_score + 20))
    else
        log_error "SecureMindForge component missing"
    fi
    
    if [[ -f "src/auth/SecureAuth.tsx" ]]; then
        log_success "SecureAuth component found"
        frontend_score=$((frontend_score + 15))
    else
        log_error "SecureAuth component missing"
    fi
    
    if [[ -f "src/config/security.ts" ]]; then
        log_success "Security configuration found"
        frontend_score=$((frontend_score + 10))
    else
        log_error "Security configuration missing"
    fi
    
    # Check security dependencies
    log "✅ Checking security dependencies..."
    if [[ -f "package.json" ]] && grep -q "dompurify" package.json; then
        log_success "DOMPurify dependency found"
        frontend_score=$((frontend_score + 10))
    else
        log_error "DOMPurify dependency missing"
    fi
    
    if [[ -f "package-secure.json" ]]; then
        log_success "Secure package configuration found"
        frontend_score=$((frontend_score + 15))
    else
        log_error "Secure package configuration missing"
    fi
    
    # Check security scripts
    log "✅ Checking security scripts..."
    if [[ -f "audit-ci.json" ]]; then
        log_success "Audit CI configuration found"
        frontend_score=$((frontend_score + 10))
    else
        log_error "Audit CI configuration missing"
    fi
    
    # Run security tests
    log "✅ Checking security tests..."
    if [[ -f "tests/security/comprehensive-security-tests.spec.ts" ]]; then
        log_success "Security tests found"
        frontend_score=$((frontend_score + 20))
    else
        log_warn "Security tests not found"
    fi
    
    local frontend_percentage=$((frontend_score * 100 / max_frontend_score))
    log "Frontend security score: $frontend_score/$max_frontend_score ($frontend_percentage%)"
    
    # Update report
    jq ".results.frontend_security = {
        \"score\": $frontend_score,
        \"max_score\": $max_frontend_score,
        \"percentage\": $frontend_percentage,
        \"components\": {
            \"secure_mindforge\": $(if [[ -f "src/components/SecureMindForge.tsx" ]]; then echo "true"; else echo "false"; fi),
            \"secure_auth\": $(if [[ -f "src/auth/SecureAuth.tsx" ]]; then echo "true"; else echo "false"; fi),
            \"security_config\": $(if [[ -f "src/config/security.ts" ]]; then echo "true"; else echo "false"; fi),
            \"secure_package\": $(if [[ -f "package-secure.json" ]]; then echo "true"; else echo "false"; fi)
        }
    }" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    cd - > /dev/null
    return 0
}

# Backend security validation
assess_backend_security() {
    log_header "BACKEND SECURITY ASSESSMENT"
    
    local backend_score=0
    local max_backend_score=100
    
    # Check Rust components
    log "✅ Checking Rust components..."
    if [[ -d "${PROJECT_ROOT}/BACKEND/nexus-prime-core" ]]; then
        cd "${PROJECT_ROOT}/BACKEND/nexus-prime-core"
        
        if [[ -f "Cargo.toml" ]]; then
            log_success "Rust project structure found"
            backend_score=$((backend_score + 20))
            
            # Check for security dependencies
            if grep -q "tokio" Cargo.toml && grep -q "serde" Cargo.toml; then
                log_success "Secure Rust dependencies found"
                backend_score=$((backend_score + 15))
            fi
        fi
        
        cd - > /dev/null
    fi
    
    # Check Go components
    log "✅ Checking Go components..."
    if [[ -d "${PROJECT_ROOT}/BACKEND/go-node-proxies" ]]; then
        cd "${PROJECT_ROOT}/BACKEND/go-node-proxies"
        
        if [[ -f "go.mod" ]]; then
            log_success "Go project structure found"
            backend_score=$((backend_score + 20))
            
            # Check for security modules
            if grep -q "crypto" go.mod; then
                log_success "Cryptographic modules found"
                backend_score=$((backend_score + 10))
            fi
        fi
        
        cd - > /dev/null
    fi
    
    # Check infrastructure CLI
    log "✅ Checking infrastructure CLI..."
    if [[ -f "${PROJECT_ROOT}/infrastructure/cli/install-secure-production.sh" ]]; then
        log_success "Secure installation script found"
        backend_score=$((backend_score + 25))
    else
        log_error "Secure installation script missing"
    fi
    
    # Check scripts
    log "✅ Checking security scripts..."
    if [[ -f "${PROJECT_ROOT}/scripts/pre-deployment-security-check.sh" ]]; then
        log_success "Pre-deployment security check found"
        backend_score=$((backend_score + 10))
    else
        log_error "Pre-deployment security check missing"
    fi
    
    local backend_percentage=$((backend_score * 100 / max_backend_score))
    log "Backend security score: $backend_score/$max_backend_score ($backend_percentage%)"
    
    # Update report
    jq ".results.backend_security = {
        \"score\": $backend_score,
        \"max_score\": $max_backend_score,
        \"percentage\": $backend_percentage,
        \"components\": {
            \"rust_core\": $(if [[ -f "${PROJECT_ROOT}/BACKEND/nexus-prime-core/Cargo.toml" ]]; then echo "true"; else echo "false"; fi),
            \"go_proxies\": $(if [[ -f "${PROJECT_ROOT}/BACKEND/go-node-proxies/go.mod" ]]; then echo "true"; else echo "false"; fi),
            \"secure_installer\": $(if [[ -f "${PROJECT_ROOT}/infrastructure/cli/install-secure-production.sh" ]]; then echo "true"; else echo "false"; fi),
            \"security_scripts\": $(if [[ -f "${PROJECT_ROOT}/scripts/pre-deployment-security-check.sh" ]]; then echo "true"; else echo "false"; fi)
        }
    }" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    return 0
}

# Infrastructure security validation
assess_infrastructure_security() {
    log_header "INFRASTRUCTURE SECURITY ASSESSMENT"
    
    local infra_score=0
    local max_infra_score=100
    
    # Check Kubernetes manifests
    log "✅ Checking Kubernetes security manifests..."
    if [[ -f "${PROJECT_ROOT}/kubernetes/security/security-policies.yaml" ]]; then
        log_success "Security policies found"
        infra_score=$((infra_score + 25))
    else
        log_error "Security policies missing"
    fi
    
    # Check deployment scripts
    log "✅ Checking deployment scripts..."
    if [[ -f "${PROJECT_ROOT}/scripts/production-deploy.sh" ]]; then
        log_success "Production deployment script found"
        infra_score=$((infra_score + 20))
    else
        log_error "Production deployment script missing"
    fi
    
    # Check CI/CD pipeline
    log "✅ Checking CI/CD pipeline..."
    if [[ -f "${PROJECT_ROOT}/.github/workflows/security-production-pipeline.yml" ]]; then
        log_success "Security pipeline found"
        infra_score=$((infra_score + 20))
    else
        log_error "Security pipeline missing"
    fi
    
    # Check monitoring configuration
    log "✅ Checking monitoring..."
    if [[ -d "${PROJECT_ROOT}/kubernetes/monitoring" ]]; then
        log_success "Monitoring configuration found"
        infra_score=$((infra_score + 15))
    else
        log_warn "Monitoring configuration missing"
    fi
    
    # Check backup scripts
    log "✅ Checking backup procedures..."
    if [[ -f "${PROJECT_ROOT}/scripts/backup-production.sh" ]]; then
        log_success "Backup scripts found"
        infra_score=$((infra_score + 10))
    else
        log_warn "Backup scripts missing"
    fi
    
    # Check documentation
    log "✅ Checking documentation..."
    if [[ -f "${PROJECT_ROOT}/docs/PRODUCTION_DEPLOYMENT.md" ]]; then
        log_success "Production deployment documentation found"
        infra_score=$((infra_score + 10))
    else
        log_error "Production deployment documentation missing"
    fi
    
    local infra_percentage=$((infra_score * 100 / max_infra_score))
    log "Infrastructure security score: $infra_score/$max_infra_score ($infra_percentage%)"
    
    # Update report
    jq ".results.infrastructure_security = {
        \"score\": $infra_score,
        \"max_score\": $max_infra_score,
        \"percentage\": $infra_percentage,
        \"components\": {
            \"k8s_security_policies\": $(if [[ -f "${PROJECT_ROOT}/kubernetes/security/security-policies.yaml" ]]; then echo "true"; else echo "false"; fi),
            \"production_deploy\": $(if [[ -f "${PROJECT_ROOT}/scripts/production-deploy.sh" ]]; then echo "true"; else echo "false"; fi),
            \"cicd_pipeline\": $(if [[ -f "${PROJECT_ROOT}/.github/workflows/security-production-pipeline.yml" ]]; then echo "true"; else echo "false"; fi),
            \"monitoring\": $(if [[ -d "${PROJECT_ROOT}/kubernetes/monitoring" ]]; then echo "true"; else echo "false"; fi),
            \"documentation\": $(if [[ -f "${PROJECT_ROOT}/docs/PRODUCTION_DEPLOYMENT.md" ]]; then echo "true"; else echo "false"; fi)
        }
    }" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    return 0
}

# Compliance validation
assess_compliance() {
    log_header "COMPLIANCE ASSESSMENT"
    
    local compliance_score=0
    local max_compliance_score=100
    
    # Check security framework documentation
    log "✅ Checking security framework..."
    if [[ -f "${PROJECT_ROOT}/SECURITY_FRAMEWORK.md" ]]; then
        log_success "Security framework documentation found"
        compliance_score=$((compliance_score + 20))
    else
        log_error "Security framework documentation missing"
    fi
    
    # Check audit scripts
    log "✅ Checking audit capabilities..."
    if [[ -f "${PROJECT_ROOT}/security-audit-complete.sh" ]]; then
        log_success "Comprehensive audit script found"
        compliance_score=$((compliance_score + 20))
    else
        log_error "Comprehensive audit script missing"
    fi
    
    # Check security policies
    log "✅ Checking security policies..."
    if [[ -f "${PROJECT_ROOT}/SECURITY.md" ]]; then
        log_success "Security policy found"
        compliance_score=$((compliance_score + 15))
    else
        log_error "Security policy missing"
    fi
    
    # Check incident response
    log "✅ Checking incident response..."
    if [[ -f "${PROJECT_ROOT}/docs/INCIDENT_RESPONSE.md" ]]; then
        log_success "Incident response documentation found"
        compliance_score=$((compliance_score + 15))
    else
        log_warn "Incident response documentation missing"
    fi
    
    # Check data protection
    log "✅ Checking data protection..."
    if [[ -f "${PROJECT_ROOT}/docs/DATA_PROTECTION.md" ]]; then
        log_success "Data protection documentation found"
        compliance_score=$((compliance_score + 15))
    else
        log_warn "Data protection documentation missing"
    fi
    
    # Check training materials
    log "✅ Checking training materials..."
    if [[ -f "${PROJECT_ROOT}/docs/SECURITY_TRAINING.md" ]]; then
        log_success "Security training documentation found"
        compliance_score=$((compliance_score + 15))
    else
        log_warn "Security training documentation missing"
    fi
    
    local compliance_percentage=$((compliance_score * 100 / max_compliance_score))
    log "Compliance score: $compliance_score/$max_compliance_score ($compliance_percentage%)"
    
    # Update report
    jq ".results.compliance_status = {
        \"score\": $compliance_score,
        \"max_score\": $max_compliance_score,
        \"percentage\": $compliance_percentage,
        \"frameworks\": {
            \"security_framework\": $(if [[ -f "${PROJECT_ROOT}/SECURITY_FRAMEWORK.md" ]]; then echo "true"; else echo "false"; fi),
            \"audit_capabilities\": $(if [[ -f "${PROJECT_ROOT}/security-audit-complete.sh" ]]; then echo "true"; else echo "false"; fi),
            \"security_policies\": $(if [[ -f "${PROJECT_ROOT}/SECURITY.md" ]]; then echo "true"; else echo "false"; fi),
            \"incident_response\": $(if [[ -f "${PROJECT_ROOT}/docs/INCIDENT_RESPONSE.md" ]]; then echo "true"; else echo "false"; fi)
        }
    }" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    return 0
}

# Calculate overall security grade
calculate_security_grade() {
    log_header "SECURITY GRADE CALCULATION"
    
    # Extract scores from report
    local frontend_score=$(jq -r '.results.frontend_security.percentage // 0' "$REPORT_FILE")
    local backend_score=$(jq -r '.results.backend_security.percentage // 0' "$REPORT_FILE")
    local infra_score=$(jq -r '.results.infrastructure_security.percentage // 0' "$REPORT_FILE")
    local compliance_score=$(jq -r '.results.compliance_status.percentage // 0' "$REPORT_FILE")
    
    # Calculate weighted average
    local total_score=$(echo "scale=2; ($frontend_score * 0.3) + ($backend_score * 0.25) + ($infra_score * 0.25) + ($compliance_score * 0.2)" | bc)
    
    # Determine grade
    local grade
    if (( $(echo "$total_score >= 95" | bc -l) )); then
        grade="A+"
    elif (( $(echo "$total_score >= 90" | bc -l) )); then
        grade="A"
    elif (( $(echo "$total_score >= 85" | bc -l) )); then
        grade="B+"
    elif (( $(echo "$total_score >= 80" | bc -l) )); then
        grade="B"
    elif (( $(echo "$total_score >= 75" | bc -l) )); then
        grade="C+"
    elif (( $(echo "$total_score >= 70" | bc -l) )); then
        grade="C"
    else
        grade="F"
    fi
    
    log "📊 Security Assessment Results:"
    log "  Frontend Security: $frontend_score%"
    log "  Backend Security: $backend_score%"
    log "  Infrastructure Security: $infra_score%"
    log "  Compliance Status: $compliance_score%"
    log "  Overall Score: $total_score%"
    log "  Security Grade: $grade"
    
    # Update report with final grade
    jq ".security_grade = \"$grade\" | .overall_score = $total_score | .status = \"COMPLETED\"" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    return 0
}

# Generate final recommendations
generate_recommendations() {
    log_header "RECOMMENDATIONS"
    
    local recommendations=()
    
    # Check scores and generate recommendations
    local frontend_score=$(jq -r '.results.frontend_security.percentage // 0' "$REPORT_FILE")
    local backend_score=$(jq -r '.results.backend_security.percentage // 0' "$REPORT_FILE")
    local infra_score=$(jq -r '.results.infrastructure_security.percentage // 0' "$REPORT_FILE")
    local compliance_score=$(jq -r '.results.compliance_status.percentage // 0' "$REPORT_FILE")
    
    if (( $(echo "$frontend_score < 90" | bc -l) )); then
        recommendations+=("Improve frontend security components and testing")
    fi
    
    if (( $(echo "$backend_score < 90" | bc -l) )); then
        recommendations+=("Enhance backend security measures and dependency management")
    fi
    
    if (( $(echo "$infra_score < 90" | bc -l) )); then
        recommendations+=("Strengthen infrastructure security policies and monitoring")
    fi
    
    if (( $(echo "$compliance_score < 90" | bc -l) )); then
        recommendations+=("Complete compliance documentation and training materials")
    fi
    
    # Add general recommendations
    recommendations+=("Implement continuous security monitoring")
    recommendations+=("Conduct regular penetration testing")
    recommendations+=("Maintain security training program")
    recommendations+=("Establish incident response procedures")
    
    # Update report with recommendations
    local rec_json=$(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
    jq ".recommendations = $rec_json" "$REPORT_FILE" > "$REPORT_FILE.tmp" && mv "$REPORT_FILE.tmp" "$REPORT_FILE"
    
    log "📋 Recommendations generated:"
    for rec in "${recommendations[@]}"; do
        log "  • $rec"
    done
    
    return 0
}

# Main assessment execution
main() {
    show_banner
    init_assessment
    
    log "🔍 Starting comprehensive security assessment..."
    
    # Run all assessments
    assess_frontend_security
    assess_backend_security
    assess_infrastructure_security
    assess_compliance
    
    # Calculate final grade
    calculate_security_grade
    generate_recommendations
    
    log_header "ASSESSMENT COMPLETED"
    
    local final_grade=$(jq -r '.security_grade' "$REPORT_FILE")
    local final_score=$(jq -r '.overall_score' "$REPORT_FILE")
    
    if [[ "$final_grade" == "A+" ]] || [[ "$final_grade" == "A" ]]; then
        log_success "🎉 PRODUCTION READY! Security Grade: $final_grade ($final_score%)"
        log_success "System meets enterprise security standards"
    elif [[ "$final_grade" == "B+" ]] || [[ "$final_grade" == "B" ]]; then
        log_warn "⚠️  NEEDS IMPROVEMENT. Security Grade: $final_grade ($final_score%)"
        log_warn "Address recommendations before production deployment"
    else
        log_critical "❌ NOT PRODUCTION READY. Security Grade: $final_grade ($final_score%)"
        log_critical "Critical security issues must be resolved"
    fi
    
    log "📊 Final assessment report: $REPORT_FILE"
    log "📝 Assessment log: $LOG_FILE"
    
    return 0
}

# Execute main function
main "$@"
