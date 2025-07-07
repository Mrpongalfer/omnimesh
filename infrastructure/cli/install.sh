#!/bin/bash

# omni-cli Installation Script
# This script installs the omni-cli tool for OmniTide Compute Fabric

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="Mrpongalfer/omnimesh"
BINARY_NAME="omni-cli"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.config/omni-cli"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS and architecture
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
        x86_64)
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
    
    PLATFORM="${OS}-${ARCH}"
    log_info "Detected platform: $PLATFORM"
}

# Get latest release version
get_latest_version() {
    log_info "Fetching latest release information..."
    
    # For now, use a default version since the releases might not be set up yet
    VERSION="v1.0.0"
    
    # In production, you would uncomment this to get the actual latest release:
    # VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    
    if [ -z "$VERSION" ]; then
        log_error "Failed to get latest version"
        exit 1
    fi
    
    log_info "Latest version: $VERSION"
}

# Download and install binary
install_binary() {
    log_info "Installing $BINARY_NAME..."
    
    # Create temporary directory
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT
    
    # For now, we'll build from source since pre-built binaries might not be available
    if command -v go >/dev/null 2>&1; then
        log_info "Building from source..."
        
        # Clone repository
        cd "$TMP_DIR"
        git clone "https://github.com/$GITHUB_REPO.git" 
        cd omnimesh/infrastructure/cli
        
        # Build binary
        go build -o "$BINARY_NAME" .
        
        # Install binary
        sudo mv "$BINARY_NAME" "$INSTALL_DIR/"
        sudo chmod +x "$INSTALL_DIR/$BINARY_NAME"
        
    else
        log_error "Go is not installed. Please install Go 1.23+ or download a pre-built binary."
        exit 1
    fi
    
    log_success "$BINARY_NAME installed to $INSTALL_DIR"
}

# Create configuration directory
setup_config() {
    log_info "Setting up configuration..."
    
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        log_info "Created configuration directory: $CONFIG_DIR"
    fi
    
    # Create sample configuration if it doesn't exist
    if [ ! -f "$CONFIG_DIR/omni-cli.yaml" ]; then
        log_info "Creating sample configuration..."
        "$INSTALL_DIR/$BINARY_NAME" config init
        log_success "Sample configuration created at $CONFIG_DIR/omni-cli.yaml"
        log_warn "Please edit the configuration file with your project details"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    if command -v "$BINARY_NAME" >/dev/null 2>&1; then
        VERSION_OUTPUT=$("$BINARY_NAME" --version 2>/dev/null || echo "unknown")
        log_success "$BINARY_NAME is installed and working"
        log_info "Version: $VERSION_OUTPUT"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for required tools
    if ! command -v kubectl >/dev/null 2>&1; then
        missing_deps+=("kubectl")
    fi
    
    if ! command -v terraform >/dev/null 2>&1; then
        missing_deps+=("terraform")
    fi
    
    if ! command -v docker >/dev/null 2>&1; then
        missing_deps+=("docker")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_warn "The following dependencies are missing:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        log_warn "omni-cli will have limited functionality without these tools"
    else
        log_success "All dependencies are installed"
    fi
}

# Main installation function
main() {
    echo "🌊 OmniTide omni-cli Installation Script"
    echo "========================================"
    
    detect_platform
    get_latest_version
    install_binary
    setup_config
    verify_installation
    check_dependencies
    
    echo ""
    log_success "Installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit your configuration: $CONFIG_DIR/omni-cli.yaml"
    echo "2. Run 'omni-cli --help' to see available commands"
    echo "3. Start with 'omni-cli infra up --env dev' to provision infrastructure"
    echo ""
    echo "For more information, visit: https://github.com/$GITHUB_REPO"
}

# Run installation
main "$@"
