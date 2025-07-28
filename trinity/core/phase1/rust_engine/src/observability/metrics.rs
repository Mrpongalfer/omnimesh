// Metrics and Telemetry Framework for OmniMesh
// Production-grade metrics collection with Prometheus integration

use prometheus::{
    Counter, CounterVec, Gauge, GaugeVec, Histogram, HistogramVec, IntCounter, IntCounterVec,
    IntGauge, IntGaugeVec, Registry, Encoder, TextEncoder, Opts, HistogramOpts,
};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct MetricsCollector {
    registry: Registry,
    
    // System metrics
    pub http_requests_total: CounterVec,
    pub http_request_duration: HistogramVec,
    pub http_response_size_bytes: HistogramVec,
    pub active_connections: IntGauge,
    
    // Business metrics
    pub workflow_executions_total: CounterVec,
    pub workflow_execution_duration: HistogramVec,
    pub active_workflows: IntGauge,
    pub node_count: IntGauge,
    pub edge_count: IntGauge,
    
    // Performance metrics
    pub memory_usage_bytes: Gauge,
    pub cpu_usage_percent: Gauge,
    pub disk_io_bytes_total: CounterVec,
    pub network_io_bytes_total: CounterVec,
    
    // Error metrics
    pub errors_total: CounterVec,
    pub panics_total: Counter,
    pub circuit_breaker_state: IntGaugeVec,
    
    // Security metrics
    pub authentication_attempts_total: CounterVec,
    pub authorization_failures_total: CounterVec,
    pub security_events_total: CounterVec,
    
    // Data fabric metrics
    pub data_operations_total: CounterVec,
    pub data_operation_duration: HistogramVec,
    pub queue_depth: IntGaugeVec,
    pub message_size_bytes: HistogramVec,
    
    // Custom metrics registry
    custom_metrics: Arc<Mutex<HashMap<String, Box<dyn prometheus::core::Metric>>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricLabels {
    pub service: String,
    pub version: String,
    pub environment: String,
    pub node_id: Option<String>,
    pub component: Option<String>,
    pub operation: Option<String>,
}

impl MetricsCollector {
    pub fn new(service_name: &str, version: &str, environment: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let registry = Registry::new();
        
        // HTTP metrics
        let http_requests_total = CounterVec::new(
            Opts::new("http_requests_total", "Total number of HTTP requests")
                .namespace("omnimesh")
                .subsystem("http"),
            &["method", "endpoint", "status_code", "service", "version"]
        )?;
        
        let http_request_duration = HistogramVec::new(
            HistogramOpts::new("http_request_duration_seconds", "HTTP request duration in seconds")
                .namespace("omnimesh")
                .subsystem("http")
                .buckets(vec![0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]),
            &["method", "endpoint", "service", "version"]
        )?;
        
        let http_response_size_bytes = HistogramVec::new(
            HistogramOpts::new("http_response_size_bytes", "HTTP response size in bytes")
                .namespace("omnimesh")
                .subsystem("http")
                .buckets(vec![100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0]),
            &["method", "endpoint", "service", "version"]
        )?;
        
        let active_connections = IntGauge::new(
            "omnimesh_http_active_connections",
            "Number of active HTTP connections"
        )?;
        
        // Workflow metrics
        let workflow_executions_total = CounterVec::new(
            Opts::new("workflow_executions_total", "Total number of workflow executions")
                .namespace("omnimesh")
                .subsystem("workflow"),
            &["workflow_type", "status", "service", "version"]
        )?;
        
        let workflow_execution_duration = HistogramVec::new(
            HistogramOpts::new("workflow_execution_duration_seconds", "Workflow execution duration in seconds")
                .namespace("omnimesh")
                .subsystem("workflow")
                .buckets(vec![0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0]),
            &["workflow_type", "service", "version"]
        )?;
        
        let active_workflows = IntGauge::new(
            "omnimesh_workflow_active_total",
            "Number of currently executing workflows"
        )?;
        
        let node_count = IntGauge::new(
            "omnimesh_workflow_nodes_total",
            "Total number of workflow nodes"
        )?;
        
        let edge_count = IntGauge::new(
            "omnimesh_workflow_edges_total",
            "Total number of workflow edges"
        )?;
        
        // Performance metrics
        let memory_usage_bytes = Gauge::new(
            "omnimesh_memory_usage_bytes",
            "Current memory usage in bytes"
        )?;
        
        let cpu_usage_percent = Gauge::new(
            "omnimesh_cpu_usage_percent",
            "Current CPU usage percentage"
        )?;
        
        let disk_io_bytes_total = CounterVec::new(
            Opts::new("disk_io_bytes_total", "Total disk I/O in bytes")
                .namespace("omnimesh")
                .subsystem("system"),
            &["operation", "device"]
        )?;
        
        let network_io_bytes_total = CounterVec::new(
            Opts::new("network_io_bytes_total", "Total network I/O in bytes")
                .namespace("omnimesh")
                .subsystem("system"),
            &["direction", "interface"]
        )?;
        
        // Error metrics
        let errors_total = CounterVec::new(
            Opts::new("errors_total", "Total number of errors")
                .namespace("omnimesh")
                .subsystem("errors"),
            &["error_type", "severity", "component", "service"]
        )?;
        
        let panics_total = Counter::new(
            "omnimesh_panics_total",
            "Total number of panics"
        )?;
        
        let circuit_breaker_state = IntGaugeVec::new(
            Opts::new("circuit_breaker_state", "Circuit breaker state (0=closed, 1=open, 2=half-open)")
                .namespace("omnimesh")
                .subsystem("reliability"),
            &["service", "endpoint"]
        )?;
        
        // Security metrics
        let authentication_attempts_total = CounterVec::new(
            Opts::new("authentication_attempts_total", "Total authentication attempts")
                .namespace("omnimesh")
                .subsystem("security"),
            &["method", "result", "service"]
        )?;
        
        let authorization_failures_total = CounterVec::new(
            Opts::new("authorization_failures_total", "Total authorization failures")
                .namespace("omnimesh")
                .subsystem("security"),
            &["resource", "action", "service"]
        )?;
        
        let security_events_total = CounterVec::new(
            Opts::new("security_events_total", "Total security events")
                .namespace("omnimesh")
                .subsystem("security"),
            &["event_type", "severity", "service"]
        )?;
        
        // Data fabric metrics
        let data_operations_total = CounterVec::new(
            Opts::new("data_operations_total", "Total data operations")
                .namespace("omnimesh")
                .subsystem("data"),
            &["operation", "status", "service"]
        )?;
        
        let data_operation_duration = HistogramVec::new(
            HistogramOpts::new("data_operation_duration_seconds", "Data operation duration in seconds")
                .namespace("omnimesh")
                .subsystem("data")
                .buckets(vec![0.001, 0.01, 0.1, 1.0, 10.0, 60.0]),
            &["operation", "service"]
        )?;
        
        let queue_depth = IntGaugeVec::new(
            Opts::new("queue_depth", "Current queue depth")
                .namespace("omnimesh")
                .subsystem("data"),
            &["queue_name", "service"]
        )?;
        
        let message_size_bytes = HistogramVec::new(
            HistogramOpts::new("message_size_bytes", "Message size in bytes")
                .namespace("omnimesh")
                .subsystem("data")
                .buckets(vec![100.0, 1000.0, 10000.0, 100000.0, 1000000.0]),
            &["message_type", "service"]
        )?;
        
        // Register all metrics
        registry.register(Box::new(http_requests_total.clone()))?;
        registry.register(Box::new(http_request_duration.clone()))?;
        registry.register(Box::new(http_response_size_bytes.clone()))?;
        registry.register(Box::new(active_connections.clone()))?;
        registry.register(Box::new(workflow_executions_total.clone()))?;
        registry.register(Box::new(workflow_execution_duration.clone()))?;
        registry.register(Box::new(active_workflows.clone()))?;
        registry.register(Box::new(node_count.clone()))?;
        registry.register(Box::new(edge_count.clone()))?;
        registry.register(Box::new(memory_usage_bytes.clone()))?;
        registry.register(Box::new(cpu_usage_percent.clone()))?;
        registry.register(Box::new(disk_io_bytes_total.clone()))?;
        registry.register(Box::new(network_io_bytes_total.clone()))?;
        registry.register(Box::new(errors_total.clone()))?;
        registry.register(Box::new(panics_total.clone()))?;
        registry.register(Box::new(circuit_breaker_state.clone()))?;
        registry.register(Box::new(authentication_attempts_total.clone()))?;
        registry.register(Box::new(authorization_failures_total.clone()))?;
        registry.register(Box::new(security_events_total.clone()))?;
        registry.register(Box::new(data_operations_total.clone()))?;
        registry.register(Box::new(data_operation_duration.clone()))?;
        registry.register(Box::new(queue_depth.clone()))?;
        registry.register(Box::new(message_size_bytes.clone()))?;
        
        Ok(Self {
            registry,
            http_requests_total,
            http_request_duration,
            http_response_size_bytes,
            active_connections,
            workflow_executions_total,
            workflow_execution_duration,
            active_workflows,
            node_count,
            edge_count,
            memory_usage_bytes,
            cpu_usage_percent,
            disk_io_bytes_total,
            network_io_bytes_total,
            errors_total,
            panics_total,
            circuit_breaker_state,
            authentication_attempts_total,
            authorization_failures_total,
            security_events_total,
            data_operations_total,
            data_operation_duration,
            queue_depth,
            message_size_bytes,
            custom_metrics: Arc::new(Mutex::new(HashMap::new())),
        })
    }
    
    // HTTP metrics helpers
    pub fn record_http_request(&self, method: &str, endpoint: &str, status_code: u16, service: &str, version: &str, duration: Duration, response_size: u64) {
        self.http_requests_total
            .with_label_values(&[method, endpoint, &status_code.to_string(), service, version])
            .inc();
        
        self.http_request_duration
            .with_label_values(&[method, endpoint, service, version])
            .observe(duration.as_secs_f64());
        
        self.http_response_size_bytes
            .with_label_values(&[method, endpoint, service, version])
            .observe(response_size as f64);
    }
    
    // Workflow metrics helpers
    pub fn record_workflow_execution(&self, workflow_type: &str, status: &str, service: &str, version: &str, duration: Duration) {
        self.workflow_executions_total
            .with_label_values(&[workflow_type, status, service, version])
            .inc();
        
        self.workflow_execution_duration
            .with_label_values(&[workflow_type, service, version])
            .observe(duration.as_secs_f64());
    }
    
    pub fn set_active_workflows(&self, count: i64) {
        self.active_workflows.set(count);
    }
    
    pub fn set_workflow_node_count(&self, count: i64) {
        self.node_count.set(count);
    }
    
    pub fn set_workflow_edge_count(&self, count: i64) {
        self.edge_count.set(count);
    }
    
    // Performance metrics helpers
    pub fn set_memory_usage(&self, bytes: f64) {
        self.memory_usage_bytes.set(bytes);
    }
    
    pub fn set_cpu_usage(&self, percent: f64) {
        self.cpu_usage_percent.set(percent);
    }
    
    // Error metrics helpers
    pub fn record_error(&self, error_type: &str, severity: &str, component: &str, service: &str) {
        self.errors_total
            .with_label_values(&[error_type, severity, component, service])
            .inc();
    }
    
    pub fn record_panic(&self) {
        self.panics_total.inc();
    }
    
    // Security metrics helpers
    pub fn record_authentication_attempt(&self, method: &str, result: &str, service: &str) {
        self.authentication_attempts_total
            .with_label_values(&[method, result, service])
            .inc();
    }
    
    pub fn record_authorization_failure(&self, resource: &str, action: &str, service: &str) {
        self.authorization_failures_total
            .with_label_values(&[resource, action, service])
            .inc();
    }
    
    pub fn record_security_event(&self, event_type: &str, severity: &str, service: &str) {
        self.security_events_total
            .with_label_values(&[event_type, severity, service])
            .inc();
    }
    
    // Data fabric metrics helpers
    pub fn record_data_operation(&self, operation: &str, status: &str, service: &str, duration: Duration) {
        self.data_operations_total
            .with_label_values(&[operation, status, service])
            .inc();
        
        self.data_operation_duration
            .with_label_values(&[operation, service])
            .observe(duration.as_secs_f64());
    }
    
    pub fn set_queue_depth(&self, queue_name: &str, service: &str, depth: i64) {
        self.queue_depth
            .with_label_values(&[queue_name, service])
            .set(depth);
    }
    
    pub fn record_message_size(&self, message_type: &str, service: &str, size_bytes: u64) {
        self.message_size_bytes
            .with_label_values(&[message_type, service])
            .observe(size_bytes as f64);
    }
    
    // Export metrics for Prometheus scraping
    pub fn export(&self) -> Result<String, Box<dyn std::error::Error>> {
        let encoder = TextEncoder::new();
        let metric_families = self.registry.gather();
        let mut buffer = Vec::new();
        encoder.encode(&metric_families, &mut buffer)?;
        Ok(String::from_utf8(buffer)?)
    }
    
    // Get registry for custom metrics
    pub fn registry(&self) -> &Registry {
        &self.registry
    }
}

// Timer helper for measuring durations
pub struct Timer {
    start: Instant,
}

impl Timer {
    pub fn new() -> Self {
        Self {
            start: Instant::now(),
        }
    }
    
    pub fn elapsed(&self) -> Duration {
        self.start.elapsed()
    }
    
    pub fn observe<F>(&self, histogram: &Histogram, f: F) -> F::Output
    where
        F: FnOnce() -> F::Output,
    {
        let _timer = histogram.start_timer();
        f()
    }
}

// Macros for convenience
#[macro_export]
macro_rules! time_operation {
    ($metrics:expr, $histogram:expr, $code:block) => {
        {
            let timer = $histogram.start_timer();
            let result = $code;
            timer.observe_duration();
            result
        }
    };
}

#[macro_export]
macro_rules! record_error_with_context {
    ($metrics:expr, $error_type:expr, $severity:expr, $component:expr, $service:expr) => {
        $metrics.record_error($error_type, $severity, $component, $service);
    };
}

// Usage example:
/*
use omnimesh_metrics::*;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let metrics = MetricsCollector::new("nexus-prime-core", "2.0.0", "production")?;
    
    // Record HTTP request
    let start = std::time::Instant::now();
    // ... handle request ...
    let duration = start.elapsed();
    metrics.record_http_request("GET", "/api/workflows", 200, "nexus-prime-core", "2.0.0", duration, 1024);
    
    // Record workflow execution
    let workflow_start = std::time::Instant::now();
    // ... execute workflow ...
    let workflow_duration = workflow_start.elapsed();
    metrics.record_workflow_execution("data_processing", "success", "nexus-prime-core", "2.0.0", workflow_duration);
    
    // Update system metrics
    metrics.set_memory_usage(1024.0 * 1024.0 * 512.0); // 512MB
    metrics.set_cpu_usage(45.2);
    
    // Record security event
    metrics.record_security_event("SUSPICIOUS_LOGIN", "HIGH", "nexus-prime-core");
    
    // Export metrics for Prometheus
    let metrics_output = metrics.export()?;
    println!("{}", metrics_output);
    
    Ok(())
}
*/
