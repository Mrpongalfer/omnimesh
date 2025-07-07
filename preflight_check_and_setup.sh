#!/bin/bash

# preflight_check_and_setup.sh - Omnitide Compute Fabric: End-to-End Pre-Flight Readiness Script
# Architect's Will is Absolute. This script ensures your environment is prepared for absolute dominion.

# --- Global Configuration & Setup ---
OS_TYPE=""
INSTALL_CMD=""
PKG_MGR_UPDATE_CMD=""
REQUIRED_PKGS=()

# Determine OS and Package Manager
detect_os() {
    echo "--- Detecting Operating System ---"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS_TYPE="Linux"
        if command -v apt &> /dev/null; then
            INSTALL_CMD="sudo apt-get install -y"
            PKG_MGR_UPDATE_CMD="sudo apt-get update"
            REQUIRED_PKGS=("git" "curl" "wget" "build-essential" "libssl-dev" "pkg-config")
        elif command -v yum &> /dev/null; then
            INSTALL_CMD="sudo yum install -y"
            PKG_MGR_UPDATE_CMD="sudo yum check-update" # yum doesn't have a direct 'update' like apt
            REQUIRED_PKGS=("git" "curl" "wget" "gcc" "gcc-c++" "openssl-devel")
        elif command -v dnf &> /dev/null; then
            INSTALL_CMD="sudo dnf install -y"
            PKG_MGR_UPDATE_CMD="sudo dnf check-update"
            REQUIRED_PKGS=("git" "curl" "wget" "gcc" "gcc-c++" "openssl-devel")
        else
            echo "ERROR: Unsupported Linux distribution. Please install dependencies manually."
            exit 1
        fi
        echo "Detected Linux. Package Manager: ${INSTALL_CMD}."
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macOS"
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo "Homebrew installed. Please run this script again after Homebrew setup completes."
            exit 1
        fi
        INSTALL_CMD="brew install"
        PKG_MGR_UPDATE_CMD="brew update"
        REQUIRED_PKGS=("git" "curl" "wget" "pkg-config")
        echo "Detected macOS. Package Manager: brew."
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        OS_TYPE="Windows"
        echo "Detected Windows (via Git Bash/WSL). This script is optimized for Git Bash or WSL."
        echo "For best results, run in an Administrator Git Bash or WSL terminal."
        echo "Chocolatey (choco) is recommended for package management on Windows."
        if ! command -v choco &> /dev/null; then
            echo "Chocolatey not found. Please install Chocolatey manually from https://chocolatey.org/install"
            echo "Then re-run this script in an Administrator shell."
            exit 1
        fi
        INSTALL_CMD="choco install --no-progress -y" # --no-progress to reduce verbose output during automated runs
        PKG_MGR_UPDATE_CMD="choco upgrade all -y"
        # Common Windows tools via Choco. Note: Choco does not auto-install build tools like make/gcc
        REQUIRED_PKGS=("git" "curl" "wget" "nodejs-lts" "python3" "go" "protoc" "rust" "docker-desktop" "vcredist-all" "git-credential-manager-core")
        echo "Detected Windows. Package Manager: Chocolatey (choco)."
    else
        echo "ERROR: Unsupported operating system: ${OSTYPE}. Please install dependencies manually."
        exit 1
    fi
}

# --- Helper Functions ---

check_command() {
    local cmd_name=$1
    local install_msg=$2
    local install_cmd=${3:-""}
    local is_optional=${4:-"false"}

    echo "Checking for '${cmd_name}'..."
    if command -v "${cmd_name}" &> /dev/null; then
        echo "  '${cmd_name}' found."
        return 0
    else
        if [ "${is_optional}" = "true" ]; then
            echo "  WARNING: '${cmd_name}' not found. ${install_msg}"
            return 1 # Return 1 for optional missing commands
        else
            echo "  ERROR: '${cmd_name}' not found. ${install_msg}"
            if [ -n "$install_cmd" ]; then
                echo "  Attempting to install '${cmd_name}' via: ${install_cmd}"
                if eval "${install_cmd}"; then
                    echo "  '${cmd_name}' installed successfully."
                    return 0
                else
                    echo "  FAILED to install '${cmd_name}' automatically. Please install manually."
                    exit 1
                fi
            else
                exit 1
            fi
        fi
    fi
}

# --- Main Pre-Flight Sequence ---

