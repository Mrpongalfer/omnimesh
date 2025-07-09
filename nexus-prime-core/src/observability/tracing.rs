// Distributed Tracing Framework for OmniMesh
// OpenTelemetry-based distributed tracing for request flow visibility

use opentelemetry::{
    global,
    trace::{TraceContextExt, Tracer, TracerProvider, SpanKind, Status, SpanBuilder},
    Context, KeyValue,
};
use opentelemetry_sdk::{
    trace::{self, RandomIdGenerator, Sampler},
    Resource,
};
use opentelemetry_jaeger::JaegerPipeline;
use opentelemetry_otlp::WithExportConfig;
use std::collections::HashMap;
use std::time::{Duration, SystemTime};
use uuid::Uuid;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct TracingConfig {
    pub service_name: String,
    pub service_version: String,
    pub environment: String,
    pub jaeger_endpoint: Option<String>,
    pub otlp_endpoint: Option<String>,
    pub sampling_ratio: f64,
    pub max_events_per_span: u32,
    pub max_attributes_per_span: u32,
    pub max_links_per_span: u32,
}

impl Default for TracingConfig {
    fn default() -> Self {
        Self {
            service_name: "omnimesh-service".to_string(),
            service_version: "2.0.0".to_string(),
            environment: "production".to_string(),
            jaeger_endpoint: None,
            otlp_endpoint: None,
            sampling_ratio: 1.0,
            max_events_per_span: 128,
            max_attributes_per_span: 128,
            max_links_per_span: 128,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpanContext {
    pub trace_id: String,
    pub span_id: String,
    pub parent_span_id: Option<String>,
    pub operation_name: String,
    pub service_name: String,
    pub start_time: SystemTime,
    pub tags: HashMap<String, String>,
    pub logs: Vec<SpanLog>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpanLog {
    pub timestamp: SystemTime,
    pub level: String,
    pub message: String,
    pub fields: HashMap<String, String>,
}

pub struct DistributedTracer {
    tracer: Box<dyn Tracer + Send + Sync>,
    config: TracingConfig,
}

impl DistributedTracer {
    pub fn new(config: TracingConfig) -> Result<Self, Box<dyn std::error::Error>> {
        // Set up resource with service information
        let resource = Resource::new(vec![
            KeyValue::new("service.name", config.service_name.clone()),
            KeyValue::new("service.version", config.service_version.clone()),
            KeyValue::new("service.environment", config.environment.clone()),
            KeyValue::new("service.instance.id", Uuid::new_v4().to_string()),
        ]);

        // Create tracer provider
        let mut tracer_provider_builder = trace::TracerProvider::builder()
            .with_sampler(Sampler::TraceIdRatioBased(config.sampling_ratio))
            .with_id_generator(RandomIdGenerator::default())
            .with_resource(resource);

        // Configure exporters based on config
        if let Some(jaeger_endpoint) = &config.jaeger_endpoint {
            let jaeger_exporter = opentelemetry_jaeger::new_agent_pipeline()
                .with_endpoint(jaeger_endpoint)
                .with_service_name(&config.service_name)
                .build_exporter()?;
            
            tracer_provider_builder = tracer_provider_builder
                .with_batch_exporter(jaeger_exporter, opentelemetry_sdk::runtime::Tokio);
        }

        if let Some(otlp_endpoint) = &config.otlp_endpoint {
            let otlp_exporter = opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint(otlp_endpoint)
                .build_span_exporter()?;
            
            tracer_provider_builder = tracer_provider_builder
                .with_batch_exporter(otlp_exporter, opentelemetry_sdk::runtime::Tokio);
        }

        let tracer_provider = tracer_provider_builder.build();
        global::set_tracer_provider(tracer_provider.clone());

        let tracer = tracer_provider.tracer(&config.service_name);

        Ok(Self {
            tracer: Box::new(tracer),
            config,
        })
    }

    pub fn start_span(&self, operation_name: &str) -> TracedOperation {
        let span = self.tracer
            .span_builder(operation_name)
            .with_kind(SpanKind::Internal)
            .start(&Context::new());

        TracedOperation::new(span, operation_name.to_string(), &self.config)
    }

    pub fn start_http_server_span(&self, method: &str, url: &str) -> TracedOperation {
        let operation_name = format!("{} {}", method, url);
        let span = self.tracer
            .span_builder(&operation_name)
            .with_kind(SpanKind::Server)
            .with_attributes(vec![
                KeyValue::new("http.method", method.to_string()),
                KeyValue::new("http.url", url.to_string()),
                KeyValue::new("component", "http"),
            ])
            .start(&Context::new());

        TracedOperation::new(span, operation_name, &self.config)
    }

    pub fn start_http_client_span(&self, method: &str, url: &str) -> TracedOperation {
        let operation_name = format!("{} {}", method, url);
        let span = self.tracer
            .span_builder(&operation_name)
            .with_kind(SpanKind::Client)
            .with_attributes(vec![
                KeyValue::new("http.method", method.to_string()),
                KeyValue::new("http.url", url.to_string()),
                KeyValue::new("component", "http-client"),
            ])
            .start(&Context::new());

        TracedOperation::new(span, operation_name, &self.config)
    }

    pub fn start_database_span(&self, operation: &str, table: &str) -> TracedOperation {
        let operation_name = format!("db.{}.{}", operation, table);
        let span = self.tracer
            .span_builder(&operation_name)
            .with_kind(SpanKind::Client)
            .with_attributes(vec![
                KeyValue::new("db.type", "postgresql"),
                KeyValue::new("db.operation", operation.to_string()),
                KeyValue::new("db.table", table.to_string()),
                KeyValue::new("component", "database"),
            ])
            .start(&Context::new());

        TracedOperation::new(span, operation_name, &self.config)
    }

    pub fn start_workflow_span(&self, workflow_id: &str, workflow_type: &str) -> TracedOperation {
        let operation_name = format!("workflow.{}", workflow_type);
        let span = self.tracer
            .span_builder(&operation_name)
            .with_kind(SpanKind::Internal)
            .with_attributes(vec![
                KeyValue::new("workflow.id", workflow_id.to_string()),
                KeyValue::new("workflow.type", workflow_type.to_string()),
                KeyValue::new("component", "workflow-engine"),
            ])
            .start(&Context::new());

        TracedOperation::new(span, operation_name, &self.config)
    }

    pub fn start_child_span(&self, parent: &TracedOperation, operation_name: &str) -> TracedOperation {
        let span = self.tracer
            .span_builder(operation_name)
            .with_kind(SpanKind::Internal)
            .with_parent_context(&parent.context())
            .start(&Context::new());

        TracedOperation::new(span, operation_name.to_string(), &self.config)
    }

    pub fn extract_context_from_headers(&self, headers: &HashMap<String, String>) -> Option<Context> {
        // Extract trace context from HTTP headers (simplified)
        if let (Some(trace_id), Some(span_id)) = (
            headers.get("x-trace-id"),
            headers.get("x-span-id"),
        ) {
            // In a real implementation, this would properly deserialize the OpenTelemetry context
            Some(Context::new())
        } else {
            None
        }
    }

    pub fn inject_context_to_headers(&self, context: &Context, headers: &mut HashMap<String, String>) {
        // Inject trace context into HTTP headers (simplified)
        let span = context.span();
        let span_context = span.span_context();
        
        headers.insert("x-trace-id".to_string(), span_context.trace_id().to_string());
        headers.insert("x-span-id".to_string(), span_context.span_id().to_string());
    }
}

pub struct TracedOperation {
    span: Box<dyn opentelemetry::trace::Span + Send + Sync>,
    operation_name: String,
    service_name: String,
    start_time: SystemTime,
    context: Context,
}

impl TracedOperation {
    fn new(span: impl opentelemetry::trace::Span + Send + Sync + 'static, operation_name: String, config: &TracingConfig) -> Self {
        let start_time = SystemTime::now();
        let context = Context::new().with_span(span);
        
        Self {
            span: Box::new(span),
            operation_name,
            service_name: config.service_name.clone(),
            start_time,
            context,
        }
    }

    pub fn context(&self) -> Context {
        self.context.clone()
    }

    pub fn set_attribute(&mut self, key: &str, value: impl Into<opentelemetry::Value>) {
        self.span.set_attribute(KeyValue::new(key, value));
    }

    pub fn set_attributes(&mut self, attributes: Vec<KeyValue>) {
        self.span.set_attributes(attributes);
    }

    pub fn add_event(&mut self, name: &str, attributes: Vec<KeyValue>) {
        self.span.add_event(name, attributes);
    }

    pub fn set_status(&mut self, status: Status) {
        self.span.set_status(status);
    }

    pub fn set_error(&mut self, error: &dyn std::error::Error) {
        self.span.set_status(Status::error(error.to_string()));
        self.span.set_attribute(KeyValue::new("error", true));
        self.span.set_attribute(KeyValue::new("error.message", error.to_string()));
        
        // Add error as an event
        self.span.add_event(
            "error",
            vec![
                KeyValue::new("error.type", error.to_string()),
                KeyValue::new("error.message", error.to_string()),
            ],
        );
    }

    pub fn log(&mut self, level: &str, message: &str, fields: HashMap<String, String>) {
        let mut attributes = vec![
            KeyValue::new("log.level", level.to_string()),
            KeyValue::new("log.message", message.to_string()),
        ];

        for (key, value) in fields {
            attributes.push(KeyValue::new(format!("log.{}", key), value));
        }

        self.span.add_event("log", attributes);
    }

    pub fn finish(mut self) {
        let duration = self.start_time.elapsed().unwrap_or(Duration::from_secs(0));
        self.span.set_attribute(KeyValue::new("duration.ms", duration.as_millis() as i64));
        self.span.end();
    }

    pub fn finish_with_status(mut self, status: Status) {
        let duration = self.start_time.elapsed().unwrap_or(Duration::from_secs(0));
        self.span.set_attribute(KeyValue::new("duration.ms", duration.as_millis() as i64));
        self.span.set_status(status);
        self.span.end();
    }
}

// Middleware for HTTP request tracing
pub struct TracingMiddleware {
    tracer: DistributedTracer,
}

impl TracingMiddleware {
    pub fn new(tracer: DistributedTracer) -> Self {
        Self { tracer }
    }

    pub fn trace_request<F, R>(&self, method: &str, url: &str, headers: &HashMap<String, String>, handler: F) -> R
    where
        F: FnOnce(&mut TracedOperation) -> R,
    {
        let mut span = if let Some(parent_context) = self.tracer.extract_context_from_headers(headers) {
            // Continue existing trace
            let span = self.tracer.tracer
                .span_builder(&format!("{} {}", method, url))
                .with_kind(SpanKind::Server)
                .with_parent_context(&parent_context)
                .start(&Context::new());
            TracedOperation::new(span, format!("{} {}", method, url), &self.tracer.config)
        } else {
            // Start new trace
            self.tracer.start_http_server_span(method, url)
        };

        let result = handler(&mut span);
        span.finish();
        result
    }
}

// Macros for convenience
#[macro_export]
macro_rules! trace_function {
    ($tracer:expr, $func_name:expr, $code:block) => {
        {
            let mut span = $tracer.start_span($func_name);
            let result = $code;
            span.finish();
            result
        }
    };
}

#[macro_export]
macro_rules! trace_async_function {
    ($tracer:expr, $func_name:expr, $code:block) => {
        {
            let mut span = $tracer.start_span($func_name);
            let result = $code.await;
            span.finish();
            result
        }
    };
}

#[macro_export]
macro_rules! trace_with_attributes {
    ($tracer:expr, $func_name:expr, $attrs:expr, $code:block) => {
        {
            let mut span = $tracer.start_span($func_name);
            span.set_attributes($attrs);
            let result = $code;
            span.finish();
            result
        }
    };
}

// Usage example:
/*
use omnimesh_tracing::*;
use opentelemetry::KeyValue;
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = TracingConfig {
        service_name: "nexus-prime-core".to_string(),
        service_version: "2.0.0".to_string(),
        environment: "production".to_string(),
        jaeger_endpoint: Some("http://jaeger:14268/api/traces".to_string()),
        sampling_ratio: 1.0,
        ..Default::default()
    };

    let tracer = DistributedTracer::new(config)?;

    // Trace a workflow execution
    let mut workflow_span = tracer.start_workflow_span("wf_12345", "data_processing");
    workflow_span.set_attribute("workflow.node_count", 10);
    workflow_span.set_attribute("workflow.complexity", "high");

    // Trace a database operation within the workflow
    let mut db_span = tracer.start_child_span(&workflow_span, "database_query");
    db_span.set_attribute("db.query", "SELECT * FROM workflows WHERE id = $1");
    db_span.set_attribute("db.rows_affected", 1);
    
    // Simulate some work
    tokio::time::sleep(std::time::Duration::from_millis(50)).await;
    
    db_span.finish();

    // Trace an HTTP call
    let mut http_span = tracer.start_child_span(&workflow_span, "external_api_call");
    http_span.set_attribute("http.method", "POST");
    http_span.set_attribute("http.url", "https://api.external.com/process");
    
    // Simulate HTTP call
    tokio::time::sleep(std::time::Duration::from_millis(200)).await;
    
    http_span.set_attribute("http.status_code", 200);
    http_span.finish();

    workflow_span.finish();

    // HTTP middleware usage
    let middleware = TracingMiddleware::new(tracer);
    let headers = HashMap::new();
    
    middleware.trace_request("GET", "/api/workflows", &headers, |span| {
        span.set_attribute("user.id", "user123");
        span.set_attribute("request.size", 1024);
        
        // Handle request
        "response data"
    });

    Ok(())
}
*/
