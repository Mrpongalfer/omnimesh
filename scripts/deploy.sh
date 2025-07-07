#!/bin/bash

# scripts/deploy.sh - Production Deployment Script for Omnitide Fabric

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/deployment.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root for production deployment
check_permissions() {
    if [[ $EUID -ne 0 && "$1" == "production" ]]; then
        log_error "Production deployment requires root privileges. Run with sudo."
    fi
}

# Create necessary directories
setup_directories() {
    log "Setting up directory structure..."
    
    directories=(
        "/opt/omnitide"
        "/opt/omnitide/nexus-prime-core"
        "/opt/omnitide/go-node-proxies"
        "/opt/omnitide/data"
        "/opt/omnitide/logs"
        "/opt/omnitide/config"
        "/opt/omnitide/certs"
        "/var/log/omnitide"
        "/etc/omnitide"
    )
    
    for dir in "${directories[@]}"; do
        if [[ "$1" == "production" ]]; then
            mkdir -p "$dir"
            chown -R omnitide:omnitide "$dir" 2>/dev/null || true
        else
            mkdir -p "$PROJECT_ROOT/local${dir}"
        fi
    done
    
    log_success "Directory structure created"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        apt-get install -y \
            build-essential \
            pkg-config \
            libssl-dev \
            postgresql-client \
            docker.io \
            docker-compose
    elif command -v yum >/dev/null 2>&1; then
        yum update -y
        yum groupinstall -y "Development Tools"
        yum install -y \
            openssl-devel \
            postgresql \
            docker \
            docker-compose
    else
        log_warning "Unknown package manager. Please install dependencies manually."
    fi
    
    log_success "System dependencies installed"
}

# Create system user for production
create_system_user() {
    if [[ "$1" == "production" ]]; then
        log "Creating omnitide system user..."
        
        if ! id "omnitide" &>/dev/null; then
            useradd -r -s /bin/false -d /opt/omnitide omnitide
            usermod -a -G docker omnitide
            log_success "System user created"
        else
            log "System user already exists"
        fi
    fi
}

# Build Rust components
build_rust() {
    log "Building Nexus Prime Core (Rust)..."
    
    cd "$PROJECT_ROOT/nexus-prime-core"
    
    # Install Rust if not present
    if ! command -v cargo >/dev/null 2>&1; then
        log "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    # Build in release mode
    RUST_LOG=info cargo build --release
    
    if [[ "$1" == "production" ]]; then
        cp target/release/nexus-prime-core /opt/omnitide/nexus-prime-core/
        cp -r src/config /opt/omnitide/nexus-prime-core/
    fi
    
    log_success "Rust components built"
}

# Build Go components
build_go() {
    log "Building Go Node Proxies..."
    
    cd "$PROJECT_ROOT/go-node-proxies"
    
    # Install Go if not present
    if ! command -v go >/dev/null 2>&1; then
        log "Installing Go..."
        wget -O go.tar.gz https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
        tar -C /usr/local -xzf go.tar.gz
        export PATH=$PATH:/usr/local/go/bin
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    fi
    
    # Build
    go build -o gcnp .
    
    if [[ "$1" == "production" ]]; then
        cp gcnp /opt/omnitide/go-node-proxies/
        cp -r internal /opt/omnitide/go-node-proxies/
    fi
    
    log_success "Go components built"
}

# Setup configuration files
setup_config() {
    log "Setting up configuration files..."
    
    config_dir="/etc/omnitide"
    if [[ "$1" != "production" ]]; then
        config_dir="$PROJECT_ROOT/local/etc/omnitide"
        mkdir -p "$config_dir"
    fi
    
    # Create main configuration
    cat > "$config_dir/nexus.toml" << 'EOF'
[server]
grpc_host = "0.0.0.0"
grpc_port = 50053
websocket_host = "0.0.0.0"
websocket_port = 8080
metrics_port = 9090

[database]
postgres_url = "postgresql://omnitide:changeme@localhost:5432/omnitide"
use_timescaledb = true
embedded_db_path = "/opt/omnitide/data/nexus_db"
use_rocksdb = true
max_connections = 10

[security]
enable_mtls = false
auth_token_secret = "CHANGE_THIS_IN_PRODUCTION"
session_timeout_minutes = 60

[telemetry]
enable_prometheus = true
enable_jaeger = false
log_level = "info"
enable_detailed_metrics = true

[consensus]
enable_raft = false
node_id = 1
heartbeat_interval_ms = 1000
election_timeout_ms = 5000

[fabric]
max_nodes = 100
max_agents_per_node = 50
health_check_interval_seconds = 30
agent_timeout_seconds = 300
enable_auto_scaling = true
enable_load_balancing = true
EOF
    
    log_success "Configuration files created"
}