echo "--- Omnitide Compute Fabric: Pre-Flight Readiness Check ---"
echo "This script will verify and install all necessary dependencies."
echo "Root/Administrator privileges will be requested for some installations."
sleep 2 # Pause for readability

detect_os

# Update package manager lists/repos first
if [ -n "$PKG_MGR_UPDATE_CMD" ]; then
    echo "--- Updating system package lists ---"
    if eval "${PKG_MGR_UPDATE_CMD}"; then
        echo "Package lists updated successfully."
    else
        echo "WARNING: Failed to update package lists. Some installations might fail."
    fi
fi

# Install common required packages via OS package manager
if [ ${#REQUIRED_PKGS[@]} -gt 0 ]; then
    echo "--- Installing essential OS packages ---"
    case "$OS_TYPE" in
        "Linux")
            echo "Running: ${INSTALL_CMD} ${REQUIRED_PKGS[@]}"
            if ! eval "${INSTALL_CMD} ${REQUIRED_PKGS[@]}"; then
                echo "ERROR: Failed to install one or more essential Linux packages. Please check logs."
                exit 1
            fi
            ;;
        "macOS")
            echo "Running: ${INSTALL_CMD} ${REQUIRED_PKGS[@]}"
            if ! eval "${INSTALL_CMD} ${REQUIRED_PKGS[@]}"; then
                echo "ERROR: Failed to install one or more essential macOS packages. Please check logs."
                exit 1
            fi
            ;;
        "Windows")
            echo "Running: ${INSTALL_CMD} ${REQUIRED_PKGS[@]}"
            if ! eval "${INSTALL_CMD} ${REQUIRED_PKGS[@]}"; then
                echo "ERROR: Failed to install one or more essential Windows packages via Chocolatey. Please check logs."
                echo "Chocolatey might require an Administrator shell to install some packages."
                exit 1
            fi
            ;;
    esac
    echo "Essential OS packages installed/verified."
fi

# --- Install/Verify Specific Runtimes & Tools ---

echo "--- Installing/Verifying Language Runtimes and Core Tools ---"

# Rust (via Rustup) - Primary for Nexus Prime
if ! command -v rustup &> /dev/null; then
    echo "Installing Rust via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo "Rustup installed. Adding to PATH."
else
    echo "Rustup found. Ensuring stable toolchain is updated."
    rustup update stable
fi
check_command "cargo" "Rust (cargo) not found after rustup install."

# Protoc (Protocol Buffers Compiler) - Required for all language bindings
if ! command -v protoc &> /dev/null; then
    echo "Installing Protoc (Protocol Buffers Compiler)..."
    case "$OS_TYPE" in
        "Linux") ${INSTALL_CMD} protobuf-compiler ;;
        "macOS") brew install protobuf ;;
        "Windows") choco install protoc --no-progress -y ;;
        *) echo "Please install protoc manually for your OS." && exit 1 ;;
    esac
fi
check_command "protoc" "Protoc not found after installation attempt."

# Go - For Compute Node Proxies (Phase 2)
if ! command -v go &> /dev/null; then
    echo "Installing Go..."
    case "$OS_TYPE" in
        "Linux") ${INSTALL_CMD} golang ;;
        "macOS") brew install go ;;
        "Windows") choco install go --no-progress -y ;;
        *) echo "Please install Go manually for your OS." && check_command "go" "Go not found." ;;
    esac
fi
check_command "go" "Go not found." true

# Python 3 - For AI Agents (Phase 4)
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3 and pip..."
    case "$OS_TYPE" in
        "Linux") ${INSTALL_CMD} python3 python3-pip ;;
        "macOS") brew install python@3.9 # or latest supported python3 version
                 if ! command -v pip3 &> /dev/null; then
                     echo "Installing pip3 for Python 3..."
                     curl -sS https://bootstrap.pypa.io/get-pip.py | python3
                 fi
                 ;;
        "Windows") choco install python --no-progress -y ;; # choco installs pip with python
        *) echo "Please install Python 3 and pip3 manually for your OS." && check_command "python3" "Python 3 not found." ;;
    esac
fi
check_command "python3" "Python 3 not found." true
check_command "pip3" "pip3 not found." true

