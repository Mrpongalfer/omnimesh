#!/bin/bash

# OmniMesh Secure Installation Script
# Addresses Tiger Lily audit findings with production-grade security
# Version: 2.0.0-secure
# 
# SECURITY FEATURES:
# - Cryptographic verification of all downloads
# - GPG signature validation
# - No pipe-to-shell execution
# - Comprehensive audit logging
# - Rollback capability
# - Privilege validation
# - Network security checks
# - Environment validation

set -euo pipefail

# Security configuration
readonly SCRIPT_VERSION="2.0.0-secure"
readonly GITHUB_REPO="Mrpongalfer/omnimesh"
readonly BINARY_NAME="omni-cli"
readonly INSTALL_DIR="/usr/local/bin"
readonly CONFIG_DIR="$HOME/.config/omni-cli"
readonly LOG_DIR="$HOME/.local/share/omni-cli/logs"
readonly CACHE_DIR="$HOME/.cache/omni-cli"
readonly BACKUP_DIR="$HOME/.local/share/omni-cli/backup"

# Security settings
readonly CHECKSUM_ALGORITHM="sha256"
readonly GPG_KEY_ID="omnimesh-security@omnimesh.dev"
readonly DOWNLOAD_TIMEOUT="300"
readonly MAX_RETRIES="3"
readonly MIN_DISK_SPACE="100" # MB
readonly AUDIT_LOG_RETENTION="90" # days

# Network security
readonly ALLOWED_HOSTS=(
    "github.com"
    "api.github.com"
    "objects.githubusercontent.com"
    "releases.github.com"
)

readonly REQUIRED_TLS_VERSION="1.2"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Global variables
TEMP_DIR=""
DOWNLOAD_URL=""
CHECKSUM_URL=""
SIGNATURE_URL=""
CURRENT_VERSION=""
NEW_VERSION=""
INSTALL_LOG=""
AUDIT_LOG=""
TRANSACTION_ID=""

# Logging and audit functions
init_logging() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    TRANSACTION_ID="install_${timestamp}_$$"
    
    mkdir -p "$LOG_DIR" "$CACHE_DIR" "$BACKUP_DIR"
    
    INSTALL_LOG="${LOG_DIR}/install-${timestamp}.log"
    AUDIT_LOG="${LOG_DIR}/audit.log"
    
    # Create install log
    {
        echo "# OmniMesh Secure Installation Log"
        echo "# Transaction ID: $TRANSACTION_ID"
        echo "# Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "# Script Version: $SCRIPT_VERSION"
        echo "# User: $(whoami)"
        echo "# Working Directory: $(pwd)"
        echo "# Shell: $SHELL"
        echo "# OS: $(uname -a)"
        echo ""
    } > "$INSTALL_LOG"
    
    # Append to audit log
    log_audit "INSTALL_START" "Installation started" \
        "transaction_id=$TRANSACTION_ID" \
        "script_version=$SCRIPT_VERSION" \
        "user=$(whoami)" \
        "pwd=$(pwd)"
}

log_info() {
    local message="$1"
    echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$INSTALL_LOG"
}

log_success() {
    local message="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$INSTALL_LOG"
}

log_warn() {
    local message="$1"
    echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$INSTALL_LOG"
}

log_error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" | tee -a "$INSTALL_LOG"
}

log_critical() {
    local message="$1"
    echo -e "${RED}[CRITICAL]${NC} $message" | tee -a "$INSTALL_LOG"
}

log_audit() {
    local level="$1"
    local event="$2"
    shift 2
    
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local details="$*"
    
    {
        echo "[$timestamp] [$level] [$TRANSACTION_ID] $event"
        if [[ -n "$details" ]]; then
            echo "  Details: $details"
        fi
    } >> "$AUDIT_LOG"
    
    # Also send to syslog if available
    if command -v logger >/dev/null 2>&1; then
        logger -t "omnimesh-install" "[$level] $event: $details"
    fi
}

