# 🚀 OMNIMESH Installation Guide

## Universal Installer - One Script to Rule Them All

The OMNIMESH Universal Installer is an intelligent, comprehensive setup script that automatically configures the entire OMNIMESH ecosystem from scratch. It handles dependency detection, environment configuration, and component orchestration across multiple platforms.

## 🎯 What the Installer Does

### **Intelligent System Detection**
- Automatically detects OS (Linux, macOS, Windows)
- Identifies architecture (x64, ARM64, ARM)
- Configures appropriate package managers
- Sets up language environments

### **Complete Environment Setup**
- **Python 3.8+** with virtual environment
- **Node.js 18+** with pnpm package manager
- **Rust** with cargo, clippy, and rustfmt
- **Go 1.20+** for microservices
- **Docker** for containerization
- **Kubernetes tools** (kubectl, kind)

### **OMNIMESH Components**
- **Backend**: Rust Nexus Prime Core + Go Node Proxies
- **Frontend**: SolidJS Control Panel with bleeding-edge features
- **Control Center**: Multi-interface Python TUI system
- **Infrastructure**: Terraform + Kubernetes manifests
- **Security**: Tiger Lily enforcement and compliance framework

## 🚀 Quick Start

### **Interactive Installation (Recommended)**
```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/your-repo/omnimesh/main/install-omnimesh.sh | bash

# Or clone and run locally
git clone https://github.com/your-repo/omnimesh.git OMNIMESH
cd OMNIMESH
chmod +x install-omnimesh.sh
./install-omnimesh.sh
```

### **Non-Interactive Installation**
```bash
# Development environment
./install-omnimesh.sh --dev --non-interactive

# Production environment with AI
./install-omnimesh.sh --prod --ai --non-interactive

# Custom installation
./install-omnimesh.sh --no-backend --kubernetes --ai --non-interactive
```

## 📋 Installation Options

### **Installation Types**

| Type | Command | Description | Components |
|------|---------|-------------|------------|
| **Development** | `--dev` | Full development environment | All components + Docker |
| **Production** | `--prod` | Production deployment | All components + K8s + Services |
| **User** | Interactive choice | Control Center + Frontend only | Python TUI + SolidJS UI |
| **Custom** | Various flags | Choose specific components | Configurable |

### **Component Flags**

| Flag | Description | Default |
|------|-------------|---------|
| `--no-backend` | Skip Rust/Go backend installation | Included |
| `--no-frontend` | Skip SolidJS frontend installation | Included |
| `--no-docker` | Skip Docker installation | Included |
| `--kubernetes` | Install Kubernetes tools | Optional |
| `--ai` | Enable AI features | Optional |
| `--openai-key KEY` | Set OpenAI API key | None |
| `--non-interactive` | Run without prompts | Interactive |

## 🔧 System Requirements

### **Minimum Requirements**
- **OS**: Linux (Ubuntu 20.04+), macOS (12+), Windows 10/11
- **RAM**: 4GB (8GB recommended)
- **Storage**: 10GB free space
- **Network**: Internet connection for dependencies

### **Recommended Requirements**
- **OS**: Linux (Ubuntu 22.04+), macOS (13+), Windows 11
- **RAM**: 16GB for full development environment
- **Storage**: 25GB for all components
- **CPU**: 4+ cores for optimal performance

## 📦 What Gets Installed

### **Development Environment**
```
🌊 OMNIMESH Ecosystem
├── 🐍 Python 3.8+ Virtual Environment
│   ├── textual>=0.41.0 (Advanced TUI framework)
│   ├── rich>=13.0.0 (Terminal formatting)
│   ├── pydantic>=2.0.0 (Data validation)
│   ├── docker>=6.0.0 (Container management)
│   ├── openai>=1.0.0 (AI integration)
│   └── 15+ other production dependencies
├── 📦 Node.js 18+ Environment
│   ├── pnpm (Fast package manager)
│   ├── SolidJS 1.9+ (Frontend framework)
│   ├── TypeScript 5.8+ (Type safety)
│   ├── Vite 6.3+ (Build tool)
│   └── Tailwind CSS 4.1+ (Styling)
├── 🦀 Rust Environment
│   ├── cargo (Package manager)
│   ├── clippy (Linter)
│   ├── rustfmt (Formatter)
│   └── Nexus Prime Core dependencies
├── 🐹 Go 1.20+ Environment
│   ├── Standard library
│   ├── gRPC libraries
│   └── Node Proxy dependencies
├── 🐳 Docker Environment
│   ├── Docker Engine
│   ├── Docker Compose
│   └── Container registry access
└── ☸️ Kubernetes Tools (Optional)
    ├── kubectl (Cluster CLI)
    ├── kind (Local clusters)
    └── ArgoCD applications
```