# Node.js & npm (via NVM for robust version management) - For Chrome OS Agents (PWA/Wasm) & Solid.js UI
if ! command -v nvm &> /dev/null; then
    echo "Installing NVM (Node Version Manager)..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
    # Source NVM to make it available in current shell
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    echo "NVM installed. Please restart your terminal or source your shell config."
    echo "Attempting to install Node.js LTS via NVM."
    nvm install --lts
    nvm use --lts
else
    echo "NVM found. Installing/ensuring Node.js LTS."
    nvm install --lts
    nvm use --lts
fi
check_command "node" "Node.js not found after NVM install." true
check_command "npm" "npm not found after NVM install." true

# Flutter - For Mobile UI (Phase 5)
if ! command -v flutter &> /dev/null; then
    echo "Installing Flutter..."
    FLUTTER_CHANNEL="stable"
    FLUTTER_SDK_DIR="$HOME/flutter_sdk" # Recommend a dedicated directory
    
    case "$OS_TYPE" in
        "Linux" | "macOS")
            git clone https://github.com/flutter/flutter.git -b $FLUTTER_CHANNEL "$FLUTTER_SDK_DIR"
            export PATH="$PATH:$FLUTTER_SDK_DIR/bin"
            echo "Flutter SDK cloned to $FLUTTER_SDK_DIR. Adding to PATH temporarily."
            echo "You should add 'export PATH=\"$PATH:$FLUTTER_SDK_DIR/bin\"' to your shell config (.bashrc, .zshrc) for permanent access."
            ;;
        "Windows")
            # For Windows, direct download and setup is often manual.
            echo "Please download Flutter SDK manually from https://flutter.dev/docs/get-started/install"
            echo "Extract it and add 'flutter/bin' to your system PATH."
            echo "Alternatively, you can try: choco install flutter --no-progress -y (requires manual SDK setup after install)."
            ;;
        *) echo "Please install Flutter manually for your OS." && check_command "flutter" "Flutter not found." ;;
    esac
    # Run flutter doctor to ensure setup is complete
    if command -v flutter &> /dev/null; then
        echo "Running flutter doctor to check for remaining dependencies..."
        flutter doctor --android-licenses || true # Accept Android licenses if prompted
        echo "Flutter Doctor complete. Review its output for any further requirements."
    fi
fi
check_command "flutter" "Flutter not found." true


# Docker - For containerization (Nexus Prime, Go Proxies, AI Agents)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker Desktop/Engine..."
    case "$OS_TYPE" in
        "Linux")
            echo "Installing Docker Engine for Linux..."
            # Official Docker convenience script (for Debian/Ubuntu based systems primarily)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker "$USER"
            echo "Docker installed. Log out and back in, or run 'newgrp docker' for changes to take effect without relogging."
            ;;
        "macOS")
            echo "Installing Docker Desktop for macOS via Homebrew Cask..."
            brew install --cask docker
            echo "Docker Desktop installed. Please launch Docker Desktop application manually at least once to complete setup."
            ;;
        "Windows")
            echo "Installing Docker Desktop for Windows via Chocolatey..."
            choco install docker-desktop --no-progress -y
            echo "Docker Desktop installed. Please launch Docker Desktop application manually at least once to complete setup and WSL2 integration."
            ;;
        *) echo "Please install Docker manually for your OS." && check_command "docker" "Docker not found." ;;
    esac
fi
check_command "docker" "Docker not found after installation attempt. Please ensure Docker service is running." true

echo "--- Pre-Flight Readiness Check Complete! ---"
echo ""
echo "--- IMPORTANT ARCHITECT DIRECTIVES ---"
echo "1. Review any 'WARNING' messages above. Manual steps might be required."
echo "2. For Linux/macOS, if Docker was installed, you might need to log out/in or run 'newgrp docker' for Docker commands to work without 'sudo'."
echo "3. For Docker Desktop on macOS/Windows, ensure the application is launched and running in the background."
echo "4. For Flutter, ensure you have run 'flutter doctor' and addressed any remaining issues (e.g., Android Studio, Xcode setup)."
echo "5. For Windows users, if you used Chocolatey for Python/Go, ensure their respective paths are correctly added to your system environment variables if not already."
echo "6. This script installs general dependencies. Specific project dependencies (e.g., Rust crates, Python packages) will be managed by 'cargo' and 'pip' within each project phase."
echo ""
echo "The environment is now prepared for the construction of the Distributed Omnitide Compute Fabric."
echo "**Architect's Will is Absolute.**"