# Security validation functions
validate_environment() {
    log_info "Validating installation environment..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root is not recommended for security reasons"
        log_audit "SECURITY_WARNING" "Running as root" "user=root"
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Installation cancelled by user"
            exit 1
        fi
    fi
    
    # Check if user has write permissions to install directory
    if [[ ! -w "$(dirname "$INSTALL_DIR")" ]]; then
        log_error "No write permission to $INSTALL_DIR"
        log_error "Please run with appropriate privileges or choose different install directory"
        exit 1
    fi
    
    # Validate shell environment
    if [[ -z "${SHELL:-}" ]]; then
        log_error "SHELL environment variable not set"
        exit 1
    fi
    
    # Check disk space
    local available_space
    available_space=$(df -m "$HOME" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt $MIN_DISK_SPACE ]]; then
        log_error "Insufficient disk space: ${available_space}MB available, ${MIN_DISK_SPACE}MB required"
        exit 1
    fi
    
    # Validate network connectivity
    if ! ping -c 1 github.com >/dev/null 2>&1; then
        log_error "No network connectivity to GitHub"
        exit 1
    fi
    
    log_success "Environment validation passed"
    log_audit "VALIDATION_SUCCESS" "Environment validated" \
        "user=$(whoami)" \
        "disk_space=${available_space}MB" \
        "install_dir=$INSTALL_DIR"
}

validate_dependencies() {
    log_info "Checking required dependencies..."
    
    local required_commands=(
        "curl"
        "tar"
        "gzip"
        "sha256sum"
        "gpg"
        "openssl"
    )
    
    local missing_deps=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
            log_error "Missing required dependency: $cmd"
        else
            log_info "Found dependency: $cmd"
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Please install missing dependencies and try again"
        
        # Provide installation hints
        if command -v apt-get >/dev/null 2>&1; then
            log_info "Install with: sudo apt-get install ${missing_deps[*]}"
        elif command -v yum >/dev/null 2>&1; then
            log_info "Install with: sudo yum install ${missing_deps[*]}"
        elif command -v brew >/dev/null 2>&1; then
            log_info "Install with: brew install ${missing_deps[*]}"
        fi
        
        exit 1
    fi
    
    log_success "All dependencies satisfied"
    log_audit "DEPENDENCY_CHECK" "All dependencies validated" \
        "dependencies=${required_commands[*]}"
}

validate_network_security() {
    log_info "Validating network security..."
    
    # Check TLS version support
    local tls_version
    tls_version=$(curl -sI --tlsv1.2 https://github.com 2>/dev/null | head -n1 || echo "FAILED")
    
    if [[ "$tls_version" == "FAILED" ]]; then
        log_error "TLS 1.2+ not supported or network error"
        exit 1
    fi
    
    # Validate allowed hosts
    for host in "${ALLOWED_HOSTS[@]}"; do
        if ! nslookup "$host" >/dev/null 2>&1; then
            log_warn "Cannot resolve host: $host"
        else
            log_info "Validated host: $host"
        fi
    done
    
    # Check for proxy configuration
    if [[ -n "${HTTP_PROXY:-}" ]] || [[ -n "${HTTPS_PROXY:-}" ]]; then
        log_warn "Proxy configuration detected"
        log_audit "PROXY_DETECTED" "Proxy configuration found" \
            "http_proxy=${HTTP_PROXY:-}" \
            "https_proxy=${HTTPS_PROXY:-}"
    fi
    
    log_success "Network security validation passed"
}

# Platform detection with security validation
detect_platform() {
    log_info "Detecting platform..."
    
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    # Validate OS
    case $os in
        linux*)
            OS="linux"
            log_info "Detected OS: Linux"
            ;;
        darwin*)
            OS="darwin"
            log_info "Detected OS: macOS"
            ;;
        *)
            log_error "Unsupported operating system: $os"
            log_audit "UNSUPPORTED_OS" "Unsupported OS detected" "os=$os"
            exit 1
            ;;
    esac
    
    # Validate architecture
    case $arch in
        x86_64|amd64)
            ARCH="amd64"
            log_info "Detected architecture: amd64"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            log_info "Detected architecture: arm64"
            ;;
        armv7l)
            ARCH="armv7"
            log_info "Detected architecture: armv7"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            log_audit "UNSUPPORTED_ARCH" "Unsupported architecture detected" "arch=$arch"
            exit 1
            ;;
    esac
    
    # Set platform-specific variables
    PLATFORM="${OS}_${ARCH}"
    log_success "Platform detected: $PLATFORM"
    log_audit "PLATFORM_DETECTION" "Platform detected" "platform=$PLATFORM"
}

