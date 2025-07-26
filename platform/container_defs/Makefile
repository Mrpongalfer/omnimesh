# OmniTide Infrastructure Makefile

.PHONY: help init plan apply destroy validate fmt clean check-gcp

# Default environment
ENV ?= dev
PROJECT_ID ?= $(shell grep "project_id" terraform.tfvars 2>/dev/null | cut -d'"' -f2)

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)OmniTide Infrastructure Management$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make <target> [ENV=dev|staging|prod]"
	@echo ""
	@echo "$(YELLOW)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: check-gcp ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform for $(ENV) environment...$(NC)"
	terraform init
	@echo "$(GREEN)✓ Terraform initialized$(NC)"

plan: init ## Plan infrastructure changes
	@echo "$(YELLOW)Planning infrastructure changes for $(ENV) environment...$(NC)"
	terraform plan -var="environment=$(ENV)" -out="$(ENV).tfplan"
	@echo "$(GREEN)✓ Plan completed. Review the changes above.$(NC)"

apply: ## Apply infrastructure changes
	@echo "$(YELLOW)Applying infrastructure changes for $(ENV) environment...$(NC)"
	@if [ ! -f "$(ENV).tfplan" ]; then \
		echo "$(RED)No plan file found. Run 'make plan' first.$(NC)"; \
		exit 1; \
	fi
	terraform apply "$(ENV).tfplan"
	rm -f "$(ENV).tfplan"
	@echo "$(GREEN)✓ Infrastructure applied successfully$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Configure kubectl: $$(terraform output -raw kubectl_config_command)"
	@echo "2. Install ArgoCD: make install-argocd"
	@echo "3. Deploy applications: make deploy-apps"

destroy: check-confirm ## Destroy infrastructure (DANGEROUS)
	@echo "$(RED)⚠️  Destroying infrastructure for $(ENV) environment...$(NC)"
	terraform destroy -var="environment=$(ENV)"
	@echo "$(RED)✓ Infrastructure destroyed$(NC)"

validate: ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	terraform validate
	terraform fmt -check
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

fmt: ## Format Terraform files
	@echo "$(YELLOW)Formatting Terraform files...$(NC)"
	terraform fmt -recursive
	@echo "$(GREEN)✓ Files formatted$(NC)"

clean: ## Clean temporary files
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	rm -f *.tfplan
	rm -f terraform.tfstate.backup
	@echo "$(GREEN)✓ Temporary files cleaned$(NC)"

show: ## Show current state
	@echo "$(YELLOW)Current Terraform state:$(NC)"
	terraform show

output: ## Show Terraform outputs
	@echo "$(YELLOW)Terraform outputs:$(NC)"
	terraform output

refresh: ## Refresh Terraform state
	@echo "$(YELLOW)Refreshing Terraform state...$(NC)"
	terraform refresh -var="environment=$(ENV)"
	@echo "$(GREEN)✓ State refreshed$(NC)"

# GCP and Prerequisites
check-gcp: ## Check GCP authentication and prerequisites
	@echo "$(YELLOW)Checking GCP authentication...$(NC)"
	@gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null || \
		(echo "$(RED)❌ Not authenticated with GCP. Run: gcloud auth login$(NC)" && exit 1)
	@echo "$(GREEN)✓ GCP authentication verified$(NC)"
	@echo "$(YELLOW)Checking required APIs...$(NC)"
	@./scripts/check-apis.sh 2>/dev/null || echo "$(YELLOW)⚠️  Some APIs may not be enabled$(NC)"

enable-apis: ## Enable required GCP APIs
	@echo "$(YELLOW)Enabling required GCP APIs...$(NC)"
	gcloud services enable container.googleapis.com
	gcloud services enable compute.googleapis.com
	gcloud services enable secretmanager.googleapis.com
	gcloud services enable sql-component.googleapis.com
	gcloud services enable artifactregistry.googleapis.com
	gcloud services enable servicenetworking.googleapis.com
	@echo "$(GREEN)✓ APIs enabled$(NC)"

