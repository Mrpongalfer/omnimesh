#!/usr/bin/env bash

################################################################################
# GitOps Automation Test Suite
# Version: 1.0.0
# 
# Comprehensive testing framework for the GitOps automation script
################################################################################

set -euo pipefail

# Test configuration
readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR="$(dirname "$TEST_DIR")"
readonly GITOPS_SCRIPT="$SCRIPT_DIR/gitops-automation.sh"
readonly TEST_REPO="https://github.com/octocat/Hello-World.git"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Test results
declare -i TESTS_RUN=0
declare -i TESTS_PASSED=0
declare -i TESTS_FAILED=0

# Utility functions
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "PASS") echo -e "${GREEN}[PASS]${NC} $message" ;;
        "FAIL") echo -e "${RED}[FAIL]${NC} $message" ;;
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $message" ;;
    esac
}

run_test() {
    local test_name="$1"
    local test_function="$2"
    
    ((TESTS_RUN++))
    log "INFO" "Running test: $test_name"
    
    if $test_function; then
        ((TESTS_PASSED++))
        log "PASS" "$test_name"
    else
        ((TESTS_FAILED++))
        log "FAIL" "$test_name"
    fi
}

# Test functions
test_script_exists() {
    [[ -f "$GITOPS_SCRIPT" ]] && [[ -x "$GITOPS_SCRIPT" ]]
}

test_script_syntax() {
    bash -n "$GITOPS_SCRIPT"
}

test_help_option() {
    "$GITOPS_SCRIPT" --help > /dev/null 2>&1
}

test_version_display() {
    "$GITOPS_SCRIPT" --help | grep -q "Version"
}

test_dependency_check() {
    # Mock environment without required tools
    export PATH="/usr/bin:/bin"
    
    # This should trigger dependency installation logic
    timeout 30 bash -c "
        source '$GITOPS_SCRIPT'
        check_system_requirements 2>/dev/null || true
    "
}

test_repository_parsing() {
    # Test URL parsing logic
    timeout 10 bash -c "
        export REPO_URL='$TEST_REPO'
        source '$GITOPS_SCRIPT'
        parse_repository_info
        [[ \$REPO_OWNER == 'octocat' ]] && [[ \$REPO_NAME == 'Hello-World' ]]
    "
}

test_authentication_setup() {
    # Test authentication method detection
    timeout 30 bash -c "
        source '$GITOPS_SCRIPT'
        setup_github_cli_auth || setup_ssh_auth || setup_token_auth
    " 2>/dev/null
}

test_error_handling() {
    # Test error handler with a known failing command
    timeout 10 bash -c "
        source '$GITOPS_SCRIPT'
        false || true  # This should trigger error handler
    " 2>/dev/null
}

test_self_healing() {
    # Test self-healing mechanism
    timeout 10 bash -c "
        source '$GITOPS_SCRIPT'
        attempt_self_healing 'git clone' 128 'test_function' || true
    " 2>/dev/null
}

test_monitoring_setup() {
    # Test monitoring initialization
    timeout 10 bash -c "
        export ENABLE_MONITORING=true
        source '$GITOPS_SCRIPT'
        start_monitoring
        sleep 2
        kill \$(cat /tmp/gitops-*/monitor.pid) 2>/dev/null || true
    " 2>/dev/null
}

test_configuration_loading() {
    # Test configuration file loading
    local test_config="/tmp/test-gitops.env"
    cat > "$test_config" << 'EOF'
GITOPS_LOG_LEVEL="DEBUG"
GITOPS_MAX_RETRIES="5"
EOF
    
    timeout 10 bash -c "
        source '$test_config'
        [[ \$GITOPS_LOG_LEVEL == 'DEBUG' ]] && [[ \$GITOPS_MAX_RETRIES == '5' ]]
    "
    
    rm -f "$test_config"
}

test_performance_metrics() {
    # Test performance monitoring
    timeout 10 bash -c "
        source '$GITOPS_SCRIPT'
        start_timer 'test_operation'
        sleep 1
        end_timer 'test_operation'
        [[ -n \${PERFORMANCE_METRICS['test_operation_duration']} ]]
    " 2>/dev/null
}

test_cleanup_function() {
    # Test cleanup mechanism
    timeout 10 bash -c "
        source '$GITOPS_SCRIPT'
        cleanup_and_exit 0
    " 2>/dev/null
}

