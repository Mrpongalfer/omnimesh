# omni-cli

The unified command-line interface for the OmniTide Compute Fabric.

## Overview

`omni-cli` is a comprehensive tool for managing the complete lifecycle of the OmniTide Compute Fabric:

- **Infrastructure Management**: Provision and manage GCP infrastructure using Terraform
- **Build & Release**: Build components and create releases with semantic versioning
- **Deployment**: Deploy applications with advanced strategies (rolling, canary, blue-green)
- **Operations**: Monitor, troubleshoot, and manage running systems

## Installation

### From Source

```bash
git clone https://github.com/Mrpongalfer/omnimesh.git OMNIMESH
cd OMNIMESH/infrastructure/cli
go build -o omni-cli .
sudo mv omni-cli /usr/local/bin/
```

### Configuration

Create a configuration file at `~/.config/omni-cli/omni-cli.yaml`:

```yaml
project_id: "your-gcp-project-id"
region: "us-central1"
environment: "dev"

environments:
  dev:
    project_id: "your-dev-project"
    region: "us-central1"
    cluster_name: "dev-omnimesh-cluster"
    namespace: "omnitide-dev"
    image_registry: "us-central1-docker.pkg.dev/your-project/dev-omnimesh"
  
  staging:
    project_id: "your-staging-project"
    region: "us-central1"
    cluster_name: "staging-omnimesh-cluster"
    namespace: "omnitide-staging"
    image_registry: "us-central1-docker.pkg.dev/your-project/staging-omnimesh"
  
  prod:
    project_id: "your-prod-project"
    region: "us-central1"
    cluster_name: "prod-omnimesh-cluster"
    namespace: "omnitide-prod"
    image_registry: "us-central1-docker.pkg.dev/your-project/prod-omnimesh"
```

## Usage

### Infrastructure Management

```bash
# Provision infrastructure for development
omni-cli infra up --env dev

# Check infrastructure status
omni-cli infra status

# Destroy infrastructure (requires confirmation)
omni-cli infra down --env dev --confirm
```

### Build & Release

```bash
# Build all components
omni-cli build

# Build and push specific component
omni-cli build --component nexus --push

# Create a release
omni-cli release --version v1.2.3 --env production
```

### Deployment

```bash
# Deploy to development environment
omni-cli deploy dev

# Deploy with canary strategy
omni-cli deploy production --strategy canary --canary 10

# Rollback a deployment
omni-cli rollback production

# Promote from staging to production
omni-cli promote --from staging --to production
```

### Operations & Monitoring

```bash
# Check system status
omni-cli status

# Stream logs from all components
omni-cli logs --follow

# Stream logs from specific component
omni-cli logs --component nexus --follow

# View metrics
omni-cli metrics --service nexus

# Open monitoring dashboard
omni-cli dashboard

# Open shell to a pod
omni-cli shell --pod nexus-core-abc123

# SSH to a node
omni-cli shell --node gke-node-1
```

## Environment Variables

The CLI supports the following environment variables:

- `OMNI_PROJECT_ID`: GCP project ID
- `OMNI_REGION`: GCP region
- `OMNI_ENVIRONMENT`: Default environment
- `KUBECONFIG`: Path to kubectl config file

## Global Flags

- `--config, -c`: Path to config file
- `--project, -p`: GCP project ID
- `--region, -r`: GCP region
- `--verbose, -v`: Verbose output
- `--dry-run, -d`: Dry run mode

## Command Reference

### Infrastructure Commands

- `infra up`: Provision infrastructure
- `infra down`: Destroy infrastructure
- `infra status`: Show infrastructure status

### Build Commands

- `build`: Build all components
- `release`: Create and deploy a release

### Deployment Commands

- `deploy`: Deploy to environment
- `rollback`: Rollback deployment
- `promote`: Promote between environments

### Operations Commands

- `status`: Show system status
- `logs`: Stream component logs
- `metrics`: Show system metrics
- `shell`: Open shell to node/pod
- `dashboard`: Open monitoring dashboard

## Advanced Usage

### Deployment Strategies

#### Rolling Deployment (Default)
```bash
omni-cli deploy production --strategy rolling
```

#### Canary Deployment
```bash
omni-cli deploy production --strategy canary --canary 20
```

#### Blue-Green Deployment
```bash
omni-cli deploy production --strategy blue-green
```

### Multi-Environment Workflow

```bash
# Deploy to development
omni-cli deploy dev

# Test and validate
omni-cli status
omni-cli logs --component nexus

# Promote to staging
omni-cli promote --from dev --to staging

# Deploy to production
omni-cli deploy production --strategy canary --canary 10
```

### Emergency Procedures

```bash
# Quick rollback
omni-cli rollback production

# Scale down deployment
kubectl scale deployment/nexus-core --replicas=0 -n omnitide-prod

# Check cluster health
omni-cli status
```

## Development

### Building from Source

```bash
git clone https://github.com/Mrpongalfer/omnimesh.git
cd omnimesh/infrastructure/cli
go mod tidy
go build -o omni-cli .
```

### Running Tests

```bash
go test ./...
```

### Adding New Commands

1. Create command file in `cmd/` directory
2. Implement command logic in `pkg/` packages
3. Add command to `cmd/commands.go`
4. Update main.go to register the command

## Architecture

```
omni-cli/
├── main.go              # CLI entry point
├── cmd/                 # Command implementations
│   ├── infra.go        # Infrastructure commands
│   ├── build.go        # Build commands
│   ├── deploy.go       # Deployment commands
│   ├── ops.go          # Operations commands
│   └── commands.go     # Command exports
├── pkg/                 # Core packages
│   ├── config/         # Configuration management
│   ├── terraform/      # Terraform client
│   ├── kubernetes/     # Kubernetes client
│   ├── build/          # Build system
│   ├── deploy/         # Deployment engine
│   └── ops/            # Operations toolkit
└── README.md           # This file
```

## Dependencies

- Go 1.23+
- kubectl
- terraform
- docker
- gcloud CLI (for GCP authentication)

## License

MIT License - see [LICENSE](../../../LICENSE) file for details.
