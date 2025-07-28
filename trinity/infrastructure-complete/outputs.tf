# Outputs for OmniTide Infrastructure

# Network Outputs
output "vpc_name" {
  description = "Name of the VPC"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "Name of the GKE subnet"
  value       = google_compute_subnetwork.gke_subnet.name
}

output "subnet_cidr" {
  description = "CIDR block of the GKE subnet"
  value       = google_compute_subnetwork.gke_subnet.ip_cidr_range
}

# GKE Cluster Outputs
output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "Endpoint of the GKE cluster"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "CA certificate of the GKE cluster"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.primary.location
}

output "cluster_zones" {
  description = "Zones where the GKE cluster nodes are located"
  value       = google_container_cluster.primary.node_locations
}

# Service Account Outputs
output "gke_service_account_email" {
  description = "Email of the GKE service account"
  value       = google_service_account.gke_service_account.email
}

# Artifact Registry Outputs
output "artifact_registry_repository" {
  description = "Name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.omnimesh_repo.name
}

output "artifact_registry_location" {
  description = "Location of the Artifact Registry repository"
  value       = google_artifact_registry_repository.omnimesh_repo.location
}

# Secret Manager Outputs
output "jwt_signing_key_secret_id" {
  description = "Secret ID for JWT signing key"
  value       = google_secret_manager_secret.jwt_signing_key.secret_id
}

output "database_password_secret_id" {
  description = "Secret ID for database password"
  value       = google_secret_manager_secret.database_password.secret_id
}

output "api_keys_secret_id" {
  description = "Secret ID for API keys"
  value       = google_secret_manager_secret.api_keys.secret_id
}

# Cloud SQL Outputs (conditional)
output "database_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = var.enable_cloud_sql ? google_sql_database_instance.postgres[0].name : null
}

output "database_connection_name" {
  description = "Connection name of the Cloud SQL instance"
  value       = var.enable_cloud_sql ? google_sql_database_instance.postgres[0].connection_name : null
}

output "database_private_ip" {
  description = "Private IP of the Cloud SQL instance"
  value       = var.enable_cloud_sql ? google_sql_database_instance.postgres[0].private_ip_address : null
  sensitive   = true
}

# Kubectl Configuration Command
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region=${google_container_cluster.primary.location} --project=${var.project_id}"
}

# ArgoCD Installation Commands
output "argocd_install_commands" {
  description = "Commands to install ArgoCD"
  value = [
    "kubectl create namespace argocd",
    "kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
    "kubectl patch svc argocd-server -n argocd -p '{\"spec\":{\"type\":\"LoadBalancer\"}}'",
    "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
  ]
}

# URLs and Endpoints
output "monitoring_urls" {
  description = "URLs for monitoring services"
  value = {
    grafana    = "http://grafana.${var.environment}.omnitide.local"
    prometheus = "http://prometheus.${var.environment}.omnitide.local"
    argocd     = "http://argocd.${var.environment}.omnitide.local"
  }
}

# Resource Information
output "resource_summary" {
  description = "Summary of created resources"
  value = {
    environment = var.environment
    region      = var.region
    vpc_name    = google_compute_network.vpc.name
    cluster     = google_container_cluster.primary.name
    node_pools = [
      {
        name         = "default-pool"
        machine_type = var.default_pool_machine_type
        min_nodes    = var.default_pool_min_nodes
        max_nodes    = var.default_pool_max_nodes
      },
      {
        name         = "ai-agent-pool"
        machine_type = var.ai_pool_machine_type
        gpu_type     = var.ai_pool_gpu_type
        min_nodes    = var.ai_pool_min_nodes
        max_nodes    = var.ai_pool_max_nodes
      }
    ]
    cloud_sql_enabled = var.enable_cloud_sql
    istio_enabled      = var.enable_istio
  }
}
