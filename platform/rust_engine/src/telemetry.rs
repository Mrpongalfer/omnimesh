// nexus-prime-core/src/telemetry.rs - Advanced Telemetry and Monitoring

use crate::config::TelemetryConfig;
use crate::storage::{TelemetryRecord, TelemetryStorage};
use chrono::{DateTime, Utc};
use metrics::{counter, gauge, histogram, Counter, Gauge, Histogram};
use metrics_exporter_prometheus::PrometheusBuilder;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tracing::{info, warn, error, debug};
use uuid::Uuid;

pub type TelemetryResult<T> = Result<T, TelemetryError>;

#[derive(Debug, thiserror::Error)]
pub enum TelemetryError {
    #[error("Metrics error: {0}")]
    Metrics(String),
    #[error("Storage error: {0}")]
    Storage(#[from] crate::storage::StorageError),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

// Comprehensive system metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub timestamp: DateTime<Utc>,
    pub cpu_usage: f32,
    pub memory_usage: f32,
    pub memory_total: u64,
    pub memory_available: u64,
    pub disk_usage: f32,
    pub disk_total: u64,
    pub disk_available: u64,
    pub network_in_bytes: u64,
    pub network_out_bytes: u64,
    pub load_average: [f32; 3], // 1min, 5min, 15min
    pub process_count: u32,
    pub thread_count: u32,
    pub file_descriptor_count: u32,
}

// Fabric-specific metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricMetrics {
    pub timestamp: DateTime<Utc>,
    pub total_nodes: u32,
    pub online_nodes: u32,
    pub total_agents: u32,
    pub running_agents: u32,
    pub pending_tasks: u32,
    pub completed_tasks: u32,
    pub failed_tasks: u32,
    pub average_task_duration_ms: f32,
    pub fabric_throughput_ops_per_sec: f32,
    pub fabric_latency_ms: f32,
}

// Performance metrics for individual operations
#[derive(Debug, Clone)]
pub struct PerformanceMetrics {
    pub operation_counters: HashMap<String, u64>,
    pub operation_histograms: HashMap<String, Vec<Duration>>,
    pub error_counters: HashMap<String, u64>,
}

// Telemetry manager for collecting, processing, and exporting metrics
pub struct TelemetryManager {
    config: TelemetryConfig,
    storage: Arc<dyn TelemetryStorage>,
    system_metrics: Arc<RwLock<SystemMetrics>>,
    fabric_metrics: Arc<RwLock<FabricMetrics>>,
    performance_metrics: Arc<RwLock<PerformanceMetrics>>,
    
    // Prometheus metrics
    node_count_gauge: Gauge,
    agent_count_gauge: Gauge,
    task_duration_histogram: Histogram,
    operation_counter: Counter,
    error_counter: Counter,
}

impl TelemetryManager {
    pub async fn new(
        config: TelemetryConfig,
        storage: Arc<dyn TelemetryStorage>,
    ) -> TelemetryResult<Self> {
        // Initialize Prometheus exporter if enabled
        if config.enable_prometheus {
            PrometheusBuilder::new()
                .with_http_listener(([0, 0, 0, 0], 9090))
                .install()
                .map_err(|e| TelemetryError::Metrics(format!("Failed to initialize Prometheus: {}", e)))?;
        }

        // Initialize OpenTelemetry/Jaeger if enabled
        if config.enable_jaeger {
            if let Some(endpoint) = &config.jaeger_endpoint {
                // Initialize Jaeger tracer (simplified for now)
                info!("Jaeger telemetry would be initialized with endpoint: {}", endpoint);
                // TODO: Implement full Jaeger integration when dependencies are stable
            }
        }

        // Initialize Prometheus metrics
        let node_count_gauge = gauge!("fabric_nodes_total");
        let agent_count_gauge = gauge!("fabric_agents_total");
        let task_duration_histogram = histogram!("fabric_task_duration_seconds");
        let operation_counter = counter!("fabric_operations_total");
        let error_counter = counter!("fabric_errors_total");

        let manager = Self {
            config,
            storage,
            system_metrics: Arc::new(RwLock::new(Self::default_system_metrics())),
            fabric_metrics: Arc::new(RwLock::new(Self::default_fabric_metrics())),
            performance_metrics: Arc::new(RwLock::new(PerformanceMetrics {
                operation_counters: HashMap::new(),
                operation_histograms: HashMap::new(),
                error_counters: HashMap::new(),
            })),
            node_count_gauge,
            agent_count_gauge,
            task_duration_histogram,
            operation_counter,
            error_counter,
        };

        Ok(manager)
    }