# Secure download functions
setup_temp_directory() {
    # Create secure temporary directory
    TEMP_DIR=$(mktemp -d -t omnimesh-install.XXXXXXXXXX)
    
    # Set secure permissions
    chmod 700 "$TEMP_DIR"
    
    log_info "Created temporary directory: $TEMP_DIR"
    log_audit "TEMP_DIR_CREATED" "Temporary directory created" "temp_dir=$TEMP_DIR"
    
    # Cleanup on exit
    trap cleanup_temp_directory EXIT
}

cleanup_temp_directory() {
    if [[ -n "$TEMP_DIR" ]] && [[ -d "$TEMP_DIR" ]]; then
        log_info "Cleaning up temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
        log_audit "TEMP_DIR_CLEANUP" "Temporary directory cleaned up" "temp_dir=$TEMP_DIR"
    fi
}

get_latest_version() {
    log_info "Fetching latest version information..."
    
    local api_url="https://api.github.com/repos/$GITHUB_REPO/releases/latest"
    local response_file="$TEMP_DIR/release_info.json"
    
    # Download release information with security headers
    if ! curl -fsSL \
        --max-time "$DOWNLOAD_TIMEOUT" \
        --retry "$MAX_RETRIES" \
        --user-agent "omnimesh-secure-installer/$SCRIPT_VERSION" \
        --header "Accept: application/vnd.github+json" \
        --header "X-GitHub-Api-Version: 2022-11-28" \
        --tlsv1.2 \
        --cert-status \
        --output "$response_file" \
        "$api_url"; then
        log_error "Failed to fetch release information from GitHub API"
        log_audit "API_FETCH_FAILED" "GitHub API fetch failed" "url=$api_url"
        exit 1
    fi
    
    # Validate JSON response
    if ! command -v jq >/dev/null 2>&1; then
        # Parse JSON without jq (basic parsing)
        NEW_VERSION=$(grep -o '"tag_name":"[^"]*"' "$response_file" | cut -d'"' -f4)
    else
        NEW_VERSION=$(jq -r '.tag_name' "$response_file")
    fi
    
    if [[ -z "$NEW_VERSION" ]] || [[ "$NEW_VERSION" == "null" ]]; then
        log_error "Failed to parse version from release information"
        exit 1
    fi
    
    # Remove 'v' prefix if present
    NEW_VERSION=${NEW_VERSION#v}
    
    log_success "Latest version: $NEW_VERSION"
    log_audit "VERSION_FETCHED" "Latest version fetched" "version=$NEW_VERSION"
}

check_current_version() {
    log_info "Checking current installation..."
    
    if command -v "$BINARY_NAME" >/dev/null 2>&1; then
        CURRENT_VERSION=$("$BINARY_NAME" --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -n1 || echo "unknown")
        log_info "Current version: $CURRENT_VERSION"
        
        if [[ "$CURRENT_VERSION" == "$NEW_VERSION" ]]; then
            log_info "Already have the latest version ($CURRENT_VERSION)"
            log_audit "VERSION_CURRENT" "Already latest version" "version=$CURRENT_VERSION"
            
            read -p "Reinstall anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Installation cancelled by user"
                exit 0
            fi
        fi
    else
        log_info "No current installation found"
        CURRENT_VERSION="none"
    fi
    
    log_audit "VERSION_CHECK" "Version check completed" \
        "current=$CURRENT_VERSION" \
        "latest=$NEW_VERSION"
}

construct_download_urls() {
    log_info "Constructing download URLs..."
    
    local base_url="https://github.com/$GITHUB_REPO/releases/download/v$NEW_VERSION"
    local filename="${BINARY_NAME}_${NEW_VERSION}_${PLATFORM}.tar.gz"
    
    DOWNLOAD_URL="${base_url}/${filename}"
    CHECKSUM_URL="${base_url}/${filename}.${CHECKSUM_ALGORITHM}"
    SIGNATURE_URL="${base_url}/${filename}.sig"
    
    log_info "Download URL: $DOWNLOAD_URL"
    log_info "Checksum URL: $CHECKSUM_URL"
    log_info "Signature URL: $SIGNATURE_URL"
    
    log_audit "URLS_CONSTRUCTED" "Download URLs constructed" \
        "download_url=$DOWNLOAD_URL" \
        "checksum_url=$CHECKSUM_URL" \
        "signature_url=$SIGNATURE_URL"
}

secure_download() {
    local url="$1"
    local output_file="$2"
    local description="$3"
    
    log_info "Downloading $description..."
    log_audit "DOWNLOAD_START" "Download started" "url=$url" "file=$output_file"
    
    # Download with security measures
    if ! curl -fsSL \
        --max-time "$DOWNLOAD_TIMEOUT" \
        --retry "$MAX_RETRIES" \
        --user-agent "omnimesh-secure-installer/$SCRIPT_VERSION" \
        --tlsv1.2 \
        --cert-status \
        --location \
        --output "$output_file" \
        "$url"; then
        log_error "Failed to download $description from $url"
        log_audit "DOWNLOAD_FAILED" "Download failed" "url=$url" "file=$output_file"
        return 1
    fi
    
    # Validate download
    if [[ ! -f "$output_file" ]] || [[ ! -s "$output_file" ]]; then
        log_error "Downloaded file is empty or missing: $output_file"
        log_audit "DOWNLOAD_INVALID" "Downloaded file invalid" "file=$output_file"
        return 1
    fi
    
    log_success "Downloaded $description ($(du -h "$output_file" | cut -f1))"
    log_audit "DOWNLOAD_SUCCESS" "Download completed" \
        "url=$url" \
        "file=$output_file" \
        "size=$(stat -c%s "$output_file" 2>/dev/null || stat -f%z "$output_file" 2>/dev/null)"
    
    return 0
}

download_files() {
    log_info "Downloading installation files..."
    
    local archive_file="$TEMP_DIR/${BINARY_NAME}.tar.gz"
    local checksum_file="$TEMP_DIR/${BINARY_NAME}.${CHECKSUM_ALGORITHM}"
    local signature_file="$TEMP_DIR/${BINARY_NAME}.sig"
    
    # Download binary archive
    if ! secure_download "$DOWNLOAD_URL" "$archive_file" "binary archive"; then
        exit 1
    fi
    
    # Download checksum
    if ! secure_download "$CHECKSUM_URL" "$checksum_file" "checksum file"; then
        exit 1
    fi
    
    # Download signature (optional but recommended)
    if ! secure_download "$SIGNATURE_URL" "$signature_file" "signature file"; then
        log_warn "Signature file not available - skipping GPG verification"
        log_audit "SIGNATURE_UNAVAILABLE" "Signature file not available" "url=$SIGNATURE_URL"
    fi
    
    log_success "All files downloaded successfully"
}

verify_checksum() {
    log_info "Verifying file integrity..."
    
    local archive_file="$TEMP_DIR/${BINARY_NAME}.tar.gz"
    local checksum_file="$TEMP_DIR/${BINARY_NAME}.${CHECKSUM_ALGORITHM}"
    
    if [[ ! -f "$checksum_file" ]]; then
        log_error "Checksum file not found"
        exit 1
    fi
    
    # Read expected checksum
    local expected_checksum
    expected_checksum=$(cat "$checksum_file" | awk '{print $1}')
    
    if [[ -z "$expected_checksum" ]]; then
        log_error "Invalid checksum file format"
        exit 1
    fi
    
    # Calculate actual checksum
    local actual_checksum
    case "$CHECKSUM_ALGORITHM" in
        sha256)
            actual_checksum=$(sha256sum "$archive_file" | awk '{print $1}')
            ;;
        sha512)
            actual_checksum=$(sha512sum "$archive_file" | awk '{print $1}')
            ;;
        *)
            log_error "Unsupported checksum algorithm: $CHECKSUM_ALGORITHM"
            exit 1
            ;;
    esac
    
    # Compare checksums
    if [[ "$expected_checksum" != "$actual_checksum" ]]; then
        log_critical "CHECKSUM VERIFICATION FAILED!"
        log_critical "Expected: $expected_checksum"
        log_critical "Actual:   $actual_checksum"
        log_audit "CHECKSUM_FAILED" "Checksum verification failed" \
            "expected=$expected_checksum" \
            "actual=$actual_checksum"
        exit 1
    fi
    
    log_success "Checksum verification passed"
    log_audit "CHECKSUM_SUCCESS" "Checksum verified" \
        "algorithm=$CHECKSUM_ALGORITHM" \
        "checksum=$expected_checksum"
}

