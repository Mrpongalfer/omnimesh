# 📖 OMNIMESH User Guide

**Complete guide to using the Trinity Convergence Platform**

## 🎯 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/mrpongalfer/omnimesh.git
cd omnimesh

# One-command setup (installs all dependencies)
make setup

# Verify installation
make health
```

### First Commands
```bash
# Check system status
make health

# Try natural language commands
./interfaces/cli/nexus_cli.py "check system health"
./interfaces/cli/nexus_cli.py "deploy in production mode"
```

## 🗣️ Natural Language Interface

The Trinity system understands natural language commands. Here are examples:

### Health & Status Commands
```bash
"check system health"
"show me the current status"
"health check please"
"is everything operational?"
```

### Deployment Commands
```bash
"deploy in production mode"
"start production deployment"
"go live with the system"
"deploy everything"
```

### Build Commands
```bash
"build the trinity system"
"compile everything"
"build all components"
"make the system"
```

## 🛠️ Available Make Targets

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies and prepare environment |
| `make build` | Build all Trinity components (Rust, Go, Python) |
| `make health` | Run comprehensive system health check |
| `make test` | Execute full test suite |
| `make deploy` | Deploy to production environment |
| `make clean` | Clean all build artifacts |
| `make format` | Format codebase (all languages) |
| `make install` | Install global commands (omnimesh, omni, om) |

## 🖥️ Command Line Interface

### Direct CLI Usage
```bash
# Basic command execution
./interfaces/cli/nexus_cli.py "your command here"

# Interactive mode
./interfaces/cli/nexus_cli.py --interactive

# JSON output for scripting
./interfaces/cli/nexus_cli.py --json "check system health"
```

### Interactive Mode
```bash
$ ./interfaces/cli/nexus_cli.py --interactive
🌟 LoL Nexus CLI v1.0.0 - Trinity Convergence
Enter natural language commands or 'exit' to quit

nexus> check system health
💭 Processing: 'check system health'
🚀 Executing: health_check
🏥 Running Trinity Convergence health check...
✅ Operation completed successfully!
  core_orchestrator: operational
  exwork_agent: operational
  rust_engine: operational
  fabric_proxies: operational
  web_frontend: operational
  global_commands: operational

nexus> deploy in production mode
💭 Processing: 'deploy in production mode'
🚀 Executing: deploy
🚢 Deploying LoL Nexus Compute Fabric...
✅ Operation completed successfully!

nexus> exit
👋 Goodbye from LoL Nexus!
```

## ⚙️ Configuration

### Main Configuration File
Location: `config/nexus_config.toml`

```toml
[trinity]
name = "LoL Nexus Compute Fabric"
version = "3.0.0"
mode = "production"  # or "development"

[core]
orchestrator_port = 8080
health_check_interval = 30
max_concurrent_operations = 100
log_level = "info"

[agents]
exwork_enabled = true
auto_scaling = true
resource_limits = { cpu = "4.0", memory = "8Gi" }

[interfaces]
cli_enabled = true
web_enabled = true
api_enabled = true
tui_enabled = true

[platform]
rust_engine_threads = 8
go_proxy_pool_size = 50
python_workers = 16

[security]
authentication_required = true
encryption_enabled = true
audit_logging = true
```

### Environment Variables
```bash
# Optional environment overrides
export OMNIMESH_CONFIG_PATH="/custom/path/to/config.toml"
export OMNIMESH_LOG_LEVEL="debug"
export OMNIMESH_MODE="development"
```

## 🏗️ Development Mode

### Starting Development Environment
```bash
# Full development setup
make setup
make build
make health

# Start in development mode
export OMNIMESH_MODE="development"
make health
```

### Hot Reloading
```bash
# Python components auto-reload
make dev-python

# Full system with file watching
make dev-watch
```

## 📊 Monitoring & Health Checks

### System Health
```bash
# Quick health check
make health

# Detailed health with JSON output
./interfaces/cli/nexus_cli.py --json "check system health"
```

### Component Status
The health check monitors these components:
- **Core Orchestrator**: Main Trinity coordination system
- **ExWork Agent**: Autonomous execution agent
- **Rust Engine**: High-performance computation engine
- **Fabric Proxies**: gRPC communication layer
- **Web Frontend**: User interface components
- **Global Commands**: System-wide command availability

### Health Check Output
```
✅ Operation completed successfully!
  core_orchestrator: operational
  exwork_agent: operational
  rust_engine: operational
  fabric_proxies: operational
  web_frontend: operational
  global_commands: operational
```

## 🚀 Production Deployment

### Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (optional)
- Terraform (for infrastructure)

### Local Production Test
```bash
# Build production image
make build

# Deploy locally
make deploy

# Verify deployment
make health
```

### Container Deployment
```bash
# Using Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f trinity

# Health check
docker-compose exec trinity make health
```

### Kubernetes Deployment
```bash
# Deploy to K8s
kubectl apply -f kubernetes/

# Check deployment
kubectl get pods -l app=trinity

# Port forward for testing
kubectl port-forward svc/trinity 8080:8080
```

## 🧪 Testing

### Running Tests
```bash
# All tests
make test

# Component-specific tests
make test-rust      # Rust engine tests
make test-go        # Go proxy tests  
make test-python    # Python orchestrator tests
make test-integration # End-to-end tests
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction
- **End-to-End Tests**: Full system workflow testing
- **Performance Tests**: Load and stress testing

## 🔧 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
make clean && make setup
```

#### Health check failures
```bash
# Check individual components
make test-python
make test-rust
make test-go

# Verify configuration
cat config/nexus_config.toml
```

#### Build failures
```bash
# Clean and rebuild
make clean
make build

# Check system requirements
make check-deps
```

### Debug Mode
```bash
# Enable debug logging
export OMNIMESH_LOG_LEVEL="debug"
make health

# Verbose output
./interfaces/cli/nexus_cli.py --verbose "check system health"
```

### Getting Help
```bash
# CLI help
./interfaces/cli/nexus_cli.py --help

# Make targets help
make help

# System information
make info
```

## 📚 Advanced Usage

### Custom Commands
Create custom natural language commands by extending the CLI:

```python
# In interfaces/cli/nexus_cli.py
self.command_patterns.update({
    'custom_action': [
        r'run\s+my\s+custom\s+action',
        r'execute\s+special\s+task'
    ]
})
```

### API Integration
```python
import requests

# Health check via API
response = requests.get('http://localhost:8080/health')
print(response.json())

# Execute command via API
response = requests.post('http://localhost:8080/execute', 
                        json={'command': 'check system health'})
```

### Extending the Platform
- Add new agents in `core/agents/`
- Extend fabric proxies in `core/fabric_proxies/`
- Add interface components in `interfaces/`
- Customize configuration in `config/nexus_config.toml`

## 🎯 Best Practices

### Development
1. Always run `make health` after changes
2. Use `make format` before committing
3. Write tests for new functionality
4. Update documentation for new features

### Production
1. Use configuration files instead of environment variables
2. Enable authentication and encryption
3. Monitor system health regularly
4. Keep backups of configuration files

### Performance
1. Adjust thread counts based on your hardware
2. Monitor resource usage during deployment
3. Use production mode for better performance
4. Scale components based on load

---

*For more detailed information, see our [API Documentation](api-reference.md) and [Developer Guide](developer-guide.md).*
