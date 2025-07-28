#!/usr/bin/env bash

################################################################################
# GitOps Automation Script - Tungsten Grade
# Version: 3.0.0
# 
# Advanced Git automation with AI-driven self-healing, intelligent error
# recovery, and hyper-adaptive pipeline management for any GitHub repository.
#
# Features:
# - Zero-configuration repository detection
# - Intelligent authentication management
# - AI-powered error diagnosis and recovery
# - Dynamic workflow adaptation
# - Self-healing pipeline corrections
# - Advanced security and best practices
# - Cross-platform compatibility
# - Real-time monitoring and alerting
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# GLOBAL CONFIGURATION & CONSTANTS
# ============================================================================

# Script metadata
readonly SCRIPT_VERSION="3.0.0"
readonly SCRIPT_NAME="GitOps Automation - Tungsten Grade"
readonly SCRIPT_START_TIME=$(date +%s)
readonly SCRIPT_PID=$$

# Colors and formatting
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Symbols
readonly SUCCESS="✅"
readonly ERROR="❌"
readonly WARNING="⚠️"
readonly INFO="ℹ️"
readonly ROCKET="🚀"
readonly GEAR="⚙️"
readonly BRAIN="🧠"
readonly SHIELD="🛡️"

# ============================================================================
# UTILITY FUNCTIONS (Must be defined before configuration loading)
# ============================================================================

# Basic logging function (must be defined before config loading)
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""
    
    case "$level" in
        "ERROR")   color="$RED" ;;
        "WARN")    color="$YELLOW" ;;
        "INFO")    color="$BLUE" ;;
        "SUCCESS") color="$GREEN" ;;
        "DEBUG")   color="$PURPLE" ;;
        *)         color="$NC" ;;
    esac
    
    # Console output with colors
    echo -e "${color}[$timestamp] [$level] $message${NC}" >&2
    
    # Structured log to file (ensure directory exists)
    if [[ -d "${TEMP_DIR:-}" ]]; then
        local log_file="${LOG_FILE:-/tmp/gitops-execution.log}"
        echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$message\",\"pid\":$SCRIPT_PID}" >> "$log_file"
        
        # Error tracking
        if [[ "$level" == "ERROR" ]]; then
            local error_log="${ERROR_LOG:-/tmp/gitops-errors.log}"
            echo "$message" >> "$error_log"
            if [[ -n "${ERROR_HISTORY:-}" ]]; then
                ERROR_HISTORY["$(date +%s)"]="$message"
            fi
        fi
    fi
}

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

# Default configuration (can be overridden)
DEFAULT_REPO_URL="https://github.com/mrpongalfer/exwork-agent.git"
REPO_URL="$DEFAULT_REPO_URL"
WORK_DIR="${GITOPS_WORK_DIR:-$(pwd)}"
LOG_LEVEL="${GITOPS_LOG_LEVEL:-INFO}"
MAX_RETRIES="${GITOPS_MAX_RETRIES:-3}"
RETRY_DELAY="${GITOPS_RETRY_DELAY:-5}"
TIMEOUT="${GITOPS_TIMEOUT:-300}"
ENABLE_AI="${GITOPS_ENABLE_AI:-true}"
ENABLE_SELF_HEALING="${GITOPS_SELF_HEALING:-true}"
ENABLE_MONITORING="${GITOPS_MONITORING:-true}"
TEST_MODE="${GITOPS_TEST_MODE:-false}"

# Load configuration from .gitops.env if it exists
if [[ -f ".gitops.env" ]]; then
    log "INFO" "Loading configuration from .gitops.env"
    source .gitops.env
    # Override defaults with values from config file if they exist
    DEFAULT_REPO_URL="${GITOPS_DEFAULT_REPO:-$DEFAULT_REPO_URL}"
    WORK_DIR="${GITOPS_WORK_DIR:-$WORK_DIR}"
    LOG_LEVEL="${GITOPS_LOG_LEVEL:-$LOG_LEVEL}"
    MAX_RETRIES="${GITOPS_MAX_RETRIES:-$MAX_RETRIES}"
    RETRY_DELAY="${GITOPS_RETRY_DELAY:-$RETRY_DELAY}"
    TIMEOUT="${GITOPS_TIMEOUT:-$TIMEOUT}"
    ENABLE_AI="${GITOPS_ENABLE_AI:-$ENABLE_AI}"
    ENABLE_SELF_HEALING="${GITOPS_SELF_HEALING:-$ENABLE_SELF_HEALING}"
    ENABLE_MONITORING="${GITOPS_MONITORING:-$ENABLE_MONITORING}"
fi

# State tracking
declare -A OPERATION_STATUS
declare -A RETRY_COUNT
declare -A ERROR_HISTORY
declare -A PERFORMANCE_METRICS