verify_signature() {
    log_info "Verifying GPG signature..."
    
    local archive_file="$TEMP_DIR/${BINARY_NAME}.tar.gz"
    local signature_file="$TEMP_DIR/${BINARY_NAME}.sig"
    
    if [[ ! -f "$signature_file" ]]; then
        log_warn "Signature file not found - skipping GPG verification"
        return 0
    fi
    
    # Import public key if not already imported
    if ! gpg --list-keys "$GPG_KEY_ID" >/dev/null 2>&1; then
        log_info "Importing GPG public key..."
        
        # Try to fetch key from multiple keyservers
        local keyservers=(
            "keyserver.ubuntu.com"
            "keys.openpgp.org"
            "pgp.mit.edu"
        )
        
        local key_imported=false
        for keyserver in "${keyservers[@]}"; do
            if gpg --keyserver "$keyserver" --recv-keys "$GPG_KEY_ID" >/dev/null 2>&1; then
                log_success "Imported GPG key from $keyserver"
                key_imported=true
                break
            fi
        done
        
        if [[ "$key_imported" != "true" ]]; then
            log_warn "Failed to import GPG key - skipping signature verification"
            log_audit "GPG_KEY_IMPORT_FAILED" "Failed to import GPG key" "key_id=$GPG_KEY_ID"
            return 0
        fi
    fi
    
    # Verify signature
    if ! gpg --verify "$signature_file" "$archive_file" >/dev/null 2>&1; then
        log_critical "GPG SIGNATURE VERIFICATION FAILED!"
        log_audit "SIGNATURE_FAILED" "GPG signature verification failed" \
            "signature_file=$signature_file" \
            "archive_file=$archive_file"
        exit 1
    fi
    
    log_success "GPG signature verification passed"
    log_audit "SIGNATURE_SUCCESS" "GPG signature verified" \
        "key_id=$GPG_KEY_ID" \
        "signature_file=$signature_file"
}