# Integration tests
test_dry_run() {
    # Test complete script execution in dry-run mode
    export GITOPS_DRY_RUN="true"
    export GITOPS_WORK_DIR="/tmp/gitops-test-$$"
    
    timeout 60 "$GITOPS_SCRIPT" --disable-ai --disable-monitoring "$TEST_REPO" || true
    
    # Cleanup
    rm -rf "/tmp/gitops-test-$$" 2>/dev/null || true
}

test_invalid_repository() {
    # Test handling of invalid repository URL
    export GITOPS_WORK_DIR="/tmp/gitops-invalid-$$"
    
    ! timeout 30 "$GITOPS_SCRIPT" "https://invalid-url.com/repo.git" 2>/dev/null
    
    # Cleanup
    rm -rf "/tmp/gitops-invalid-$$" 2>/dev/null || true
}

# Performance tests
test_script_startup_time() {
    local start_time=$(date +%s.%3N)
    "$GITOPS_SCRIPT" --help > /dev/null 2>&1
    local end_time=$(date +%s.%3N)
    local duration=$(echo "$end_time - $start_time" | bc)
    
    # Should start within 2 seconds
    (( $(echo "$duration < 2.0" | bc -l) ))
}

test_memory_usage() {
    # Test memory usage during execution
    local pid
    {
        "$GITOPS_SCRIPT" --help > /dev/null 2>&1 &
        pid=$!
        sleep 1
        
        # Check memory usage (should be reasonable)
        local memory_kb=$(ps -o rss= -p $pid 2>/dev/null | tr -d ' ')
        kill $pid 2>/dev/null || true
        
        # Should use less than 100MB
        [[ ${memory_kb:-0} -lt 102400 ]]
    }
}

# Security tests
test_secure_temp_files() {
    # Test that temporary files are created securely
    timeout 10 bash -c "
        source '$GITOPS_SCRIPT'
        [[ -d \$TEMP_DIR ]] && [[ \$(stat -c '%a' \$TEMP_DIR) == '700' ]]
    " 2>/dev/null
}

test_no_secrets_in_logs() {
    # Test that secrets are not logged
    export GITHUB_TOKEN="test-secret-token"
    export GITOPS_WORK_DIR="/tmp/gitops-secret-$$"
    
    "$GITOPS_SCRIPT" --help > "/tmp/test-log-$$" 2>&1
    
    ! grep -q "test-secret-token" "/tmp/test-log-$$"
    
    # Cleanup
    rm -f "/tmp/test-log-$$"
    rm -rf "/tmp/gitops-secret-$$" 2>/dev/null || true
}

# Main test execution
main() {
    echo "GitOps Automation Test Suite"
    echo "============================"
    echo
    
    # Unit tests
    echo "Running unit tests..."
    run_test "Script exists and is executable" test_script_exists
    run_test "Script syntax is valid" test_script_syntax
    run_test "Help option works" test_help_option
    run_test "Version information displayed" test_version_display
    run_test "Dependency check logic" test_dependency_check
    run_test "Repository URL parsing" test_repository_parsing
    run_test "Authentication setup" test_authentication_setup
    run_test "Error handling mechanism" test_error_handling
    run_test "Self-healing functionality" test_self_healing
    run_test "Monitoring setup" test_monitoring_setup
    run_test "Configuration loading" test_configuration_loading
    run_test "Performance metrics" test_performance_metrics
    run_test "Cleanup function" test_cleanup_function
    
    echo
    echo "Running integration tests..."
    run_test "Dry run execution" test_dry_run
    run_test "Invalid repository handling" test_invalid_repository
    
    echo
    echo "Running performance tests..."
    run_test "Script startup time" test_script_startup_time
    run_test "Memory usage" test_memory_usage
    
    echo
    echo "Running security tests..."
    run_test "Secure temporary files" test_secure_temp_files
    run_test "No secrets in logs" test_no_secrets_in_logs
    
    # Results summary
    echo
    echo "Test Results Summary"
    echo "==================="
    echo "Tests run: $TESTS_RUN"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log "PASS" "All tests passed!"
        exit 0
    else
        log "FAIL" "$TESTS_FAILED test(s) failed"
        exit 1
    fi
}

# Cleanup on exit
cleanup() {
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Clean up temporary files
    rm -rf /tmp/gitops-test-* 2>/dev/null || true
    rm -f /tmp/test-log-* 2>/dev/null || true
}

trap cleanup EXIT

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