# Temporary files
readonly TEMP_DIR=$(mktemp -d -t gitops-XXXXXXXXXX)
readonly LOG_FILE="${TEMP_DIR}/gitops.log"
readonly ERROR_LOG="${TEMP_DIR}/errors.log"
readonly METRICS_FILE="${TEMP_DIR}/metrics.json"
readonly STATE_FILE="${TEMP_DIR}/state.json"

# Ensure temporary files exist
touch "$LOG_FILE" "$ERROR_LOG" "$METRICS_FILE" "$STATE_FILE"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Enhanced error handler with context and recovery suggestions
error_handler() {
    local exit_code=$?
    local line_number=$1
    local command="$2"
    local function_name="${FUNCNAME[2]:-main}"
    
    log "ERROR" "Command failed in $function_name:$line_number with exit code $exit_code"
    log "ERROR" "Failed command: $command"
    
    # AI-powered error analysis if enabled
    if [[ "$ENABLE_AI" == "true" ]]; then
        analyze_and_suggest_fix "$command" "$exit_code" "$function_name"
    fi
    
    # Self-healing attempt if enabled
    if [[ "$ENABLE_SELF_HEALING" == "true" ]]; then
        attempt_self_healing "$command" "$exit_code" "$function_name"
    fi
    
    cleanup_and_exit $exit_code
}

# Trap setup for comprehensive error handling
trap 'error_handler $LINENO "$BASH_COMMAND"' ERR
trap cleanup_and_exit EXIT
trap 'log "WARN" "Script interrupted by user"; cleanup_and_exit 130' INT TERM

# Performance monitoring
start_timer() {
    local operation="$1"
    PERFORMANCE_METRICS["${operation}_start"]=$(date +%s.%3N)
}

end_timer() {
    local operation="$1"
    local start_time="${PERFORMANCE_METRICS["${operation}_start"]}"
    local end_time=$(date +%s.%3N)
    local duration=$(echo "$end_time - $start_time" | bc)
    PERFORMANCE_METRICS["${operation}_duration"]="$duration"
    log "DEBUG" "Operation '$operation' completed in ${duration}s"
}

# Retry mechanism with exponential backoff
retry_with_backoff() {
    local operation="$1"
    local max_attempts="${2:-$MAX_RETRIES}"
    shift 2
    local command=("$@")
    
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        log "INFO" "Attempting $operation (attempt $attempt/$max_attempts)"
        
        if "${command[@]}"; then
            log "SUCCESS" "$operation succeeded on attempt $attempt"
            OPERATION_STATUS["$operation"]="SUCCESS"
            return 0
        else
            local exit_code=$?
            log "WARN" "$operation failed on attempt $attempt (exit code: $exit_code)"
            RETRY_COUNT["$operation"]=$attempt
            
            if [[ $attempt -lt $max_attempts ]]; then
                local delay=$((RETRY_DELAY * attempt))
                log "INFO" "Retrying in ${delay}s..."
                sleep "$delay"
            fi
        fi
    done
    
    log "ERROR" "$operation failed after $max_attempts attempts"
    OPERATION_STATUS["$operation"]="FAILED"
    return 1
}

# System requirements check with auto-installation
check_system_requirements() {
    log "INFO" "${GEAR} Checking system requirements..."
    start_timer "system_check"
    
    local required_tools=("git" "curl" "jq" "bc")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log "WARN" "Missing required tools: ${missing_tools[*]}"
        install_missing_tools "${missing_tools[@]}"
    fi
    
    # Git configuration check
    if ! git config --global user.name &> /dev/null || ! git config --global user.email &> /dev/null; then
        log "WARN" "Git user configuration missing"
        configure_git_user
    fi
    
    end_timer "system_check"
    log "SUCCESS" "${SUCCESS} System requirements verified"
}

# Intelligent tool installation
install_missing_tools() {
    local tools=("$@")
    log "INFO" "Installing missing tools: ${tools[*]}"
    
    # Detect package manager and install
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y "${tools[@]}"
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y "${tools[@]}"
    elif command -v yum &> /dev/null; then
        sudo yum install -y "${tools[@]}"
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm "${tools[@]}"
    elif command -v brew &> /dev/null; then
        brew install "${tools[@]}"
    else
        log "ERROR" "No supported package manager found. Please install manually: ${tools[*]}"
        return 1
    fi
}

# Git user configuration with intelligent defaults
configure_git_user() {
    log "INFO" "Configuring Git user settings..."
    
    # Try to detect from GitHub CLI or SSH config
    local git_name git_email
    
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        git_name=$(gh api user --jq '.name' 2>/dev/null || echo "")
        git_email=$(gh api user --jq '.email' 2>/dev/null || echo "")
    fi
    
    # Fallback to system user
    git_name="${git_name:-${USER:-$(whoami)}}"
    git_email="${git_email:-${USER:-$(whoami)}@$(hostname)}"
    
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    
    log "SUCCESS" "Git configured: $git_name <$git_email>"
}