### **Directory Structure Created**
```
omnimesh/
├── BACKEND/                    # Core infrastructure
│   ├── nexus-prime-core/      # Rust orchestration engine
│   ├── go-node-proxies/       # Go microservices
│   └── agents-ai/             # AI agent implementations
├── FRONTEND/                   # User interfaces
│   └── ui-solidjs/            # SolidJS control panel
├── infrastructure/            # Cloud deployment
│   ├── main.tf               # Terraform configuration
│   └── cli/                  # Infrastructure tools
├── kubernetes/                # K8s manifests
│   ├── base/                 # Base configurations
│   └── overlays/             # Environment-specific
├── scripts/                   # Automation scripts
├── venv/                     # Python virtual environment
├── .env                      # Environment variables
├── omni-config.yaml          # System configuration
├── quick-start.sh            # Launch script
├── install-omnimesh.sh       # Universal installer
└── verify-omnimesh.sh        # Installation verification
```

## 🔍 Installation Verification

After installation, run the verification script to ensure everything is properly configured:

```bash
# Run comprehensive health check
./verify-omnimesh.sh

# Check specific components
./verify-omnimesh.sh --backend-only
./verify-omnimesh.sh --frontend-only
```

### **Verification Report**
The verification script checks:
- ✅ **System Environment**: OS, architecture, package managers
- ✅ **Language Runtimes**: Python, Node.js, Rust, Go versions
- ✅ **Dependencies**: All required packages and libraries
- ✅ **OMNIMESH Components**: Scripts, configurations, binaries
- ✅ **Infrastructure Tools**: Docker, Kubernetes, Terraform
- ✅ **Performance**: Startup times and resource usage

## 🚀 Post-Installation Quick Start

### **Launch Control Center**
```bash
# Interactive launcher (CLI mode)
./quick-start.sh

# Full TUI interface
./quick-start.sh tui

# Web interface
./quick-start.sh web

# Ultimate AI-powered system
./quick-start.sh ultimate

# Recursive orchestrator
./quick-start.sh orchestrator
```

### **Development Workflow**
```bash
# Backend development
cd BACKEND/nexus-prime-core
cargo run --release

# Frontend development
cd FRONTEND/ui-solidjs
pnpm run dev

# Full stack development
./quick-start.sh --dev-mode
```

### **Production Deployment**
```bash
# Local production simulation
./quick-start.sh --prod-local

# Cloud deployment
cd infrastructure
terraform init && terraform apply

# Kubernetes deployment
kubectl apply -k kubernetes/overlays/prod
```

## 🛡️ Security Configuration

The installer automatically configures security components:

### **Tiger Lily Enforcement Framework**
- Exponential penalty system (729x multiplier)
- Real-time compliance monitoring
- Automated threat response

### **Zero-Trust Architecture**
- mTLS encryption for all communication
- JWT-based authentication
- Role-based access control (RBAC)

### **Compliance Features**
- GDPR/CCPA privacy protection
- SOC 2 Type II readiness
- WCAG 2.2 AAA accessibility

## 🧠 AI Integration

### **OpenAI Configuration**
```bash
# Set API key during installation
./install-omnimesh.sh --ai --openai-key "your-api-key"

# Or set environment variable
export OPENAI_API_KEY="your-api-key"
./quick-start.sh ultimate
```

### **AI Features Enabled**
- Natural language command processing
- Predictive system optimization
- Anomaly detection and alerting
- Intelligent resource scaling
- Automated code suggestions

## 🔧 Troubleshooting

### **Common Issues**

#### **Permission Errors**
```bash
# Fix script permissions
chmod +x *.sh *.py

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

#### **Python Virtual Environment**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Node.js Issues**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
pnpm install
```

#### **Rust Compilation**
```bash
# Update Rust toolchain
rustup update

# Clean build cache
cargo clean
cargo build --release
```

### **Verification Failures**
```bash
# Run detailed verification
./verify-omnimesh.sh > verification-report.txt

# Check specific issues
cat verification.log | grep "FAIL"

# Re-run installer for failed components
./install-omnimesh.sh --repair
```

## 📞 Support

### **Documentation**
- 📚 [User Guide](USER_GUIDE.md)
- 🏗️ [Architecture Overview](BACKEND/README.md)
- 🎨 [Frontend Guide](FRONTEND/ui-solidjs/README.md)
- 🛡️ [Security Framework](SECURITY_FRAMEWORK.md)

### **Quick Help**
```bash
# Show all available commands
./quick-start.sh --help

# System status
./quick-start.sh status

# Run diagnostics
./quick-start.sh diagnose

# Reset configuration
./quick-start.sh --reset-config
```

### **Community**
- 🐛 Report issues on GitHub
- 💬 Join Discord community
- 📧 Email support team
- 📖 Check documentation wiki

---

## 🎉 Welcome to OMNIMESH!

The Universal Installer provides a seamless path from zero to a fully functional next-generation distributed AI orchestration platform. With intelligent dependency management, comprehensive verification, and extensive configuration options, you'll have OMNIMESH running in minutes, not hours.

**🌊 The future of distributed computing starts here. Welcome to absolute dominion over your infrastructure! 🌊**