    // Start telemetry collection background tasks
    pub fn start_collection_tasks(&self) -> Vec<tokio::task::JoinHandle<()>> {
        let mut tasks = Vec::new();

        // System metrics collection task
        let system_metrics = Arc::clone(&self.system_metrics);
        let storage = Arc::clone(&self.storage);
        tasks.push(tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(30));
            
            loop {
                interval.tick().await;
                
                match Self::collect_system_metrics().await {
                    Ok(metrics) => {
                        // Update in-memory metrics
                        {
                            let mut system_metrics = system_metrics.write().await;
                            *system_metrics = metrics.clone();
                        }

                        // Store to persistent storage
                        let telemetry_record = TelemetryRecord {
                            id: Uuid::new_v4(),
                            entity_id: "system".to_string(),
                            entity_type: "system".to_string(),
                            timestamp: metrics.timestamp,
                            cpu_utilization: metrics.cpu_usage,
                            memory_utilization: metrics.memory_usage,
                            network_in_kbps: metrics.network_in_bytes as f32 / 1024.0,
                            network_out_kbps: metrics.network_out_bytes as f32 / 1024.0,
                            custom_metrics: HashMap::new(), // Could include more detailed metrics
                        };

                        if let Err(e) = storage.store_telemetry(&telemetry_record).await {
                            error!("Failed to store system telemetry: {}", e);
                        }
                    }
                    Err(e) => {
                        error!("Failed to collect system metrics: {}", e);
                    }
                }
            }
        }));

        // Fabric metrics collection task
        let fabric_metrics = Arc::clone(&self.fabric_metrics);
        tasks.push(tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60));
            
            loop {
                interval.tick().await;
                
                // Collect fabric-specific metrics
                // This would integrate with the FabricManager to get current state
                info!("Collecting fabric metrics...");
                
                // Update Prometheus metrics
                // These values would come from the actual fabric state
                // gauge!("fabric_nodes_total").set(online_nodes as f64);
                // gauge!("fabric_agents_total").set(running_agents as f64);
            }
        }));

        // Metrics cleanup task
        let storage_clone = Arc::clone(&self.storage);
        tasks.push(tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(3600 * 24)); // Daily
            
            loop {
                interval.tick().await;
                
                info!("Cleaning up old telemetry data...");
                match storage_clone.cleanup_old_telemetry(30).await { // Keep 30 days
                    Ok(cleaned) => {
                        info!("Cleaned up {} old telemetry records", cleaned);
                    }
                    Err(e) => {
                        error!("Failed to cleanup old telemetry: {}", e);
                    }
                }
            }
        }));

        tasks
    }

    // Record operation metrics
    pub async fn record_operation(&self, operation: &str, duration: Duration, success: bool) {
        // Update Prometheus metrics
        self.operation_counter.increment(1);
        self.task_duration_histogram.record(duration.as_secs_f64());

        if !success {
            self.error_counter.increment(1);
        }

        // Update internal performance metrics
        let mut perf_metrics = self.performance_metrics.write().await;
        
        *perf_metrics.operation_counters.entry(operation.to_string()).or_insert(0) += 1;
        
        perf_metrics.operation_histograms
            .entry(operation.to_string())
            .or_insert_with(Vec::new)
            .push(duration);

        if !success {
            *perf_metrics.error_counters.entry(operation.to_string()).or_insert(0) += 1;
        }

        // Keep histogram size manageable
        if let Some(histogram) = perf_metrics.operation_histograms.get_mut(operation) {
            if histogram.len() > 1000 {
                histogram.drain(0..500); // Keep most recent 500 entries
            }
        }
    }

    // Record custom metric
    pub async fn record_custom_metric(&self, entity_id: &str, metric_name: &str, value: f32) {
        let telemetry_record = TelemetryRecord {
            id: Uuid::new_v4(),
            entity_id: entity_id.to_string(),
            entity_type: "custom".to_string(),
            timestamp: Utc::now(),
            cpu_utilization: 0.0,
            memory_utilization: 0.0,
            network_in_kbps: 0.0,
            network_out_kbps: 0.0,
            custom_metrics: [(metric_name.to_string(), value)].into_iter().collect(),
        };

        if let Err(e) = self.storage.store_telemetry(&telemetry_record).await {
            error!("Failed to store custom metric: {}", e);
        }
    }

    // Get current system metrics
    pub async fn get_system_metrics(&self) -> SystemMetrics {
        self.system_metrics.read().await.clone()
    }

    // Get current fabric metrics
    pub async fn get_fabric_metrics(&self) -> FabricMetrics {
        self.fabric_metrics.read().await.clone()
    }

    // Get performance summary
    pub async fn get_performance_summary(&self) -> HashMap<String, OperationSummary> {
        let perf_metrics = self.performance_metrics.read().await;
        let mut summary = HashMap::new();

        for (operation, count) in &perf_metrics.operation_counters {
            let error_count = perf_metrics.error_counters.get(operation).copied().unwrap_or(0);
            let success_rate = if *count > 0 {
                ((count - error_count) as f32 / *count as f32) * 100.0
            } else {
                0.0
            };

            let avg_duration = if let Some(durations) = perf_metrics.operation_histograms.get(operation) {
                if !durations.is_empty() {
                    let total: Duration = durations.iter().sum();
                    total.as_millis() as f32 / durations.len() as f32
                } else {
                    0.0
                }
            } else {
                0.0
            };

            summary.insert(operation.clone(), OperationSummary {
                total_count: *count,
                error_count,
                success_rate,
                avg_duration_ms: avg_duration,
            });
        }

        summary
    }

    // Collect system metrics (would integrate with system monitoring libraries)
    async fn collect_system_metrics() -> TelemetryResult<SystemMetrics> {
        // This is a simplified implementation
        // In production, you'd use libraries like `sysinfo` or platform-specific APIs
        Ok(SystemMetrics {
            timestamp: Utc::now(),
            cpu_usage: 45.2,
            memory_usage: 62.1,
            memory_total: 16 * 1024 * 1024 * 1024, // 16GB
            memory_available: 6 * 1024 * 1024 * 1024, // 6GB
            disk_usage: 78.5,
            disk_total: 1024 * 1024 * 1024 * 1024, // 1TB
            disk_available: 220 * 1024 * 1024 * 1024, // 220GB
            network_in_bytes: 1024 * 1024 * 50, // 50MB
            network_out_bytes: 1024 * 1024 * 30, // 30MB
            load_average: [1.2, 1.5, 1.8],
            process_count: 245,
            thread_count: 1200,
            file_descriptor_count: 8192,
        })
    }

    fn default_system_metrics() -> SystemMetrics {
        SystemMetrics {
            timestamp: Utc::now(),
            cpu_usage: 0.0,
            memory_usage: 0.0,
            memory_total: 0,
            memory_available: 0,
            disk_usage: 0.0,
            disk_total: 0,
            disk_available: 0,
            network_in_bytes: 0,
            network_out_bytes: 0,
            load_average: [0.0, 0.0, 0.0],
            process_count: 0,
            thread_count: 0,
            file_descriptor_count: 0,
        }
    }

    fn default_fabric_metrics() -> FabricMetrics {
        FabricMetrics {
            timestamp: Utc::now(),
            total_nodes: 0,
            online_nodes: 0,
            total_agents: 0,
            running_agents: 0,
            pending_tasks: 0,
            completed_tasks: 0,
            failed_tasks: 0,
            average_task_duration_ms: 0.0,
            fabric_throughput_ops_per_sec: 0.0,
            fabric_latency_ms: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperationSummary {
    pub total_count: u64,
    pub error_count: u64,
    pub success_rate: f32,
    pub avg_duration_ms: f32,
}

// Telemetry middleware for automatic operation tracking
pub struct TelemetryMiddleware {
    manager: Arc<TelemetryManager>,
}

impl TelemetryMiddleware {
    pub fn new(manager: Arc<TelemetryManager>) -> Self {
        Self { manager }
    }

    pub async fn track_operation<F, T>(&self, operation: &str, future: F) -> T
    where
        F: std::future::Future<Output = T>,
    {
        let start = Instant::now();
        let result = future.await;
        let duration = start.elapsed();

        // Assume success for now - in practice, you'd determine this from the result type
        self.manager.record_operation(operation, duration, true).await;

        result
    }
}

// Health check endpoint data
#[derive(Debug, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub timestamp: DateTime<Utc>,
    pub uptime_seconds: u64,
    pub system_metrics: SystemMetrics,
    pub fabric_metrics: FabricMetrics,
    pub components: HashMap<String, ComponentHealth>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComponentHealth {
    pub status: String,
    pub last_check: DateTime<Utc>,
    pub details: HashMap<String, String>,
}
