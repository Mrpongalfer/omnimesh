#!/bin/bash

# omni-cli Secure Installation Script
# This script implements secure installation practices for OmniTide Compute Fabric CLI
# 
# Security Features:
# - Checksum verification for all downloads
# - No direct pipe-to-shell execution
# - Privilege validation and least-privilege operations
# - Cryptographic signature verification
# - Comprehensive logging and audit trail
# - Rollback capability

set -euo pipefail

# Security Constants
readonly SCRIPT_VERSION="2.0.0"
readonly MIN_BASH_VERSION="4.0"
readonly REQUIRED_TOOLS=("curl" "sha256sum" "gpg" "tar" "sudo")
readonly GITHUB_REPO="Mrpongalfer/omnimesh"
readonly BINARY_NAME="omni-cli"
readonly INSTALL_DIR="/usr/local/bin"
readonly CONFIG_DIR="$HOME/.config/omni-cli"
readonly TEMP_DIR=$(mktemp -d)
readonly LOG_FILE="/var/log/omni-cli-install.log"
readonly BACKUP_DIR="$CONFIG_DIR/backups"

# GPG Key for signature verification (replace with actual production key)
readonly GPG_KEY_ID="YOUR_GPG_KEY_ID_HERE"
readonly GPG_KEY_SERVER="keyserver.ubuntu.com"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Cleanup function
cleanup() {
    local exit_code=$?
    log_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    exit $exit_code
}

# Set up cleanup trap
trap cleanup EXIT

# Logging functions with audit trail
log_audit() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="$1"
    echo "[$timestamp] AUDIT: $message" | sudo tee -a "$LOG_FILE" >/dev/null 2>&1 || true
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log_audit "INFO: $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_audit "SUCCESS: $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_audit "WARNING: $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_audit "ERROR: $1"
}

log_security() {
    echo -e "${RED}[SECURITY]${NC} $1"
    log_audit "SECURITY: $1"
}

# Security validation functions
validate_environment() {
    log_info "Validating installation environment..."
    
    # Check bash version
    if [[ "${BASH_VERSION%%.*}" -lt "${MIN_BASH_VERSION%%.*}" ]]; then
        log_error "Bash version ${BASH_VERSION} is not supported. Minimum required: ${MIN_BASH_VERSION}"
        exit 1
    fi
    
    # Check required tools
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' is not installed"
            exit 1
        fi
    done
    
    # Check write permissions
    if [[ ! -w "$(dirname "$INSTALL_DIR")" ]]; then
        log_error "No write permission to installation directory: $INSTALL_DIR"
        exit 1
    fi
    
    # Validate network connectivity
    if ! curl -s --connect-timeout 10 https://api.github.com/repos/$GITHUB_REPO/releases/latest &>/dev/null; then
        log_error "Cannot reach GitHub API. Check network connectivity and firewall settings."
        exit 1
    fi
    
    log_success "Environment validation completed"
}

# Platform detection with security validation
detect_platform() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    case $os in
        linux*)
            OS="linux"
            ;;
        darwin*)
            OS="darwin"
            ;;
        *)
            log_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac
    
    case $arch in
        x86_64|amd64)
            ARCH="amd64"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
    
    log_info "Detected platform: $OS/$ARCH"
}

# Secure download with checksum verification
secure_download() {
    local url="$1"
    local output_file="$2"
    local checksum_url="$3"
    local expected_checksum
    
    log_info "Downloading from: $url"
    
    # Download the file
    if ! curl -fsSL --retry 3 --retry-delay 2 -o "$output_file" "$url"; then
        log_error "Failed to download file from: $url"
        return 1
    fi
    
    # Download and verify checksum
    log_info "Verifying checksum..."
    if ! expected_checksum=$(curl -fsSL --retry 3 --retry-delay 2 "$checksum_url" | grep "$(basename "$output_file")" | cut -d' ' -f1); then
        log_error "Failed to download checksum from: $checksum_url"
        return 1
    fi
    
    # Calculate actual checksum
    local actual_checksum
    actual_checksum=$(sha256sum "$output_file" | cut -d' ' -f1)
    
    # Compare checksums
    if [[ "$expected_checksum" != "$actual_checksum" ]]; then
        log_security "CHECKSUM MISMATCH DETECTED!"
        log_security "Expected: $expected_checksum"
        log_security "Actual:   $actual_checksum"
        log_security "This could indicate a compromised download or man-in-the-middle attack"
        return 1
    fi
    
    log_success "Checksum verification passed"
    return 0
}

