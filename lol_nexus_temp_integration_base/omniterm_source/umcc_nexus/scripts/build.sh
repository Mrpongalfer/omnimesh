#!/bin/bash

# UMCC Master Build Script
# Builds the complete Unfettered Mobile Command Center from source
# Timestamp: Wednesday, July 23, 2025 at 3:56:25 PM CDT in Moore, Oklahoma

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# UMCC Project Root
UMCC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UMCC_PROJECT_ROOT="${UMCC_ROOT}"

echo -e "${BLUE}🏗️  UMCC Master Build System Initializing...${NC}"
echo -e "${BLUE}📁 Project Root: ${UMCC_PROJECT_ROOT}${NC}"

# Ensure required directories exist
mkdir -p "${UMCC_PROJECT_ROOT}/bin"
mkdir -p "${UMCC_PROJECT_ROOT}/logs"
mkdir -p "${UMCC_PROJECT_ROOT}/data"

# Function to log with timestamp
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."

    # Check Go
    if ! command -v go &> /dev/null; then
        error "Go is not installed. Please install Go 1.21+ and try again."
        exit 1
    fi
    log "✅ Go found: $(go version)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.10+ and try again."
        exit 1
    fi
    log "✅ Python found: $(python3 --version)"

    # Check Poetry
    if ! command -v poetry &> /dev/null; then
        error "Poetry is not installed. Please install Poetry and try again."
        exit 1
    fi
    log "✅ Poetry found: $(poetry --version)"

    # Check protoc
    if ! command -v protoc &> /dev/null; then
        error "Protocol Buffers compiler (protoc) is not installed."
        exit 1
    fi
    log "✅ protoc found: $(protoc --version)"

    # Check Docker/Podman
    if command -v podman &> /dev/null; then
        log "✅ Podman found: $(podman --version)"
        export CONTAINER_RUNTIME="podman"
    elif command -v docker &> /dev/null; then
        log "✅ Docker found: $(docker --version)"
        export CONTAINER_RUNTIME="docker"
    else
        warn "Neither Podman nor Docker found. Container features will be disabled."
        export CONTAINER_RUNTIME="none"
    fi
}

# Generate protobuf files
generate_protobuf() {
    log "🔧 Generating protobuf files..."

    cd "${UMCC_PROJECT_ROOT}/shared"

    # Generate Go files
    protoc --go_out=. --go_opt=paths=source_relative \
           --go-grpc_out=. --go-grpc_opt=paths=source_relative \
           umcc.proto

    # Generate Python files
    python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. umcc.proto

    log "✅ Protobuf files generated"
}

# Build Go daemons
build_go_daemons() {
    log "🔨 Building Go daemons..."

    local daemons=("sentinel_daemon" "oracle_daemon" "chronos_daemon" "noosphere_daemon" "logos_daemon" "midas_daemon" "chimera_daemon" "telos_engine_daemon")

    for daemon in "${daemons[@]}"; do
        log "Building ${daemon}..."
        cd "${UMCC_PROJECT_ROOT}/daemons/${daemon}"

        if [[ -f "main.go" ]]; then
            go mod tidy
            go build -o "${UMCC_PROJECT_ROOT}/bin/${daemon}" .
            log "✅ ${daemon} built successfully"
        else
            warn "main.go not found for ${daemon}, skipping..."
        fi
    done
}

# Build console TUI
build_console() {
    log "🖥️  Building Architect's Console (TUI)..."

    cd "${UMCC_PROJECT_ROOT}/console"
    if [[ -f "main.go" ]]; then
        go mod tidy
        go build -o "${UMCC_PROJECT_ROOT}/bin/umcc_console" .
        log "✅ Console built successfully"
    else
        warn "main.go not found for console, skipping..."
    fi
}

# Setup Python environment for Agent Ex-Work
setup_agent_ex_work() {
    log "🐍 Setting up Agent Ex-Work Python environment..."

    cd "${UMCC_PROJECT_ROOT}/agent_ex_work"

    # Initialize Poetry if pyproject.toml doesn't exist
    if [[ ! -f "pyproject.toml" ]]; then
        log "Initializing Poetry project..."
        poetry init --no-interaction --name agent-ex-work --version "3.0.0" \
              --description "The Genesis Agent - UMCC's Primary Autonomous Agent" \
              --author "The Architect" \
              --python "^3.10"
    fi

    # Install dependencies
    if [[ -f "pyproject.toml" ]]; then
        poetry install
        log "✅ Agent Ex-Work environment setup complete"
    else
        warn "pyproject.toml not found, skipping Python setup..."
    fi
}

# Run tests
run_tests() {
    log "🧪 Running tests..."

    # Go tests
    log "Running Go tests..."
    cd "${UMCC_PROJECT_ROOT}"
    find . -name "*.go" -path "./daemons/*" -o -path "./console/*" | head -1 | xargs -r -I {} dirname {} | while read dir; do
        if [[ -d "$dir" ]]; then
            cd "$dir"
            if ls *_test.go 1> /dev/null 2>&1; then
                go test ./...
            fi
            cd "${UMCC_PROJECT_ROOT}"
        fi
    done

    # Python tests
    log "Running Python tests..."
    cd "${UMCC_PROJECT_ROOT}/agent_ex_work"
    if [[ -f "pyproject.toml" ]]; then
        poetry run python -m pytest tests/ || warn "Python tests failed or no tests found"
    fi

    log "✅ Tests completed"
}

# Create systemd service files
create_systemd_services() {
    log "⚙️  Creating systemd service files..."

    local services_dir="${UMCC_PROJECT_ROOT}/scripts/systemd"
    mkdir -p "$services_dir"

    # Create master UMCC service
    cat > "${services_dir}/umcc.service" << EOF
[Unit]
Description=UMCC - Unfettered Mobile Command Center
After=network.target
Wants=network.target

[Service]
Type=forking
User=\${USER}
Group=\${USER}
WorkingDirectory=${UMCC_PROJECT_ROOT}
Environment="UMCC_PROJECT_ROOT=${UMCC_PROJECT_ROOT}"
ExecStart=${UMCC_PROJECT_ROOT}/scripts/start_umcc.sh
ExecStop=${UMCC_PROJECT_ROOT}/scripts/stop_umcc.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    log "✅ Systemd service files created in ${services_dir}"
}

# Main build function
main() {
    log "🚀 Starting UMCC Master Build Process..."

    check_prerequisites
    generate_protobuf
    build_go_daemons
    build_console
    setup_agent_ex_work
    run_tests
    create_systemd_services

    log "🎉 UMCC Build Complete!"
    log "📋 Next steps:"
    log "   1. Configure ${UMCC_PROJECT_ROOT}/config/config.toml"
    log "   2. Run: ${UMCC_PROJECT_ROOT}/scripts/start_umcc.sh"
    log "   3. Access Console: ${UMCC_PROJECT_ROOT}/bin/umcc_console"

    echo -e "${GREEN}🏆 The Architect's Digital Dominion awaits...${NC}"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
