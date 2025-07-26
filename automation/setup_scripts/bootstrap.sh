#!/bin/bash

# 🌊 OMNIMESH One-Liner Installer
# Quick bootstrap script for immediate installation

set -euo pipefail

readonly REPO_URL="https://github.com/your-repo/omnimesh.git"
readonly TEMP_DIR="/tmp/omnimesh-install-$$"
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

show_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                     🌊 OMNIMESH QUICK INSTALLER                              ║${NC}"
    echo -e "${PURPLE}║                                                                              ║${NC}"
    echo -e "${PURPLE}║              Next-Generation Distributed AI Orchestration Platform          ║${NC}"
    echo -e "${PURPLE}║                        One Command to Install Everything                     ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

main() {
    show_banner
    
    echo -e "${BLUE}🚀 Starting OMNIMESH installation...${NC}"
    echo
    
    # Check for git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git is required but not installed.${NC}"
        echo "Please install git and try again."
        exit 1
    fi
    
    # Create temporary directory
    mkdir -p "$TEMP_DIR"
    echo -e "${BLUE}📁 Created temporary directory: $TEMP_DIR${NC}"
    
    # Clone repository
    echo -e "${BLUE}📥 Cloning OMNIMESH repository...${NC}"
    if git clone "$REPO_URL" "$TEMP_DIR" &> /dev/null; then
        echo -e "${GREEN}✅ Repository cloned successfully${NC}"
    else
        echo -e "${RED}❌ Failed to clone repository${NC}"
        echo "Please check your internet connection and try again."
        exit 1
    fi
    
    # Change to repository directory
    cd "$TEMP_DIR"
    
    # Make installer executable
    chmod +x install-omnimesh.sh
    
    # Run the main installer with all arguments
    echo -e "${BLUE}🔧 Running OMNIMESH Universal Installer...${NC}"
    echo
    exec ./install-omnimesh.sh "$@"
}

# Run with all arguments passed to this script
main "$@"