# Kubernetes Operations
get-credentials: ## Get GKE cluster credentials
	@echo "$(YELLOW)Getting GKE cluster credentials...$(NC)"
	$$(terraform output -raw kubectl_config_command)
	@echo "$(GREEN)✓ Kubectl configured$(NC)"

install-argocd: get-credentials ## Install ArgoCD
	@echo "$(YELLOW)Installing ArgoCD...$(NC)"
	kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
	@echo "$(GREEN)✓ ArgoCD installed$(NC)"
	@echo ""
	@echo "$(YELLOW)To access ArgoCD:$(NC)"
	@echo "1. Expose the service: kubectl patch svc argocd-server -n argocd -p '{\"spec\":{\"type\":\"LoadBalancer\"}}'"
	@echo "2. Get admin password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"

port-forward-argocd: ## Port-forward ArgoCD UI
	@echo "$(YELLOW)Port-forwarding ArgoCD UI to localhost:8080...$(NC)"
	kubectl port-forward svc/argocd-server -n argocd 8080:443

install-nvidia-driver: get-credentials ## Install NVIDIA GPU drivers
	@echo "$(YELLOW)Installing NVIDIA GPU drivers...$(NC)"
	kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
	@echo "$(GREEN)✓ NVIDIA drivers installed$(NC)"

# Monitoring and Operations
status: ## Show infrastructure status
	@echo "$(YELLOW)Infrastructure Status for $(ENV):$(NC)"
	@echo ""
	@echo "$(YELLOW)GKE Cluster:$(NC)"
	@terraform output -json resource_summary | jq -r '"Cluster: " + .cluster + " (" + .region + ")"'
	@echo ""
	@echo "$(YELLOW)Node Pools:$(NC)"
	@terraform output -json resource_summary | jq -r '.node_pools[] | "  - " + .name + ": " + .machine_type + " (" + (.min_nodes|tostring) + "-" + (.max_nodes|tostring) + " nodes)"'
	@echo ""
	@echo "$(YELLOW)Kubernetes Nodes:$(NC)"
	@kubectl get nodes 2>/dev/null || echo "  (kubectl not configured)"

logs: ## Show recent Terraform logs
	@echo "$(YELLOW)Recent Terraform operations:$(NC)"
	@ls -la *.tfplan 2>/dev/null || echo "No recent plans found"

# Development helpers
dev-setup: ## Set up development environment
	@echo "$(YELLOW)Setting up development environment...$(NC)"
	cp terraform.tfvars.example terraform.tfvars
	@echo "$(GREEN)✓ Created terraform.tfvars from example$(NC)"
	@echo "$(YELLOW)Please edit terraform.tfvars with your project details$(NC)"

# Safety checks
check-confirm:
	@echo "$(RED)⚠️  This is a destructive operation!$(NC)"
	@echo "Environment: $(ENV)"
	@echo "Project: $(PROJECT_ID)"
	@read -p "Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || (echo "$(YELLOW)Cancelled.$(NC)" && exit 1)

# Cost estimation (requires infracost)
cost: ## Estimate infrastructure costs
	@echo "$(YELLOW)Estimating infrastructure costs...$(NC)"
	@which infracost > /dev/null || (echo "$(RED)infracost not installed. See: https://www.infracost.io/docs/$(NC)" && exit 1)
	infracost breakdown --path .

# Security scanning (requires tfsec)
security-scan: ## Run security scan on Terraform code
	@echo "$(YELLOW)Running security scan...$(NC)"
	@which tfsec > /dev/null || (echo "$(RED)tfsec not installed. See: https://aquasecurity.github.io/tfsec/$(NC)" && exit 1)
	tfsec .

# Documentation
docs: ## Generate documentation
	@echo "$(YELLOW)Generating Terraform documentation...$(NC)"
	@which terraform-docs > /dev/null || (echo "$(RED)terraform-docs not installed. See: https://terraform-docs.io/$(NC)" && exit 1)
	terraform-docs markdown table . > TERRAFORM_DOCS.md
	@echo "$(GREEN)✓ Documentation generated in TERRAFORM_DOCS.md$(NC)"

# Default target
.DEFAULT_GOAL := help
