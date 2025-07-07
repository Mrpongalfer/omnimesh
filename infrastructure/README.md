# OmniTide Infrastructure

This directory contains Terraform configurations for deploying OmniTide to Google Cloud Platform.

## 🏗️ Deployment Architecture

OmniTide uses a modern 3-phase deployment strategy with a unified CLI tool for complete infrastructure and application lifecycle management:

### Phase 1: Foundational Infrastructure (Terraform)
- **GKE Cluster** with Workload Identity and Istio service mesh
- **Dedicated VPC** with security-first networking
- **AI-optimized node pools** for GPU workloads
- **Secret Management** via Google Secret Manager
- **Cloud SQL** for persistent metadata (optional)

### Phase 2: Kubernetes Configuration & GitOps (ArgoCD)
- **ArgoCD** for declarative GitOps workflow
- **Automated sync** from Git repository to live cluster
- **Self-healing** deployments with automatic rollback
- **Multi-environment** support (dev/staging/prod)

### Phase 3: Unified CLI Operations (omni-cli)
- **Infrastructure orchestration** with embedded Terraform
- **Intelligent build system** for polyglot monorepo
- **Zero-downtime deployments** with traffic shifting
- **Integrated monitoring** and operational commands

## 🛠️ omni-cli: Unified Operations Tool

The `omni-cli` is a high-performance Go-based CLI that provides a single interface for all OmniTide operations:

### Core Commands

```bash
# Infrastructure Management
omni-cli infra up --env production    # Provision GCP infrastructure
omni-cli infra down --env staging     # Tear down infrastructure
omni-cli infra status                 # Show infrastructure health

# Build & Release Pipeline
omni-cli build                        # Build all components (Rust, Go, Node.js)
omni-cli build --component nexus      # Build specific component
omni-cli release --version v1.2.3     # Create and deploy release

# Deployment Operations
omni-cli deploy production            # Deploy to production with traffic shifting
omni-cli deploy staging --canary      # Canary deployment to staging
omni-cli rollback production          # Rollback last deployment

# Operations & Monitoring
omni-cli status                       # Overall system health
omni-cli logs --component nexus       # Stream component logs
omni-cli metrics --dashboard          # Open Grafana dashboard
omni-cli shell --node ai-worker-1     # SSH into specific node
```

### Architecture Features

- **🚀 Performance**: Written in Go for speed and static binary distribution
- **🔧 Embedded Tools**: Built-in Terraform, Docker, and Kubernetes clients
- **🎯 Intelligent**: Auto-detects changes and builds only what's needed
- **🛡️ Secure**: Direct integration with Google Secret Manager
- **📊 Observable**: Real-time status and health monitoring

## Structure

```
infrastructure/
├── main.tf              # Main GKE cluster and core resources
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── terraform.tfvars    # Variable values (not committed)
├── modules/
│   ├── gke/            # GKE cluster module
│   ├── networking/     # VPC and networking
│   └── security/       # Secret Manager and IAM
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── cli/
    ├── cmd/            # CLI command implementations
    ├── pkg/            # Core packages
    └── main.go         # CLI entry point
```

## Prerequisites

1. Install Terraform >= 1.5
2. Install Google Cloud SDK
3. Authenticate with GCP: `gcloud auth application-default login`
4. Enable required APIs:
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable sql-component.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

## Quick Start

### Option 1: Using omni-cli (Recommended)

```bash
# Install omni-cli
curl -sSL https://get.omnitide.dev/cli | sh

# Initialize project
omni-cli init --project your-gcp-project-id

# Deploy everything
omni-cli deploy production
```

### Option 2: Manual Terraform

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply

# Get cluster credentials
gcloud container clusters get-credentials omnimesh-cluster --region=us-central1
```

## Configuration

Copy `terraform.tfvars.example` to `terraform.tfvars` and update with your values:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
environment = "production"

# GKE Configuration
cluster_name = "omnimesh-cluster"
node_zones = ["us-central1-a", "us-central1-b", "us-central1-c"]

# AI Node Pool (GPU-enabled)
ai_node_pool = {
  machine_type = "g2-standard-4"
  gpu_type     = "nvidia-l4"
  gpu_count    = 1
  min_nodes    = 0
  max_nodes    = 10
}

# Networking
vpc_name = "omnimesh-vpc"
subnet_cidr = "10.0.0.0/16"
```

## Advanced Deployment Patterns

### Canary Deployments

```bash
# Deploy 10% traffic to new version
omni-cli deploy production --canary 10

# Gradually increase traffic
omni-cli traffic shift --to-canary 50

# Complete rollout or rollback
omni-cli traffic shift --to-canary 100  # Complete
omni-cli rollback production            # Rollback
```

### Blue-Green Deployments

```bash
# Deploy to green environment
omni-cli deploy production --strategy blue-green

# Switch traffic after validation
omni-cli traffic switch --to green
```

### Multi-Environment Management

```bash
# Promote from staging to production
omni-cli promote --from staging --to production

# Sync configuration across environments
omni-cli config sync --from production --to staging
```

## Monitoring & Observability

### Built-in Dashboards

```bash
# Open monitoring dashboard
omni-cli dashboard

# View application metrics
omni-cli metrics --service nexus-prime

# Real-time log streaming
omni-cli logs --follow --service all
```

### Health Checks

```bash
# Run comprehensive health check
omni-cli health check

# Test service connectivity
omni-cli test connectivity

# Validate deployment integrity
omni-cli validate deployment
```

## Security & Compliance

### Secret Management

```bash
# Rotate secrets
omni-cli secrets rotate --all

# Audit secret access
omni-cli secrets audit

# Sync secrets across environments
omni-cli secrets sync --from production --to staging
```

### Security Scanning

```bash
# Scan container images
omni-cli security scan images

# Check for vulnerabilities
omni-cli security audit

# Generate compliance report
omni-cli compliance report --format pdf
```

## Troubleshooting

### Common Issues

```bash
# Debug deployment issues
omni-cli debug deployment --verbose

# Check resource quotas
omni-cli check quotas

# Validate configuration
omni-cli validate config

# Reset to known good state
omni-cli reset --to-last-known-good
```

### Emergency Procedures

```bash
# Emergency scaling
omni-cli scale --replicas 10 --service nexus-prime

# Circuit breaker activation
omni-cli circuit-breaker enable --service ai-agents

# Emergency rollback
omni-cli emergency rollback --to v1.2.1
```

## Contributing

See the main [Contributing Guide](../BACKEND/CONTRIBUTING.md) for development guidelines.

For infrastructure-specific contributions:

1. All Terraform changes must be planned and reviewed
2. Test changes in development environment first
3. Update documentation for any new CLI commands
4. Follow security best practices for GCP resources

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
