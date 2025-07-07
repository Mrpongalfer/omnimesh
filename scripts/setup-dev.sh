#!/bin/bash
# Setup development environment for OmniTide Compute Fabric

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up OmniTide development environment...${NC}"

# Check if running on supported OS
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "${GREEN}✓ Linux detected${NC}"
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GREEN}✓ macOS detected${NC}"
        OS="macos"
    else
        echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
        exit 1
    fi
}

# Install Rust
install_rust() {
    if command -v rustc &> /dev/null; then
        echo -e "${GREEN}✓ Rust already installed: $(rustc --version)${NC}"
    else
        echo -e "${BLUE}📦 Installing Rust...${NC}"
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
        echo -e "${GREEN}✓ Rust installed${NC}"
    fi
    
    # Install Rust components
    echo -e "${BLUE}📦 Installing Rust components...${NC}"
    rustup component add clippy rustfmt
    
    # Install cargo tools
    echo -e "${BLUE}📦 Installing Cargo tools...${NC}"
    cargo install cargo-audit cargo-deny cargo-watch cargo-tarpaulin cargo-edit
}

# Install Go
install_go() {
    if command -v go &> /dev/null; then
        echo -e "${GREEN}✓ Go already installed: $(go version)${NC}"
    else
        echo -e "${BLUE}📦 Installing Go...${NC}"
        if [[ "$OS" == "linux" ]]; then
            GO_VERSION="1.23.0"
            wget -q "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
            sudo rm -rf /usr/local/go
            sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
            rm "go${GO_VERSION}.linux-amd64.tar.gz"
            
            # Add Go to PATH
            echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
            export PATH=$PATH:/usr/local/go/bin
        elif [[ "$OS" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install go
            else
                echo -e "${RED}❌ Please install Homebrew first or install Go manually${NC}"
                exit 1
            fi
        fi
        echo -e "${GREEN}✓ Go installed${NC}"
    fi
    
    # Install Go tools
    echo -e "${BLUE}📦 Installing Go tools...${NC}"
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
    go install github.com/securecodewarrior/sast-scanner/cmd/gosec@latest
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
}

# Install Protocol Buffers
install_protobuf() {
    if command -v protoc &> /dev/null; then
        echo -e "${GREEN}✓ protoc already installed: $(protoc --version)${NC}"
    else
        echo -e "${BLUE}📦 Installing Protocol Buffers...${NC}"
        if [[ "$OS" == "linux" ]]; then
            sudo apt-get update
            sudo apt-get install -y protobuf-compiler
        elif [[ "$OS" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install protobuf
            else
                echo -e "${RED}❌ Please install Homebrew first${NC}"
                exit 1
            fi
        fi
        echo -e "${GREEN}✓ Protocol Buffers installed${NC}"
    fi
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓ Docker already installed: $(docker --version)${NC}"
    else
        echo -e "${BLUE}📦 Installing Docker...${NC}"
        if [[ "$OS" == "linux" ]]; then
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
            echo -e "${YELLOW}⚠️  Please log out and back in for Docker group changes to take effect${NC}"
        elif [[ "$OS" == "macos" ]]; then
            echo -e "${YELLOW}⚠️  Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop${NC}"
        fi
        echo -e "${GREEN}✓ Docker installation initiated${NC}"
    fi
}

# Install Node.js (for UI development)
install_nodejs() {
    if command -v node &> /dev/null; then
        echo -e "${GREEN}✓ Node.js already installed: $(node --version)${NC}"
    else
        echo -e "${BLUE}📦 Installing Node.js...${NC}"
        if [[ "$OS" == "linux" ]]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [[ "$OS" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install node
            else
                echo -e "${RED}❌ Please install Homebrew first${NC}"
                exit 1
            fi
        fi
        echo -e "${GREEN}✓ Node.js installed${NC}"
    fi
    
    # Install pnpm
    if ! command -v pnpm &> /dev/null; then
        echo -e "${BLUE}📦 Installing pnpm...${NC}"
        npm install -g pnpm
        echo -e "${GREEN}✓ pnpm installed${NC}"
    fi
}

# Install development tools
install_dev_tools() {
    echo -e "${BLUE}📦 Installing development tools...${NC}"
    
    # Install pre-commit
    if ! command -v pre-commit &> /dev/null; then
        if command -v pip3 &> /dev/null; then
            pip3 install pre-commit
        elif command -v pip &> /dev/null; then
            pip install pre-commit
        else
            echo -e "${YELLOW}⚠️  pip not found, please install pre-commit manually${NC}"
        fi
    fi
    
    # Install commitlint
    if ! command -v commitlint &> /dev/null; then
        npm install -g @commitlint/cli @commitlint/config-conventional
    fi
    
    echo -e "${GREEN}✓ Development tools installed${NC}"
}

# Setup project structure
setup_project() {
    echo -e "${BLUE}📁 Setting up project structure...${NC}"
    
    # Create directories
    mkdir -p data logs coverage docs/src
    
    # Setup git hooks
    if [ -d ".git" ]; then
        echo -e "${BLUE}🔧 Setting up git hooks...${NC}"
        if command -v pre-commit &> /dev/null; then
            pre-commit install
        fi
        
        # Create commit message template
        cat > .gitmessage << EOF
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Type should be one of:
# feat: A new feature
# fix: A bug fix
# docs: Documentation only changes
# style: Changes that do not affect the meaning of the code
# refactor: A code change that neither fixes a bug nor adds a feature
# perf: A code change that improves performance
# test: Adding missing tests or correcting existing tests
# chore: Changes to the build process or auxiliary tools
EOF
        git config commit.template .gitmessage
    fi
    
    echo -e "${GREEN}✓ Project structure setup complete${NC}"
}

# Verify installation
verify_installation() {
    echo -e "${BLUE}🔍 Verifying installation...${NC}"
    
    local errors=0
    
    # Check Rust
    if ! command -v rustc &> /dev/null; then
        echo -e "${RED}❌ Rust not found${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Rust: $(rustc --version)${NC}"
    fi
    
    # Check Go
    if ! command -v go &> /dev/null; then
        echo -e "${RED}❌ Go not found${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Go: $(go version)${NC}"
    fi
    
    # Check protoc
    if ! command -v protoc &> /dev/null; then
        echo -e "${RED}❌ protoc not found${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ protoc: $(protoc --version)${NC}"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found (optional for development)${NC}"
    else
        echo -e "${GREEN}✓ Docker: $(docker --version)${NC}"
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}🎉 All essential tools installed successfully!${NC}"
        echo -e "${BLUE}💡 Next steps:${NC}"
        echo -e "  1. Run 'make build' to build all components"
        echo -e "  2. Run 'make test' to run tests"
        echo -e "  3. Run 'make run' to start the system"
        echo -e "  4. Check 'make help' for more commands"
    else
        echo -e "${RED}❌ $errors essential tools missing. Please resolve the errors above.${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🔧 OmniTide Development Environment Setup${NC}"
    echo -e "${BLUE}=========================================${NC}"
    
    check_os
    install_rust
    install_go
    install_protobuf
    install_docker
    install_nodejs
    install_dev_tools
    setup_project
    verify_installation
    
    echo -e "${GREEN}🎊 Setup complete! Happy coding!${NC}"
}

# Run main function
main "$@"