# Setup systemd services
setup_systemd() {
    if [[ "$1" == "production" ]]; then
        log "Setting up systemd services..."
        
        # Nexus Prime Core service
        cat > /etc/systemd/system/nexus-prime-core.service << 'EOF'
[Unit]
Description=Omnitide Nexus Prime Core
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=omnitide
Group=omnitide
WorkingDirectory=/opt/omnitide/nexus-prime-core
ExecStart=/opt/omnitide/nexus-prime-core/nexus-prime-core
Environment=RUST_LOG=info
Environment=NEXUS_CONFIG_PATH=/etc/omnitide/nexus.toml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        # Go Node Proxy service template
        cat > /etc/systemd/system/go-node-proxy@.service << 'EOF'
[Unit]
Description=Omnitide Go Node Proxy %i
After=network.target nexus-prime-core.service
Wants=nexus-prime-core.service

[Service]
Type=simple
User=omnitide
Group=omnitide
WorkingDirectory=/opt/omnitide/go-node-proxies
ExecStart=/opt/omnitide/go-node-proxies/gcnp -node-id=%i
Environment=NEXUS_ENDPOINT=localhost:50053
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable nexus-prime-core
        
        log_success "Systemd services configured"
    fi
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    if [[ "$1" == "production" ]]; then
        # Install PostgreSQL and TimescaleDB
        if command -v apt-get >/dev/null 2>&1; then
            apt-get install -y postgresql postgresql-contrib
            # Add TimescaleDB repository and install
            echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list
            wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -
            apt-get update
            apt-get install -y timescaledb-2-postgresql-14
        fi
        
        # Configure PostgreSQL
        sudo -u postgres createuser omnitide || true
        sudo -u postgres createdb omnitide || true
        sudo -u postgres psql -c "ALTER USER omnitide PASSWORD 'changeme';" || true
        sudo -u postgres psql -d omnitide -c "CREATE EXTENSION IF NOT EXISTS timescaledb;" || true
    fi
    
    log_success "Database setup completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring stack..."
    
    # Create docker-compose for monitoring
    monitoring_dir="/opt/omnitide/monitoring"
    if [[ "$1" != "production" ]]; then
        monitoring_dir="$PROJECT_ROOT/local/opt/omnitide/monitoring"
    fi
    
    mkdir -p "$monitoring_dir"
    
    cat > "$monitoring_dir/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: omnitide-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: omnitide-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
EOF
    
    cat > "$monitoring_dir/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nexus-prime-core'
    static_configs:
      - targets: ['host.docker.internal:9090']
  
  - job_name: 'go-node-proxies'
    static_configs:
      - targets: ['host.docker.internal:8081']
EOF
    
    log_success "Monitoring stack configured"
}

# Main deployment function
main() {
    local deployment_type="${1:-development}"
    
    echo "🚀 Starting Omnitide Fabric Deployment ($deployment_type)"
    echo "================================================="
    
    log "Starting deployment process..."
    log "Deployment type: $deployment_type"
    log "Project root: $PROJECT_ROOT"
    
    check_permissions "$deployment_type"
    setup_directories "$deployment_type"
    
    if [[ "$deployment_type" == "production" ]]; then
        install_dependencies
        create_system_user "$deployment_type"
        setup_database "$deployment_type"
    fi
    
    build_rust "$deployment_type"
    build_go "$deployment_type"
    setup_config "$deployment_type"
    setup_monitoring "$deployment_type"
    
    if [[ "$deployment_type" == "production" ]]; then
        setup_systemd "$deployment_type"
    fi
    
    log_success "Deployment completed successfully!"
    
    echo ""
    echo "🎉 Omnitide Fabric Deployment Complete!"
    echo "========================================"
    
    if [[ "$deployment_type" == "production" ]]; then
        echo "Production services are ready. To start:"
        echo "  sudo systemctl start nexus-prime-core"
        echo "  sudo systemctl start go-node-proxy@node1"
        echo ""
        echo "Monitor with:"
        echo "  sudo journalctl -u nexus-prime-core -f"
        echo "  sudo systemctl status nexus-prime-core"
    else
        echo "Development environment ready. To start:"
        echo "  cd $PROJECT_ROOT && make dev"
        echo ""
        echo "Or manually:"
        echo "  cd nexus-prime-core && cargo run"
        echo "  cd go-node-proxies && go run ."
    fi
    
    echo ""
    echo "Access points:"
    echo "  - Nexus Prime gRPC: localhost:50053"
    echo "  - WebSocket API: localhost:8080"
    echo "  - Prometheus metrics: localhost:9090"
    echo "  - Grafana dashboard: localhost:3000 (admin/admin)"
}

# Run main function with all arguments
main "$@"