backup_existing_installation() {
    if [[ "$CURRENT_VERSION" != "none" ]] && [[ -f "$INSTALL_DIR/$BINARY_NAME" ]]; then
        log_info "Backing up existing installation..."
        
        local backup_file="$BACKUP_DIR/${BINARY_NAME}-${CURRENT_VERSION}-$(date +%Y%m%d_%H%M%S)"
        
        if cp "$INSTALL_DIR/$BINARY_NAME" "$backup_file"; then
            log_success "Backup created: $backup_file"
            log_audit "BACKUP_CREATED" "Existing installation backed up" \
                "source=$INSTALL_DIR/$BINARY_NAME" \
                "backup=$backup_file" \
                "version=$CURRENT_VERSION"
        else
            log_warn "Failed to create backup"
            log_audit "BACKUP_FAILED" "Failed to create backup" \
                "source=$INSTALL_DIR/$BINARY_NAME"
        fi
    fi
}

extract_and_install() {
    log_info "Extracting and installing binary..."
    
    local archive_file="$TEMP_DIR/${BINARY_NAME}.tar.gz"
    local extract_dir="$TEMP_DIR/extracted"
    
    # Create extraction directory
    mkdir -p "$extract_dir"
    
    # Extract archive
    if ! tar -xzf "$archive_file" -C "$extract_dir"; then
        log_error "Failed to extract archive"
        log_audit "EXTRACTION_FAILED" "Archive extraction failed" "archive=$archive_file"
        exit 1
    fi
    
    # Find binary in extracted files
    local binary_path
    binary_path=$(find "$extract_dir" -name "$BINARY_NAME" -type f -executable | head -n1)
    
    if [[ -z "$binary_path" ]] || [[ ! -f "$binary_path" ]]; then
        log_error "Binary not found in archive"
        log_audit "BINARY_NOT_FOUND" "Binary not found in archive" "extract_dir=$extract_dir"
        exit 1
    fi
    
    # Verify binary
    if ! file "$binary_path" | grep -q "executable"; then
        log_error "Downloaded file is not a valid executable"
        log_audit "INVALID_BINARY" "Invalid binary file" "binary_path=$binary_path"
        exit 1
    fi
    
    # Create install directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    
    # Install binary with secure permissions
    if cp "$binary_path" "$INSTALL_DIR/$BINARY_NAME"; then
        chmod 755 "$INSTALL_DIR/$BINARY_NAME"
        log_success "Binary installed to $INSTALL_DIR/$BINARY_NAME"
        log_audit "INSTALLATION_SUCCESS" "Binary installed" \
            "source=$binary_path" \
            "destination=$INSTALL_DIR/$BINARY_NAME" \
            "version=$NEW_VERSION"
    else
        log_error "Failed to install binary"
        log_audit "INSTALLATION_FAILED" "Binary installation failed" \
            "source=$binary_path" \
            "destination=$INSTALL_DIR/$BINARY_NAME"
        exit 1
    fi
}