# ============================================================================
# AUTHENTICATION MANAGEMENT
# ============================================================================

# Multi-method authentication with fallbacks
setup_authentication() {
    log "INFO" "${SHIELD} Setting up GitHub authentication..."
    start_timer "auth_setup"
    
    # Method 1: GitHub CLI (preferred)
    if setup_github_cli_auth; then
        log "SUCCESS" "GitHub CLI authentication configured"
        end_timer "auth_setup"
        return 0
    fi
    
    # Method 2: SSH keys
    if setup_ssh_auth; then
        log "SUCCESS" "SSH authentication configured"
        end_timer "auth_setup"
        return 0
    fi
    
    # Method 3: Personal Access Token
    if setup_token_auth; then
        log "SUCCESS" "Token authentication configured"
        end_timer "auth_setup"
        return 0
    fi
    
    log "WARN" "No authentication method configured - proceeding with public repository access only"
    log "WARN" "To enable full functionality, set up GitHub authentication:"
    log "WARN" "  1. Install GitHub CLI: gh auth login"
    log "WARN" "  2. Set up SSH keys, or"
    log "WARN" "  3. Set GITHUB_TOKEN environment variable"
    
    end_timer "auth_setup"
    return 0  # Continue with public access
}

setup_github_cli_auth() {
    if command -v gh &> /dev/null; then
        if gh auth status &> /dev/null; then
            log "INFO" "GitHub CLI already authenticated"
            return 0
        else
            log "INFO" "GitHub CLI not authenticated, skipping automatic login"
            return 1
        fi
    fi
    return 1
}

setup_ssh_auth() {
    local ssh_key_path="$HOME/.ssh/id_rsa"
    
    if [[ -f "$ssh_key_path" ]]; then
        # Test SSH connection
        if timeout 10 ssh -o BatchMode=yes -o StrictHostKeyChecking=no -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            log "INFO" "SSH key authentication working"
            return 0
        fi
    fi
    
    log "INFO" "SSH authentication not available or not working"
    return 1
}

setup_token_auth() {
    local token
    
    # Check environment variable first
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        token="$GITHUB_TOKEN"
        log "INFO" "Using GitHub token from environment variable"
    else
        log "INFO" "No GitHub token found in environment variables"
        return 1
    fi
    
    if [[ -n "$token" ]]; then
        # Test token
        if timeout 10 curl -s -H "Authorization: token $token" https://api.github.com/user | jq -r '.login' &> /dev/null; then
            # Configure git to use token
            git config --global credential.helper store
            echo "https://${token}@github.com" > "$HOME/.git-credentials"
            return 0
        else
            log "WARN" "GitHub token validation failed"
            return 1
        fi
    fi
    
    return 1
}

# ============================================================================
# REPOSITORY MANAGEMENT
# ============================================================================

