# 🌊 OmniTide Compute Fabric

[![Rust](https://img.shields.io/badge/Rust-1.75+-CE422B?style=for-the-badge&logo=rust&logoColor=white)](https://rustlang.org/)
[![Go](https://img.shields.io/badge/Go-1.23+-00ADD8?style=for-the-badge&logo=go&logoColor=white)](https://golang.org/)
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

This monorepo contains the complete OmniTide Compute Fabric ecosystem:

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
- **omni-cli** - Unified command-line interface for all operations
- **Kubernetes Manifests** - GitOps-ready deployment configurations
- **ArgoCD Setup** - Automated continuous deployment

### 🛠️ omni-cli: One Tool for Everything

The `omni-cli` provides a single interface for the entire OmniTide lifecycle:

```bash
# Infrastructure management
omni-cli infra up --env production    # Provision complete GCP infrastructure
omni-cli infra status                 # Check infrastructure health

# Build and deployment
omni-cli build --push                 # Build all components and push images
omni-cli deploy production            # Deploy with zero-downtime
omni-cli rollback production          # Emergency rollback

# Operations and monitoring  
omni-cli status                       # Overall system health
omni-cli logs --component nexus --follow  # Stream live logs
omni-cli dashboard                    # Open monitoring dashboard
```

## 🚀 Quick Start

### Option 1: Production Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/Mrpongalfer/omnimesh.git
cd omnimesh

# Install omni-cli (coming soon)
curl -sSL https://get.omnitide.dev/cli | sh

# Initialize and deploy to GCP
omni-cli infra up --env production
omni-cli deploy production
```

### Option 2: Development Setup

```bash
# Clone the main repository
git clone https://github.com/Mrpongalfer/omnimesh.git
cd omnimesh

# Initialize and update the BACKEND submodule (backend-main branch)
git submodule update --init --recursive
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
  <strong>Built with ❤️ by the OmniTide Team</strong>
</div>