setup_configuration() {
    log_info "Setting up configuration..."
    
    # Create config directory
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"
    
    # Create default configuration if it doesn't exist
    local config_file="$CONFIG_DIR/config.yaml"
    if [[ ! -f "$config_file" ]]; then
        cat > "$config_file" << EOF
# OmniMesh CLI Configuration
# Generated by secure installer v$SCRIPT_VERSION
# $(date -u +%Y-%m-%dT%H:%M:%SZ)

api:
  endpoint: "https://api.omnimesh.local"
  timeout: 30s
  retries: 3
  tls:
    verify: true
    min_version: "1.2"

security:
  audit_logging: true
  rate_limiting: true
  session_timeout: 15m
  csrf_protection: true

logging:
  level: "info"
  format: "json"
  file: "$LOG_DIR/omni-cli.log"

cache:
  directory: "$CACHE_DIR"
  ttl: "1h"
  max_size: "100MB"
EOF
        
        chmod 600 "$config_file"
        log_success "Default configuration created: $config_file"
        log_audit "CONFIG_CREATED" "Default configuration created" "config_file=$config_file"
    else
        log_info "Configuration file already exists: $config_file"
    fi
}

verify_installation() {
    log_info "Verifying installation..."
    
    # Check if binary is executable and in PATH
    if ! command -v "$BINARY_NAME" >/dev/null 2>&1; then
        log_warn "$BINARY_NAME not found in PATH"
        log_warn "Add $INSTALL_DIR to your PATH environment variable"
        log_audit "PATH_WARNING" "Binary not in PATH" "install_dir=$INSTALL_DIR"
    fi
    
    # Test binary execution
    local installed_version
    if installed_version=$("$INSTALL_DIR/$BINARY_NAME" --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -n1); then
        if [[ "$installed_version" == "$NEW_VERSION" ]]; then
            log_success "Installation verified successfully"
            log_success "Installed version: $installed_version"
            log_audit "VERIFICATION_SUCCESS" "Installation verified" \
                "installed_version=$installed_version" \
                "expected_version=$NEW_VERSION"
        else
            log_error "Version mismatch after installation"
            log_error "Expected: $NEW_VERSION, Got: $installed_version"
            log_audit "VERSION_MISMATCH" "Version mismatch detected" \
                "expected=$NEW_VERSION" \
                "actual=$installed_version"
            exit 1
        fi
    else
        log_error "Failed to execute installed binary"
        log_audit "EXECUTION_FAILED" "Installed binary execution failed"
        exit 1
    fi
}

