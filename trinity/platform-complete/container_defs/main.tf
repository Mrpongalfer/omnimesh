# OmniTide Infrastructure - Main Configuration
# This file defines the core GCP infrastructure for OmniTide Compute Fabric

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  
  backend "gcs" {
    # Configure this in terraform.tfvars
    # bucket = "your-terraform-state-bucket"
    # prefix = "terraform/state"
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Data sources
data "google_client_config" "default" {}

data "google_container_engine_versions" "gke_version" {
  location       = var.region
  version_prefix = "1.28."
}

# Local values for resource naming
locals {
  cluster_name = "${var.environment}-omnimesh-cluster"
  vpc_name     = "${var.environment}-omnimesh-vpc"
  
  common_labels = {
    project     = "omnimesh"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = local.vpc_name
  auto_create_subnetworks = false
  mtu                     = 1460
  
  project = var.project_id
}

# Subnet for GKE cluster
resource "google_compute_subnetwork" "gke_subnet" {
  name          = "${local.vpc_name}-gke-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  
  # Secondary IP ranges for pods and services
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = var.pods_cidr
  }
  
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = var.services_cidr
  }
  
  project = var.project_id
}

# Cloud Router for NAT
resource "google_compute_router" "router" {
  name    = "${local.vpc_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  
  project = var.project_id
}

# NAT Gateway for private nodes
resource "google_compute_router_nat" "nat" {
  name                               = "${local.vpc_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
  
  project = var.project_id
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.vpc_name}-allow-internal"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "icmp"
  }
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  
  project = var.project_id
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = local.cluster_name
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.gke_subnet.name
  
  # IP allocation for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
  
  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Enable Istio addon
  addons_config {
    istio_config {
      disabled = false
      auth     = "AUTH_MUTUAL_TLS"
    }
    
    network_policy_config {
      disabled = false
    }
    
    http_load_balancing {
      disabled = false
    }
    
    dns_cache_config {
      enabled = true
    }
  }
  
  # Enable network policy
  network_policy {
    enabled = true
  }
  
  # Master Auth
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
  
  # Private cluster config
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
  }
  
  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }
  
  # Monitoring and logging
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }
  
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }
  
  # Maintenance policy
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T02:00:00Z"
      end_time   = "2023-01-01T06:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA"
    }
  }
  
  project = var.project_id
  
  depends_on = [
    google_compute_subnetwork.gke_subnet,
  ]
}

# Default node pool
resource "google_container_node_pool" "default_pool" {
  name       = "default-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.default_pool_node_count
  
  node_config {
    preemptible  = var.use_preemptible
    machine_type = var.default_pool_machine_type
    disk_size_gb = 50
    disk_type    = "pd-ssd"
    
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = local.common_labels
    
    tags = ["gke-node", "${local.cluster_name}-node"]
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
  
  autoscaling {
    min_node_count = var.default_pool_min_nodes
    max_node_count = var.default_pool_max_nodes
  }
  
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  project = var.project_id
}

# AI Agent node pool with GPU support
resource "google_container_node_pool" "ai_agent_pool" {
  name       = "ai-agent-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.ai_pool_node_count
  
  node_config {
    preemptible  = false # GPUs don't work well with preemptible instances
    machine_type = var.ai_pool_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    
    # GPU configuration
    guest_accelerator {
      type  = var.ai_pool_gpu_type
      count = var.ai_pool_gpu_count
    }
    
    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    labels = merge(local.common_labels, {
      "node-type" = "ai-agent"
      "gpu-type"  = var.ai_pool_gpu_type
    })
    
    tags = ["gke-node", "${local.cluster_name}-ai-node"]
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    taint {
      key    = "nvidia.com/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
  
  autoscaling {
    min_node_count = var.ai_pool_min_nodes
    max_node_count = var.ai_pool_max_nodes
  }
  
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  project = var.project_id
}

# Service Account for GKE nodes
resource "google_service_account" "gke_service_account" {
  account_id   = "${var.environment}-gke-sa"
  display_name = "GKE Service Account for ${var.environment}"
  project      = var.project_id
}

# IAM bindings for GKE service account
resource "google_project_iam_member" "gke_service_account_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "omnimesh_repo" {
  location      = var.region
  repository_id = "${var.environment}-omnimesh"
  description   = "OmniTide container images for ${var.environment}"
  format        = "DOCKER"
  
  project = var.project_id
}

# Secret Manager secrets
resource "google_secret_manager_secret" "jwt_signing_key" {
  secret_id = "${var.environment}-jwt-signing-key"
  
  replication {
    automatic = true
  }
  
  project = var.project_id
}

resource "google_secret_manager_secret" "database_password" {
  secret_id = "${var.environment}-database-password"
  
  replication {
    automatic = true
  }
  
  project = var.project_id
}

resource "google_secret_manager_secret" "api_keys" {
  secret_id = "${var.environment}-api-keys"
  
  replication {
    automatic = true
  }
  
  project = var.project_id
}

# Cloud SQL instance (optional)
resource "google_sql_database_instance" "postgres" {
  count            = var.enable_cloud_sql ? 1 : 0
  name             = "${var.environment}-omnimesh-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier              = var.db_tier
    availability_type = var.db_availability_type
    disk_size         = var.db_disk_size
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    
    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }
  }
  
  deletion_protection = var.environment == "prod"
  
  project = var.project_id
  
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private VPC connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  count         = var.enable_cloud_sql ? 1 : 0
  name          = "${var.environment}-private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  
  project = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  count                   = var.enable_cloud_sql ? 1 : 0
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address[0].name]
}

# Cloud SQL database
resource "google_sql_database" "omnimesh_db" {
  count    = var.enable_cloud_sql ? 1 : 0
  name     = "omnimesh"
  instance = google_sql_database_instance.postgres[0].name
  
  project = var.project_id
}

# Cloud SQL user
resource "google_sql_user" "omnimesh_user" {
  count    = var.enable_cloud_sql ? 1 : 0
  name     = "omnimesh"
  instance = google_sql_database_instance.postgres[0].name
  password = var.db_password
  
  project = var.project_id
}
