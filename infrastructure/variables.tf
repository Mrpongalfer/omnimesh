# Variables for OmniTide Infrastructure

# Project Configuration
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Networking Configuration
variable "subnet_cidr" {
  description = "CIDR block for the GKE subnet"
  type        = string
  default     = "10.0.0.0/16"
}

variable "pods_cidr" {
  description = "CIDR block for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "master_cidr" {
  description = "CIDR block for GKE master"
  type        = string
  default     = "172.16.0.0/28"
}

# GKE Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "use_preemptible" {
  description = "Use preemptible instances for cost savings"
  type        = bool
  default     = true
}

# Default Node Pool Configuration
variable "default_pool_machine_type" {
  description = "Machine type for default node pool"
  type        = string
  default     = "e2-standard-4"
}

variable "default_pool_node_count" {
  description = "Initial number of nodes in default pool"
  type        = number
  default     = 1
}

variable "default_pool_min_nodes" {
  description = "Minimum number of nodes in default pool"
  type        = number
  default     = 1
}

variable "default_pool_max_nodes" {
  description = "Maximum number of nodes in default pool"
  type        = number
  default     = 10
}

# AI Agent Node Pool Configuration
variable "ai_pool_machine_type" {
  description = "Machine type for AI agent node pool"
  type        = string
  default     = "g2-standard-4"
}

variable "ai_pool_gpu_type" {
  description = "GPU type for AI agent nodes"
  type        = string
  default     = "nvidia-l4"
}

variable "ai_pool_gpu_count" {
  description = "Number of GPUs per AI agent node"
  type        = number
  default     = 1
}

variable "ai_pool_node_count" {
  description = "Initial number of nodes in AI agent pool"
  type        = number
  default     = 0
}

variable "ai_pool_min_nodes" {
  description = "Minimum number of nodes in AI agent pool"
  type        = number
  default     = 0
}

variable "ai_pool_max_nodes" {
  description = "Maximum number of nodes in AI agent pool"
  type        = number
  default     = 5
}

# Cloud SQL Configuration
variable "enable_cloud_sql" {
  description = "Enable Cloud SQL PostgreSQL instance"
  type        = bool
  default     = false
}

variable "db_tier" {
  description = "Database instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_availability_type" {
  description = "Database availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "ZONAL"
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 20
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = null
}

# Additional Configuration
variable "enable_istio" {
  description = "Enable Istio service mesh"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable enhanced monitoring"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable enhanced logging"
  type        = bool
  default     = true
}