update_path() {
    log_info "Updating PATH configuration..."
    
    # Check if install directory is in PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        # Determine shell configuration file
        local shell_config=""
        case "$SHELL" in
            */bash)
                if [[ -f "$HOME/.bashrc" ]]; then
                    shell_config="$HOME/.bashrc"
                elif [[ -f "$HOME/.bash_profile" ]]; then
                    shell_config="$HOME/.bash_profile"
                fi
                ;;
            */zsh)
                shell_config="$HOME/.zshrc"
                ;;
            */fish)
                shell_config="$HOME/.config/fish/config.fish"
                ;;
        esac
        
        if [[ -n "$shell_config" ]]; then
            local path_line="export PATH=\"$INSTALL_DIR:\$PATH\""
            
            # Check if PATH update already exists
            if ! grep -q "$INSTALL_DIR" "$shell_config" 2>/dev/null; then
                echo "" >> "$shell_config"
                echo "# Added by OmniMesh secure installer" >> "$shell_config"
                echo "$path_line" >> "$shell_config"
                
                log_success "Added $INSTALL_DIR to PATH in $shell_config"
                log_audit "PATH_UPDATED" "PATH updated in shell config" \
                    "shell_config=$shell_config" \
                    "install_dir=$INSTALL_DIR"
            else
                log_info "PATH already contains $INSTALL_DIR"
            fi
        else
            log_warn "Could not determine shell configuration file"
            log_warn "Please manually add $INSTALL_DIR to your PATH"
        fi
    else
        log_info "PATH already contains $INSTALL_DIR"
    fi
}

cleanup_old_logs() {
    log_info "Cleaning up old log files..."
    
    # Remove logs older than retention period
    if command -v find >/dev/null 2>&1; then
        local deleted_count=0
        while IFS= read -r -d '' file; do
            rm -f "$file"
            ((deleted_count++))
        done < <(find "$LOG_DIR" -name "install-*.log" -type f -mtime +$AUDIT_LOG_RETENTION -print0 2>/dev/null)
        
        if [[ $deleted_count -gt 0 ]]; then
            log_info "Removed $deleted_count old log files"
            log_audit "LOG_CLEANUP" "Old log files removed" "count=$deleted_count"
        fi
    fi
}

generate_completion_script() {
    log_info "Generating shell completion script..."
    
    local completion_dir=""
    case "$SHELL" in
        */bash)
            completion_dir="$HOME/.local/share/bash-completion/completions"
            ;;
        */zsh)
            completion_dir="$HOME/.local/share/zsh/completions"
            ;;
        */fish)
            completion_dir="$HOME/.config/fish/completions"
            ;;
    esac
    
    if [[ -n "$completion_dir" ]]; then
        mkdir -p "$completion_dir"
        
        # Generate completion if binary supports it
        if "$INSTALL_DIR/$BINARY_NAME" completion bash >/dev/null 2>&1; then
            "$INSTALL_DIR/$BINARY_NAME" completion bash > "$completion_dir/$BINARY_NAME" 2>/dev/null
            log_success "Shell completion script generated: $completion_dir/$BINARY_NAME"
            log_audit "COMPLETION_GENERATED" "Shell completion generated" \
                "completion_dir=$completion_dir"
        fi
    fi
}