# Intelligent repository parsing and validation
parse_repository_info() {
    log "INFO" "${BRAIN} Parsing repository information..."
    
    # Extract owner and repo name from URL
    if [[ "$REPO_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
        REPO_OWNER="${BASH_REMATCH[1]}"
        REPO_NAME="${BASH_REMATCH[2]%.git}"
        REPO_DIR="$WORK_DIR/$REPO_NAME"
    else
        log "ERROR" "Invalid GitHub repository URL: $REPO_URL"
        return 1
    fi
    
    log "INFO" "Repository: $REPO_OWNER/$REPO_NAME"
    log "INFO" "Clone directory: $REPO_DIR"
}

# Advanced repository cloning with optimization
clone_repository() {
    log "INFO" "${ROCKET} Cloning repository..."
    start_timer "clone"
    
    # Create work directory
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    
    # Remove existing directory if it exists
    if [[ -d "$REPO_NAME" ]]; then
        log "WARN" "Repository directory exists, removing..."
        rm -rf "$REPO_NAME"
    fi
    
    # Clone with optimizations
    local clone_args=(
        "--depth=1"              # Shallow clone for speed
        "--single-branch"        # Only main branch initially
        "--recurse-submodules"   # Include submodules
        "--progress"             # Show progress
    )
    
    if ! retry_with_backoff "git_clone" 3 git clone "${clone_args[@]}" "$REPO_URL" "$REPO_NAME"; then
        log "ERROR" "Failed to clone repository"
        return 1
    fi
    
    cd "$REPO_NAME"
    
    # Check if this is an empty repository and initialize it
    if ! git log -1 >/dev/null 2>&1; then
        log "INFO" "Empty repository detected, initializing with basic structure..."
        initialize_empty_repository
    fi
    
    end_timer "clone"
    log "SUCCESS" "${SUCCESS} Repository cloned successfully"
}

# Initialize empty repository with basic structure
initialize_empty_repository() {
    log "INFO" "Setting up initial repository structure..."
    
    # Create basic README if it doesn't exist
    if [[ ! -f "README.md" ]]; then
        cat > "README.md" << EOF
# $(basename "$REPO_URL" .git)

## Overview

This repository has been automatically initialized and configured with GitOps automation.

## Features

- 🚀 Automated CI/CD pipeline
- 🛡️ Security scanning and best practices
- 🔄 Automated dependency management
- 📊 Comprehensive testing and quality checks

## Getting Started

\`\`\`bash
# Clone the repository
git clone $REPO_URL
cd $(basename "$REPO_URL" .git)

# Install dependencies (if applicable)
# npm install  # for Node.js projects
# pip install -r requirements.txt  # for Python projects
\`\`\`

## Documentation

- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*This repository was initialized and configured using GitOps Automation - Tungsten Grade v$SCRIPT_VERSION*
EOF
    fi
    
    # Create basic gitignore
    if [[ ! -f ".gitignore" ]]; then
        cat > ".gitignore" << EOF
# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.env

# Build outputs
dist/
build/
*.egg-info/

# IDE files
.vscode/
.idea/
*.swp

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/
EOF
    fi
    
    # Create basic license file
    if [[ ! -f "LICENSE" ]]; then
        cat > "LICENSE" << EOF
MIT License

Copyright (c) $(date +%Y) $(git config user.name)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    fi
    
    # Initial commit
    git add .
    git commit -m "Initial commit: Repository structure and documentation

- Added README with project overview
- Added .gitignore for common file patterns
- Added MIT license
- Repository configured with GitOps automation

Generated by GitOps Automation - Tungsten Grade v$SCRIPT_VERSION"
    
    log "SUCCESS" "Empty repository initialized with basic structure"
}

# Repository analysis and health check
analyze_repository() {
    log "INFO" "${BRAIN} Analyzing repository structure..."
    start_timer "analysis"
    
    local repo_info=()
    
    # Basic repository information with error handling for empty repos
    local current_branch=$(git branch --show-current 2>/dev/null || echo "main (empty)")
    repo_info+=("Branch: $current_branch")
    
    # Check if repository has commits
    if git log -1 --pretty=format:'%h' >/dev/null 2>&1; then
        repo_info+=("Last commit: $(git log -1 --pretty=format:'%h - %s (%an, %ar)')")
    else
        repo_info+=("Last commit: No commits yet (empty repository)")
    fi
    
    repo_info+=("File count: $(find . -type f | wc -l)")
    repo_info+=("Directory size: $(du -sh . | cut -f1)")
    
    # Detect project type
    local project_type="Unknown"
    if [[ -f "package.json" ]]; then
        project_type="Node.js/JavaScript"
    elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]] || [[ -f "setup.py" ]]; then
        project_type="Python"
    elif [[ -f "Cargo.toml" ]]; then
        project_type="Rust"
    elif [[ -f "go.mod" ]]; then
        project_type="Go"
    elif [[ -f "pom.xml" ]] || [[ -f "build.gradle" ]]; then
        project_type="Java"
    elif [[ -f "Dockerfile" ]]; then
        project_type="Docker"
    fi
    
    repo_info+=("Project type: $project_type")
    
    # Check for CI/CD configuration
    local ci_systems=()
    [[ -d ".github/workflows" ]] && ci_systems+=("GitHub Actions")
    [[ -f ".gitlab-ci.yml" ]] && ci_systems+=("GitLab CI")
    [[ -f "Jenkinsfile" ]] && ci_systems+=("Jenkins")
    [[ -f ".travis.yml" ]] && ci_systems+=("Travis CI")
    [[ -f "circle.yml" ]] || [[ -f ".circleci/config.yml" ]] && ci_systems+=("CircleCI")
    
    if [[ ${#ci_systems[@]} -gt 0 ]]; then
        repo_info+=("CI/CD: ${ci_systems[*]}")
    else
        repo_info+=("CI/CD: None detected")
    fi
    
    # Security analysis
    local security_files=()
    [[ -f "SECURITY.md" ]] && security_files+=("Security Policy")
    [[ -f ".github/dependabot.yml" ]] && security_files+=("Dependabot")
    [[ -f ".snyk" ]] && security_files+=("Snyk")
    
    if [[ ${#security_files[@]} -gt 0 ]]; then
        repo_info+=("Security: ${security_files[*]}")
    fi
    
    # Print analysis results
    log "INFO" "Repository Analysis Results:"
    for info in "${repo_info[@]}"; do
        log "INFO" "  $info"
    done
    
    end_timer "analysis"
}

# ============================================================================
# CI/CD PIPELINE MANAGEMENT
# ============================================================================

# Intelligent CI/CD setup with best practices
setup_cicd_pipeline() {
    log "INFO" "${GEAR} Setting up CI/CD pipeline..."
    start_timer "cicd_setup"
    
    # Detect existing CI/CD or create GitHub Actions workflow
    if [[ -d ".github/workflows" ]]; then
        log "INFO" "Existing GitHub Actions workflows detected"
        optimize_existing_workflows
    else
        create_github_actions_workflow
    fi
    
    # Setup additional CI/CD enhancements
    setup_dependabot
    setup_security_scanning
    setup_code_quality_checks
    
    end_timer "cicd_setup"
    log "SUCCESS" "${SUCCESS} CI/CD pipeline configured"
}

create_github_actions_workflow() {
    log "INFO" "Creating GitHub Actions workflow..."
    
    mkdir -p ".github/workflows"
    
    # Detect project type and create appropriate workflow
    if [[ -f "package.json" ]]; then
        create_nodejs_workflow
    elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
        create_python_workflow
    elif [[ -f "Cargo.toml" ]]; then
        create_rust_workflow
    elif [[ -f "go.mod" ]]; then
        create_go_workflow
    else
        create_generic_workflow
    fi
}

create_python_workflow() {
    cat > ".github/workflows/ci.yml" << 'EOF'
name: CI/CD Pipeline - Tungsten Grade

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly security scan

env:
  PYTHON_VERSION: '3.11'

jobs:
  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'

  test:
    name: Test Suite
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/pip
          ~/.local/share/virtualenvs
        key: ${{ runner.os }}-python-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt', '**/pyproject.toml') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt || pip install -e .
        pip install pytest pytest-cov ruff black isort safety bandit
    
    - name: Code quality checks
      run: |
        ruff check .
        black --check .
        isort --check-only .
        bandit -r . -f json -o bandit-report.json || true
    
    - name: Security check
      run: safety check
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'

  build:
    name: Build & Package
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Build package
      run: |
        python -m pip install --upgrade pip build
        python -m build
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist
        path: dist/

  deploy:
    name: Deploy
    needs: [build]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download artifacts
      uses: actions/download-artifact@v3
      with:
        name: dist
        path: dist/
    
    - name: Deploy to PyPI
      if: startsWith(github.ref, 'refs/tags/')
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}

  auto-merge:
    name: Auto-merge Dependabot PRs
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]' && github.event_name == 'pull_request'
    needs: [test]
    
    steps:
    - name: Enable auto-merge
      run: gh pr merge --auto --merge "$PR_URL"
      env:
        PR_URL: ${{ github.event.pull_request.html_url }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
EOF
}

setup_dependabot() {
    log "INFO" "Setting up Dependabot configuration..."
    
    mkdir -p ".github"
    cat > ".github/dependabot.yml" << 'EOF'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "02:00"
    open-pull-requests-limit: 10
    reviewers:
      - "maintainer"
    assignees:
      - "maintainer"
    commit-message:
      prefix: "deps"
      include: "scope"
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
EOF
}

setup_security_scanning() {
    log "INFO" "Setting up security scanning..."
    
    # Create CodeQL workflow
    cat > ".github/workflows/codeql-analysis.yml" << 'EOF'
name: "CodeQL Security Analysis"

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python', 'javascript' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
EOF
}

# ============================================================================
# ADVANCED ERROR HANDLING & SELF-HEALING
# ============================================================================

# AI-powered error analysis using local LLM (if ExWork Agent is available)
analyze_and_suggest_fix() {
    local failed_command="$1"
    local exit_code="$2"
    local function_name="$3"
    
    if ! command -v python3 &> /dev/null || [[ ! -f "exworkagent0.py" ]]; then
        return 0  # Skip AI analysis if ExWork Agent not available
    fi
    
    log "INFO" "${BRAIN} Analyzing error with AI..."
    
    local error_context=$(cat << EOF
{
  "step_id": "error_analysis_$(date +%s)",
  "description": "AI-powered error analysis and solution suggestion",
  "actions": [
    {
      "type": "DIAGNOSE_ERROR",
      "failed_command": "$failed_command",
      "stdout": "$(tail -10 $LOG_FILE | jq -R -s .)",
      "stderr": "$(tail -10 $ERROR_LOG | jq -R -s .)",
      "context": {
        "exit_code": $exit_code,
        "function": "$function_name",
        "script_version": "$SCRIPT_VERSION",
        "operation": "GitOps Automation"
      }
    }
  ]
}
EOF
)
    
    # Use ExWork Agent for AI analysis
    if echo "$error_context" | python3 exworkagent0.py --process-stdin 2>/dev/null; then
        log "SUCCESS" "${BRAIN} AI analysis completed"
    else
        log "WARN" "AI analysis failed, continuing with standard error handling"
    fi
}

# Self-healing mechanisms
attempt_self_healing() {
    local failed_command="$1"
    local exit_code="$2"
    local function_name="$3"
    
    log "INFO" "${GEAR} Attempting self-healing for: $function_name"
    
    case "$function_name" in
        "setup_github_cli_auth")
            heal_github_auth_issues
            ;;
        "clone_repository")
            heal_clone_issues
            ;;
        "git_operations")
            heal_git_issues
            ;;
        *)
            heal_generic_issues "$failed_command" "$exit_code"
            ;;
    esac
}

heal_github_auth_issues() {
    log "INFO" "Self-healing: GitHub authentication issues"
    
    # Clear corrupted auth and retry
    gh auth logout 2>/dev/null || true
    rm -f "$HOME/.config/gh/hosts.yml" 2>/dev/null || true
    
    # Try alternative authentication method
    setup_ssh_auth || setup_token_auth
}

heal_clone_issues() {
    log "INFO" "Self-healing: Repository clone issues"
    
    # Try different clone methods
    local repo_name_from_url=$(basename "$REPO_URL" .git)
    
    # Method 1: HTTPS with credentials
    if git clone "https://github.com/$REPO_OWNER/$repo_name_from_url.git" "$REPO_NAME" 2>/dev/null; then
        return 0
    fi
    
    # Method 2: SSH
    if git clone "git@github.com:$REPO_OWNER/$repo_name_from_url.git" "$REPO_NAME" 2>/dev/null; then
        return 0
    fi
    
    # Method 3: GitHub CLI
    if command -v gh &> /dev/null && gh repo clone "$REPO_OWNER/$repo_name_from_url" "$REPO_NAME" 2>/dev/null; then
        return 0
    fi
    
    return 1
}

heal_git_issues() {
    log "INFO" "Self-healing: Git operation issues"
    
    # Common git issue fixes
    git config --global core.autocrlf false
    git config --global core.filemode false
    git config --global init.defaultBranch main
    
    # Fix potential permission issues
    if [[ -d ".git" ]]; then
        chmod -R u+w .git
    fi
}

heal_generic_issues() {
    local failed_command="$1"
    local exit_code="$2"
    
    log "INFO" "Self-healing: Generic issue resolution"
    
    # Network-related healing
    if [[ "$failed_command" =~ (curl|wget|git|gh) ]]; then
        log "INFO" "Detected network operation, checking connectivity..."
        
        # Test connectivity
        if ! ping -c 1 8.8.8.8 &>/dev/null; then
            log "WARN" "Network connectivity issues detected"
            # Wait and retry
            sleep 10
        fi
        
        # DNS issues
        if ! nslookup github.com &>/dev/null; then
            log "WARN" "DNS resolution issues detected"
            echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
        fi
    fi
    
    # Permission-related healing
    if [[ $exit_code -eq 126 ]] || [[ $exit_code -eq 127 ]]; then
        log "INFO" "Permission or command not found issues detected"
        
        # Fix common permission issues
        chmod +x "$0" 2>/dev/null || true
        
        # Update PATH
        export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
    fi
}

# ============================================================================
# MONITORING & ALERTING
# ============================================================================

# Real-time monitoring and metrics collection
start_monitoring() {
    if [[ "$ENABLE_MONITORING" != "true" ]]; then
        return 0
    fi
    
    log "INFO" "${GEAR} Starting monitoring..."
    
    # Background monitoring process
    {
        while kill -0 $SCRIPT_PID 2>/dev/null; do
            collect_metrics
            sleep 30
        done
    } &
    
    local monitor_pid=$!
    echo "$monitor_pid" > "${TEMP_DIR}/monitor.pid"
}

collect_metrics() {
    local timestamp=$(date +%s)
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || echo "0")
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' 2>/dev/null || echo "0")
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "0")
    
    local error_count=0
    if [[ -f "$ERROR_LOG" ]]; then
        error_count=$(wc -l < "$ERROR_LOG" 2>/dev/null || echo "0")
    fi
    
    local metrics=$(cat << EOF
{
  "timestamp": $timestamp,
  "cpu_usage": "$cpu_usage",
  "memory_usage": "$memory_usage",
  "disk_usage": "$disk_usage",
  "script_pid": $SCRIPT_PID,
  "operations_completed": $(echo "${!OPERATION_STATUS[@]}" | wc -w),
  "errors_count": $error_count,
  "uptime": $((timestamp - SCRIPT_START_TIME))
}
EOF
)
    
    if [[ -d "$TEMP_DIR" ]]; then
        echo "$metrics" >> "$METRICS_FILE"
    fi
}

# Performance report generation
generate_performance_report() {
    log "INFO" "Generating performance report..."
    
    local total_duration=$(($(date +%s) - SCRIPT_START_TIME))
    local success_count=0
    local failure_count=0
    
    for status in "${OPERATION_STATUS[@]}"; do
        if [[ "$status" == "SUCCESS" ]]; then
            ((success_count++))
        else
            ((failure_count++))
        fi
    done
    
    local success_rate=0
    if [[ $((success_count + failure_count)) -gt 0 ]]; then
        success_rate=$(echo "scale=2; $success_count * 100 / ($success_count + $failure_count)" | bc)
    fi
    
    cat << EOF

${BOLD}═══════════════════════════════════════════════════════════════════${NC}
${BOLD}                    GITOPS AUTOMATION REPORT                      ${NC}
${BOLD}═══════════════════════════════════════════════════════════════════${NC}

${BLUE}Script Information:${NC}
  • Version: $SCRIPT_VERSION
  • Duration: ${total_duration}s
  • Repository: ${REPO_OWNER:-"N/A"}/${REPO_NAME:-"N/A"}

${BLUE}Operation Summary:${NC}
  • Total Operations: $((success_count + failure_count))
  • Successful: ${GREEN}$success_count${NC}
  • Failed: ${RED}$failure_count${NC}
  • Success Rate: ${GREEN}${success_rate}%${NC}

${BLUE}Performance Metrics:${NC}
EOF

    for operation in "${!PERFORMANCE_METRICS[@]}"; do
        if [[ "$operation" =~ _duration$ ]]; then
            local op_name=${operation%_duration}
            local duration=${PERFORMANCE_METRICS[$operation]}
            echo "  • ${op_name}: ${duration}s"
        fi
    done

    if [[ $failure_count -gt 0 ]]; then
        echo
        echo "${BLUE}Error Summary:${NC}"
        if [[ -f "$ERROR_LOG" ]]; then
            tail -5 "$ERROR_LOG" | while read -r error; do
                echo "  ${RED}•${NC} $error"
            done
        else
            echo "  ${RED}•${NC} No error log available"
        fi
    fi

    echo
    echo "${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

# Main execution flow
main() {
    log "INFO" "${ROCKET} Starting GitOps Automation - Tungsten Grade v$SCRIPT_VERSION"
    
    if [[ "$TEST_MODE" == "true" ]]; then
        log "INFO" "${GEAR} Running in TEST MODE - limited functionality"
        test_mode_execution
        return 0
    fi
    
    # Initialize monitoring
    start_monitoring
    
    # System preparation
    check_system_requirements
    
    # Repository setup
    parse_repository_info
    setup_authentication
    clone_repository
    analyze_repository
    
    # CI/CD pipeline setup
    setup_cicd_pipeline
    
    # Commit and push changes
    commit_and_push_changes
    
    # Final validation
    validate_deployment
    
    log "SUCCESS" "${SUCCESS} GitOps automation completed successfully!"
}

# Test mode execution with limited functionality
test_mode_execution() {
    log "INFO" "${GEAR} Test Mode: Checking system requirements..."
    check_system_requirements
    
    log "INFO" "${BRAIN} Test Mode: Parsing repository information..."
    parse_repository_info
    
    log "INFO" "${SHIELD} Test Mode: Testing authentication setup..."
    setup_authentication
    
    log "SUCCESS" "${SUCCESS} Test mode completed successfully!"
    log "INFO" "To run full automation, use: $0 --repo $REPO_URL"
}

# Commit and push all changes
commit_and_push_changes() {
    log "INFO" "${ROCKET} Committing and pushing changes..."
    start_timer "git_operations"
    
    # Check if there are changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        log "INFO" "No changes to commit"
        end_timer "git_operations"
        return 0
    fi
    
    # Add all changes
    git add .
    
    # Create intelligent commit message
    local commit_message="feat: Enhanced GitOps automation pipeline

- Added Tungsten Grade CI/CD workflows
- Configured security scanning and code quality checks
- Set up Dependabot for dependency management
- Enhanced error handling and self-healing capabilities

Auto-generated by GitOps Automation v$SCRIPT_VERSION"
    
    # Commit changes
    if ! git commit -m "$commit_message"; then
        log "ERROR" "Failed to commit changes"
        return 1
    fi
    
    # Push to remote
    local current_branch=$(git branch --show-current)
    if ! retry_with_backoff "git_push" 3 git push origin "$current_branch"; then
        log "ERROR" "Failed to push changes to remote"
        return 1
    fi
    
    end_timer "git_operations"
    log "SUCCESS" "${SUCCESS} Changes committed and pushed successfully"
}

# Final deployment validation
validate_deployment() {
    log "INFO" "${SHIELD} Validating deployment..."
    start_timer "validation"
    
    # Check if workflows are properly configured
    if [[ -f ".github/workflows/ci.yml" ]]; then
        log "SUCCESS" "CI/CD workflow configured"
    else
        log "WARN" "CI/CD workflow not found"
    fi
    
    # Check security configurations
    local security_score=0
    [[ -f ".github/dependabot.yml" ]] && ((security_score++))
    [[ -f ".github/workflows/codeql-analysis.yml" ]] && ((security_score++))
    [[ -f "SECURITY.md" ]] && ((security_score++))
    
    log "INFO" "Security configuration score: $security_score/3"
    
    # Validate git configuration
    if git config --get remote.origin.url &>/dev/null; then
        log "SUCCESS" "Git remote configuration valid"
    else
        log "WARN" "Git remote configuration issues detected"
    fi
    
    end_timer "validation"
    log "SUCCESS" "${SUCCESS} Deployment validation completed"
}

# Cleanup function
cleanup_and_exit() {
    local exit_code=${1:-0}
    
    # Stop monitoring
    if [[ -f "${TEMP_DIR}/monitor.pid" ]]; then
        local monitor_pid=$(cat "${TEMP_DIR}/monitor.pid")
        kill "$monitor_pid" 2>/dev/null || true
    fi
    
    # Generate final report
    generate_performance_report
    
    # Cleanup temporary files
    if [[ -d "$TEMP_DIR" ]]; then
        # Copy logs to current directory if they exist
        [[ -f "$LOG_FILE" ]] && cp "$LOG_FILE" "./gitops-execution.log" 2>/dev/null || true
        [[ -f "$METRICS_FILE" ]] && cp "$METRICS_FILE" "./gitops-metrics.json" 2>/dev/null || true
        rm -rf "$TEMP_DIR"
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "${SUCCESS} GitOps automation completed successfully!"
    else
        log "ERROR" "${ERROR} GitOps automation failed with exit code: $exit_code"
    fi
    
    exit $exit_code
}

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

# Display banner
cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════════════╗
 ║                                                                   ║
 ║              GitOps Automation - Tungsten Grade                  ║
 ║                         Version 3.0.0                            ║
 ║                                                                   ║
 ║     🚀 Advanced Git automation with AI-driven self-healing       ║
 ║     🧠 Intelligent error recovery and adaptation                 ║
 ║     🛡️ Enterprise-grade security and best practices              ║
 ║     ⚙️ Zero-configuration repository management                   ║
 ║                                                                   ║
 ╚═══════════════════════════════════════════════════════════════════╝
EOF

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_URL="$2"
            shift 2
            ;;
        --work-dir)
            WORK_DIR="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --disable-ai)
            ENABLE_AI="false"
            shift
            ;;
        --disable-healing)
            ENABLE_SELF_HEALING="false"
            shift
            ;;
        --disable-monitoring)
            ENABLE_MONITORING="false"
            shift
            ;;
        --help)
            cat << EOF
GitOps Automation - Tungsten Grade

Usage: $0 [OPTIONS] [REPOSITORY_URL]

OPTIONS:
    --repo URL              Repository URL (default: $DEFAULT_REPO_URL)
    --work-dir DIR          Working directory (default: $WORK_DIR)
    --log-level LEVEL       Logging level (default: $LOG_LEVEL)
    --disable-ai            Disable AI-powered error analysis
    --disable-healing       Disable self-healing mechanisms
    --disable-monitoring    Disable real-time monitoring
    --test                  Run in test mode (limited functionality)
    --help                  Show this help message

EXAMPLES:
    $0                                          # Use default repository
    $0 https://github.com/user/repo.git        # Use specific repository
    $0 --work-dir /tmp/gitops --log-level DEBUG
    $0 --test                                   # Test mode

ENVIRONMENT VARIABLES:
    GITOPS_WORK_DIR         Override default work directory
    GITOPS_LOG_LEVEL        Override default log level
    GITOPS_MAX_RETRIES      Maximum retry attempts (default: 3)
    GITOPS_ENABLE_AI        Enable AI features (default: true)
    GITHUB_TOKEN            GitHub personal access token

EOF
            exit 0
            ;;
        --test)
            TEST_MODE="true"
            shift
            ;;
        *)
            # Only set REPO_URL if it's not already set by --repo and it's not a flag
            if [[ "$REPO_URL" == "$DEFAULT_REPO_URL" && "$1" != --* ]]; then
                REPO_URL="$1"
            elif [[ "$1" == --* ]]; then
                log "ERROR" "Unknown option: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# For test mode, use default repository if none specified
if [[ "$TEST_MODE" == "true" && "$REPO_URL" == "$DEFAULT_REPO_URL" ]]; then
    REPO_URL="$DEFAULT_REPO_URL"
fi

# Validate repository URL (skip validation in test mode)
if [[ -z "$REPO_URL" && "$TEST_MODE" != "true" ]]; then
    log "ERROR" "Repository URL is required"
    exit 1
fi

# Execute main function
main "$@"
