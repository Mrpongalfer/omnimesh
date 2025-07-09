# 🌊 OmniMesh Compute Fabric

[![Rust](https://img.shields.io/badge/Rust-1.75+-CE422B?style=for-the-badge&logo=rust&logoColor=white)](https://rustlang.org/)
[![Go](https://img.shields.io/badge/Go-1.23+-00ADD8?style=for-the-badge&logo=go&logoColor=white)](https://golang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-25.0+-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Security](https://img.shields.io/badge/Security-mTLS%20%2B%20Zero%20Trust-FF6B6B?style=for-the-badge&logo=security&logoColor=white)](#security)
[![Performance](https://img.shields.io/badge/Performance-Rust%20%2B%20Tokio-CE422B?style=for-the-badge&logo=rust&logoColor=white)](#performance)

<div align="center">
  <h2>🚀 Next-Generation Distributed AI Orchestration Platform</h2>
  <p><em>Architect's Absolute Dominion over Heterogeneous Computing Resources</em></p>
  
  <a href="#quick-start">🚀 Quick Start</a> •
  <a href="#architecture">🏗️ Architecture</a> •
  <a href="#features">✨ Features</a> •
  <a href="#documentation">📚 Docs</a> •
  <a href="#contributing">🤝 Contributing</a> •
  <a href="#roadmap">🛣️ Roadmap</a>
</div>

---

## 🏛️ Repository Structure

This monorepo contains the complete OmniMesh Compute Fabric ecosystem:

### 🔧 BACKEND
The BACKEND directory contains the core infrastructure components:
- **Nexus Prime Core** - Rust-based orchestration engine
- **Go Node Proxies** - Go-based edge compute nodes  
- **AI Agents** - Specialized AI agent implementations
- **Data Fabric** - Distributed data processing layer

### 🎨 FRONTEND
The FRONTEND directory contains the UI components:
- **SolidJS UI** - High-performance web interface
- **Flutter UI** - Cross-platform mobile/desktop interface

### ☁️ INFRASTRUCTURE
The infrastructure directory contains production deployment tools:
- **Terraform Configuration** - Complete GCP infrastructure as code
- **Kubernetes Manifests** - GitOps-ready deployment configurations
- **ArgoCD Setup** - Automated continuous deployment

### 🚀 OmniMesh Control Center (Dual-Mode TUI)

The OmniMesh Control Center provides two powerful interfaces for managing the entire OmniMesh lifecycle:

1. **CLI Mode**: Rich terminal interface with menu-driven navigation
2. **TUI Mode**: Full-screen Textual interface with mouse support and advanced widgets

```bash
# Launch the unified launcher (defaults to CLI mode)
python omni_launcher.py

# Launch full TUI mode with mouse support
python omni_launcher.py --tui

# Run setup wizard
python omni_launcher.py --setup

# Show system status
python omni_launcher.py --status

# Direct CLI access (advanced users)
python omni-interactive-tui.py

# Direct TUI access (advanced users)
python omni_textual_tui.py
```

#### Key Features:
- **Dual Architecture**: Choose between CLI menus or full TUI experience
- **AI Integration**: Natural language commands and predictive automation
- **Real-time Monitoring**: Live system metrics and service health
- **Configuration Management**: Visual editors with validation
- **Container Orchestration**: Docker and Kubernetes management
- **Security Management**: Certificate and secret management
- **Self-healing Diagnostics**: Automated issue detection and resolution

## 🚀 Quick Start

### **🎯 One-Command Installation (Recommended)**
```bash
# Universal installer - automatically sets up everything
curl -fsSL https://raw.githubusercontent.com/Mrpongalfer/omnimesh/main/bootstrap.sh | bash

# Or with options
curl -fsSL https://raw.githubusercontent.com/Mrpongalfer/omnimesh/main/bootstrap.sh | bash -s -- --dev --ai
```

### **📥 Manual Installation**
```bash
# Clone the repository
git clone https://github.com/Mrpongalfer/omnimesh.git
cd omnimesh

# Run the universal installer
chmod +x install-omnimesh.sh
./install-omnimesh.sh

# Or install manually
pip install -r requirements.txt

# Launch the Control Center (CLI mode)
python omni_launcher.py

# Or launch the full TUI interface
python omni_launcher.py --tui
```

### Backend Setup

```bash
cd BACKEND
./scripts/setup-dev.sh
```

### Frontend Setup

```bash
cd FRONTEND/ui-solidjs
npm install
npm run dev
```

### Infrastructure Setup

```bash
cd infrastructure
make init
make plan ENV=dev
make apply
```

## 📚 Documentation

See the README files in each component directory for detailed documentation:

- [Backend Documentation](BACKEND/README.md)
- [Frontend Documentation](FRONTEND/ui-solidjs/README.md)
- [Infrastructure Documentation](infrastructure/README.md)
- [Kubernetes Deployment](kubernetes/README.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](BACKEND/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <strong>Built with ❤️ by the OmniMesh Team</strong>
</div>