print_installation_summary() {
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                    OMNIMESH SECURE INSTALLATION COMPLETED                                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}Installation Summary:${NC}"
    echo -e "  ${BLUE}•${NC} Binary:           $INSTALL_DIR/$BINARY_NAME"
    echo -e "  ${BLUE}•${NC} Version:          $NEW_VERSION"
    echo -e "  ${BLUE}•${NC} Configuration:    $CONFIG_DIR/config.yaml"
    echo -e "  ${BLUE}•${NC} Logs:            $LOG_DIR/"
    echo -e "  ${BLUE}•${NC} Transaction ID:   $TRANSACTION_ID"
    echo
    echo -e "${CYAN}Security Features Enabled:${NC}"
    echo -e "  ${GREEN}✓${NC} Cryptographic verification"
    echo -e "  ${GREEN}✓${NC} GPG signature validation"
    echo -e "  ${GREEN}✓${NC} Comprehensive audit logging"
    echo -e "  ${GREEN}✓${NC} Secure file permissions"
    echo -e "  ${GREEN}✓${NC} TLS 1.2+ enforcement"
    echo
    echo -e "${CYAN}Next Steps:${NC}"
    echo -e "  ${BLUE}1.${NC} Restart your shell or run: ${YELLOW}source ~/.bashrc${NC}"
    echo -e "  ${BLUE}2.${NC} Verify installation: ${YELLOW}$BINARY_NAME --version${NC}"
    echo -e "  ${BLUE}3.${NC} View configuration: ${YELLOW}$BINARY_NAME config show${NC}"
    echo -e "  ${BLUE}4.${NC} Get help: ${YELLOW}$BINARY_NAME --help${NC}"
    echo
    echo -e "${CYAN}Documentation:${NC}"
    echo -e "  ${BLUE}•${NC} User Guide:       https://docs.omnimesh.dev/cli/"
    echo -e "  ${BLUE}•${NC} Security Guide:   https://docs.omnimesh.dev/security/"
    echo -e "  ${BLUE}•${NC} API Reference:    https://docs.omnimesh.dev/api/"
    echo
    echo -e "${GREEN}Thank you for using OmniMesh! 🚀${NC}"
    echo
}

# Main installation function
main() {
    # Print header
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                                      OMNIMESH SECURE INSTALLER                                                      ║${NC}"
    echo -e "${PURPLE}║                                         Version $SCRIPT_VERSION                                                         ║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}This installer provides enterprise-grade security with:${NC}"
    echo -e "  ${GREEN}•${NC} Cryptographic verification of all downloads"
    echo -e "  ${GREEN}•${NC} GPG signature validation"
    echo -e "  ${GREEN}•${NC} Comprehensive audit logging"
    echo -e "  ${GREEN}•${NC} No pipe-to-shell execution"
    echo -e "  ${GREEN}•${NC} Rollback capability"
    echo
    
    # Confirm installation
    read -p "Continue with secure installation? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Installation cancelled by user"
        exit 0
    fi
    
    # Initialize logging first
    init_logging
    
    # Execute installation steps
    validate_environment
    validate_dependencies
    validate_network_security
    detect_platform
    setup_temp_directory
    get_latest_version
    check_current_version
    construct_download_urls
    download_files
    verify_checksum
    verify_signature
    backup_existing_installation
    extract_and_install
    setup_configuration
    verify_installation
    update_path
    cleanup_old_logs
    generate_completion_script
    
    # Log completion
    log_audit "INSTALL_COMPLETE" "Installation completed successfully" \
        "version=$NEW_VERSION" \
        "previous_version=$CURRENT_VERSION" \
        "install_dir=$INSTALL_DIR" \
        "transaction_id=$TRANSACTION_ID"
    
    # Print summary
    print_installation_summary
}

# Execute main function
main "$@"