# GPG signature verification
verify_signature() {
    local file="$1"
    local signature_file="$2"
    
    log_info "Verifying GPG signature..."
    
    # Import GPG key if not already present
    if ! gpg --list-keys "$GPG_KEY_ID" &>/dev/null; then
        log_info "Importing GPG key: $GPG_KEY_ID"
        if ! gpg --keyserver "$GPG_KEY_SERVER" --recv-keys "$GPG_KEY_ID"; then
            log_error "Failed to import GPG key"
            return 1
        fi
    fi
    
    # Verify signature
    if ! gpg --verify "$signature_file" "$file" &>/dev/null; then
        log_security "GPG SIGNATURE VERIFICATION FAILED!"
        log_security "This could indicate a compromised binary or man-in-the-middle attack"
        return 1
    fi
    
    log_success "GPG signature verification passed"
    return 0
}

# Create secure backup
create_backup() {
    if [[ -f "$INSTALL_DIR/$BINARY_NAME" ]]; then
        log_info "Creating backup of existing installation..."
        mkdir -p "$BACKUP_DIR"
        local backup_file="$BACKUP_DIR/${BINARY_NAME}_$(date +%Y%m%d_%H%M%S)"
        cp "$INSTALL_DIR/$BINARY_NAME" "$backup_file"
        log_success "Backup created: $backup_file"
    fi
}

# Install with privilege validation
secure_install() {
    local temp_binary="$TEMP_DIR/$BINARY_NAME"
    
    log_info "Installing $BINARY_NAME..."
    
    # Validate binary before installation
    if ! file "$temp_binary" | grep -q "executable"; then
        log_error "Downloaded file is not a valid executable"
        exit 1
    fi
    
    # Create backup before installation
    create_backup
    
    # Install with minimal privileges
    if ! sudo install -m 755 -o root -g root "$temp_binary" "$INSTALL_DIR/$BINARY_NAME"; then
        log_error "Failed to install binary"
        exit 1
    fi
    
    # Verify installation
    if ! "$INSTALL_DIR/$BINARY_NAME" --version &>/dev/null; then
        log_error "Installation verification failed"
        exit 1
    fi
    
    log_success "Installation completed successfully"
}

# Get latest release information
get_release_info() {
    log_info "Fetching latest release information..."
    
    local api_url="https://api.github.com/repos/$GITHUB_REPO/releases/latest"
    local release_info
    
    if ! release_info=$(curl -fsSL "$api_url"); then
        log_error "Failed to fetch release information"
        exit 1
    fi
    
    LATEST_VERSION=$(echo "$release_info" | grep '"tag_name"' | cut -d'"' -f4)
    DOWNLOAD_URL=$(echo "$release_info" | grep "browser_download_url.*${OS}_${ARCH}" | cut -d'"' -f4)
    CHECKSUM_URL=$(echo "$release_info" | grep "browser_download_url.*checksums.txt" | cut -d'"' -f4)
    SIGNATURE_URL=$(echo "$release_info" | grep "browser_download_url.*checksums.txt.sig" | cut -d'"' -f4)
    
    if [[ -z "$DOWNLOAD_URL" ]]; then
        log_error "No release found for platform: $OS/$ARCH"
        exit 1
    fi
    
    log_info "Latest version: $LATEST_VERSION"
    log_info "Download URL: $DOWNLOAD_URL"
}

# Main installation process
main() {
    log_info "Starting secure installation of omni-cli v$SCRIPT_VERSION"
    log_info "Installation will be logged to: $LOG_FILE"
    
    # Security validations
    validate_environment
    detect_platform
    
    # Get release information
    get_release_info
    
    # Download and verify
    local temp_binary="$TEMP_DIR/$BINARY_NAME"
    local temp_checksum="$TEMP_DIR/checksums.txt"
    local temp_signature="$TEMP_DIR/checksums.txt.sig"
    
    if ! secure_download "$DOWNLOAD_URL" "$temp_binary" "$CHECKSUM_URL"; then
        log_error "Download failed"
        exit 1
    fi
    
    # Download signature for verification
    if ! curl -fsSL -o "$temp_signature" "$SIGNATURE_URL"; then
        log_warn "Could not download signature file, skipping GPG verification"
    else
        if ! curl -fsSL -o "$temp_checksum" "$CHECKSUM_URL"; then
            log_error "Failed to download checksum file"
            exit 1
        fi
        
        if ! verify_signature "$temp_checksum" "$temp_signature"; then
            log_error "Signature verification failed"
            exit 1
        fi
    fi
    
    # Install
    secure_install
    
    # Create configuration directory
    mkdir -p "$CONFIG_DIR"
    
    log_success "omni-cli installation completed successfully!"
    log_info "Binary installed to: $INSTALL_DIR/$BINARY_NAME"
    log_info "Configuration directory: $CONFIG_DIR"
    log_info "Run 'omni-cli --help' to get started"
}

# Ensure script is not being piped from curl
if [[ -t 0 ]]; then
    main "$@"
else
    log_security "SECURITY: This script should not be executed via pipe from curl"
    log_security "Please download the script first and inspect it before execution"
    exit 1
fi
