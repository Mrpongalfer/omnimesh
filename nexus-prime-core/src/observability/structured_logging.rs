// Structured Logging Framework for OmniMesh
// Production-grade logging with structured output, levels, and centralized collection

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
    CRITICAL = 4,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogContext {
    pub trace_id: String,
    pub span_id: String,
    pub service: String,
    pub version: String,
    pub environment: String,
    pub node_id: Option<String>,
    pub user_id: Option<String>,
    pub session_id: Option<String>,
    pub correlation_id: Option<String>,
    pub operation: Option<String>,
    pub component: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuredLogEntry {
    pub timestamp: DateTime<Utc>,
    pub level: LogLevel,
    pub message: String,
    pub context: LogContext,
    pub fields: HashMap<String, serde_json::Value>,
    pub error: Option<ErrorDetails>,
    pub performance: Option<PerformanceMetrics>,
    pub security: Option<SecurityContext>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorDetails {
    pub error_type: String,
    pub error_code: Option<String>,
    pub stack_trace: Option<String>,
    pub cause: Option<String>,
    pub resolution_hint: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub duration_ms: u64,
    pub memory_usage_bytes: Option<u64>,
    pub cpu_usage_percent: Option<f64>,
    pub request_size_bytes: Option<u64>,
    pub response_size_bytes: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityContext {
    pub authentication_method: Option<String>,
    pub authorization_level: Option<String>,
    pub source_ip: Option<String>,
    pub user_agent: Option<String>,
    pub threat_level: Option<String>,
    pub audit_event: Option<String>,
}

pub struct StructuredLogger {
    service_name: String,
    version: String,
    environment: String,
    minimum_level: LogLevel,
    outputs: Vec<Box<dyn LogOutput>>,
}

pub trait LogOutput: Send + Sync {
    fn write(&self, entry: &StructuredLogEntry) -> Result<(), Box<dyn std::error::Error>>;
    fn flush(&self) -> Result<(), Box<dyn std::error::Error>>;
}

pub struct JsonFileOutput {
    file_path: String,
}

pub struct JsonStdoutOutput;

pub struct ElasticsearchOutput {
    endpoint: String,
    index_pattern: String,
    api_key: Option<String>,
}

impl StructuredLogger {
    pub fn new(service_name: &str, version: &str, environment: &str) -> Self {
        Self {
            service_name: service_name.to_string(),
            version: version.to_string(),
            environment: environment.to_string(),
            minimum_level: LogLevel::INFO,
            outputs: vec![Box::new(JsonStdoutOutput)],
        }
    }

    pub fn with_minimum_level(mut self, level: LogLevel) -> Self {
        self.minimum_level = level;
        self
    }

    pub fn with_file_output(mut self, file_path: &str) -> Self {
        self.outputs.push(Box::new(JsonFileOutput {
            file_path: file_path.to_string(),
        }));
        self
    }

    pub fn with_elasticsearch_output(mut self, endpoint: &str, index_pattern: &str, api_key: Option<String>) -> Self {
        self.outputs.push(Box::new(ElasticsearchOutput {
            endpoint: endpoint.to_string(),
            index_pattern: index_pattern.to_string(),
            api_key,
        }));
        self
    }

    pub fn log(&self, level: LogLevel, message: &str) -> LogEntryBuilder {
        LogEntryBuilder::new(self, level, message)
    }

    pub fn debug(&self, message: &str) -> LogEntryBuilder {
        self.log(LogLevel::DEBUG, message)
    }

    pub fn info(&self, message: &str) -> LogEntryBuilder {
        self.log(LogLevel::INFO, message)
    }

    pub fn warn(&self, message: &str) -> LogEntryBuilder {
        self.log(LogLevel::WARN, message)
    }

    pub fn error(&self, message: &str) -> LogEntryBuilder {
        self.log(LogLevel::ERROR, message)
    }

    pub fn critical(&self, message: &str) -> LogEntryBuilder {
        self.log(LogLevel::CRITICAL, message)
    }

    fn should_log(&self, level: &LogLevel) -> bool {
        (*level as u8) >= (self.minimum_level as u8)
    }

    fn write_entry(&self, entry: StructuredLogEntry) {
        if !self.should_log(&entry.level) {
            return;
        }

        for output in &self.outputs {
            if let Err(e) = output.write(&entry) {
                eprintln!("Failed to write log entry: {}", e);
            }
        }
    }

    fn create_context(&self, trace_id: Option<String>, span_id: Option<String>) -> LogContext {
        LogContext {
            trace_id: trace_id.unwrap_or_else(|| Uuid::new_v4().to_string()),
            span_id: span_id.unwrap_or_else(|| Uuid::new_v4().to_string()),
            service: self.service_name.clone(),
            version: self.version.clone(),
            environment: self.environment.clone(),
            node_id: None,
            user_id: None,
            session_id: None,
            correlation_id: None,
            operation: None,
            component: None,
        }
    }
}

pub struct LogEntryBuilder<'a> {
    logger: &'a StructuredLogger,
    level: LogLevel,
    message: String,
    context: LogContext,
    fields: HashMap<String, serde_json::Value>,
    error: Option<ErrorDetails>,
    performance: Option<PerformanceMetrics>,
    security: Option<SecurityContext>,
}

impl<'a> LogEntryBuilder<'a> {
    fn new(logger: &'a StructuredLogger, level: LogLevel, message: &str) -> Self {
        Self {
            logger,
            level,
            message: message.to_string(),
            context: logger.create_context(None, None),
            fields: HashMap::new(),
            error: None,
            performance: None,
            security: None,
        }
    }

    pub fn with_trace_id(mut self, trace_id: &str) -> Self {
        self.context.trace_id = trace_id.to_string();
        self
    }

    pub fn with_span_id(mut self, span_id: &str) -> Self {
        self.context.span_id = span_id.to_string();
        self
    }

    pub fn with_user_id(mut self, user_id: &str) -> Self {
        self.context.user_id = Some(user_id.to_string());
        self
    }

    pub fn with_session_id(mut self, session_id: &str) -> Self {
        self.context.session_id = Some(session_id.to_string());
        self
    }

    pub fn with_operation(mut self, operation: &str) -> Self {
        self.context.operation = Some(operation.to_string());
        self
    }

    pub fn with_component(mut self, component: &str) -> Self {
        self.context.component = Some(component.to_string());
        self
    }

    pub fn with_field<T: serde::Serialize>(mut self, key: &str, value: T) -> Self {
        self.fields.insert(key.to_string(), serde_json::to_value(value).unwrap_or(serde_json::Value::Null));
        self
    }

    pub fn with_error(mut self, error_type: &str, error_code: Option<&str>, stack_trace: Option<&str>) -> Self {
        self.error = Some(ErrorDetails {
            error_type: error_type.to_string(),
            error_code: error_code.map(|s| s.to_string()),
            stack_trace: stack_trace.map(|s| s.to_string()),
            cause: None,
            resolution_hint: None,
        });
        self
    }

    pub fn with_performance(mut self, duration_ms: u64) -> Self {
        self.performance = Some(PerformanceMetrics {
            duration_ms,
            memory_usage_bytes: None,
            cpu_usage_percent: None,
            request_size_bytes: None,
            response_size_bytes: None,
        });
        self
    }

    pub fn with_security_event(mut self, event_type: &str, threat_level: Option<&str>) -> Self {
        self.security = Some(SecurityContext {
            authentication_method: None,
            authorization_level: None,
            source_ip: None,
            user_agent: None,
            threat_level: threat_level.map(|s| s.to_string()),
            audit_event: Some(event_type.to_string()),
        });
        self
    }

    pub fn commit(self) {
        let entry = StructuredLogEntry {
            timestamp: Utc::now(),
            level: self.level,
            message: self.message,
            context: self.context,
            fields: self.fields,
            error: self.error,
            performance: self.performance,
            security: self.security,
        };

        self.logger.write_entry(entry);
    }
}

impl LogOutput for JsonStdoutOutput {
    fn write(&self, entry: &StructuredLogEntry) -> Result<(), Box<dyn std::error::Error>> {
        let json = serde_json::to_string(entry)?;
        println!("{}", json);
        Ok(())
    }

    fn flush(&self) -> Result<(), Box<dyn std::error::Error>> {
        use std::io::{self, Write};
        io::stdout().flush()?;
        Ok(())
    }
}

impl LogOutput for JsonFileOutput {
    fn write(&self, entry: &StructuredLogEntry) -> Result<(), Box<dyn std::error::Error>> {
        use std::fs::OpenOptions;
        use std::io::Write;

        let json = serde_json::to_string(entry)?;
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.file_path)?;
        
        writeln!(file, "{}", json)?;
        Ok(())
    }

    fn flush(&self) -> Result<(), Box<dyn std::error::Error>> {
        // File is automatically flushed when dropped
        Ok(())
    }
}

impl LogOutput for ElasticsearchOutput {
    fn write(&self, entry: &StructuredLogEntry) -> Result<(), Box<dyn std::error::Error>> {
        // Implementation would use reqwest or similar to send to Elasticsearch
        // This is a placeholder for the actual implementation
        let _json = serde_json::to_string(entry)?;
        // TODO: Send to Elasticsearch endpoint
        Ok(())
    }

    fn flush(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Elasticsearch client would handle batching and flushing
        Ok(())
    }
}

// Macros for convenience
#[macro_export]
macro_rules! log_debug {
    ($logger:expr, $msg:expr) => {
        $logger.debug($msg).commit()
    };
    ($logger:expr, $msg:expr, $($key:expr => $value:expr),*) => {
        {
            let mut builder = $logger.debug($msg);
            $(
                builder = builder.with_field($key, $value);
            )*
            builder.commit()
        }
    };
}

#[macro_export]
macro_rules! log_info {
    ($logger:expr, $msg:expr) => {
        $logger.info($msg).commit()
    };
    ($logger:expr, $msg:expr, $($key:expr => $value:expr),*) => {
        {
            let mut builder = $logger.info($msg);
            $(
                builder = builder.with_field($key, $value);
            )*
            builder.commit()
        }
    };
}

#[macro_export]
macro_rules! log_error {
    ($logger:expr, $msg:expr, $error_type:expr) => {
        $logger.error($msg).with_error($error_type, None, None).commit()
    };
    ($logger:expr, $msg:expr, $error_type:expr, $($key:expr => $value:expr),*) => {
        {
            let mut builder = $logger.error($msg).with_error($error_type, None, None);
            $(
                builder = builder.with_field($key, $value);
            )*
            builder.commit()
        }
    };
}

// Usage example:
/*
use omnimesh_logging::*;

fn main() {
    let logger = StructuredLogger::new("nexus-prime-core", "2.0.0", "production")
        .with_minimum_level(LogLevel::INFO)
        .with_file_output("/var/log/omnimesh/nexus-prime-core.log")
        .with_elasticsearch_output("https://logs.omnimesh.internal:9200", "omnimesh-logs-*", Some("api_key_here".to_string()));

    // Basic logging
    log_info!(logger, "Service started successfully");

    // Structured logging with fields
    log_info!(logger, "User session created", 
        "user_id" => "user123", 
        "session_duration_minutes" => 60
    );

    // Error logging with context
    logger.error("Database connection failed")
        .with_error("DATABASE_CONNECTION_ERROR", Some("CONN_001"), None)
        .with_field("database_host", "postgres.omnimesh.internal")
        .with_field("retry_count", 3)
        .commit();

    // Performance logging
    logger.info("API request processed")
        .with_operation("workflow_execution")
        .with_performance(234)
        .with_field("workflow_id", "wf_12345")
        .with_field("node_count", 15)
        .commit();

    // Security event logging
    logger.warn("Suspicious authentication attempt")
        .with_security_event("SUSPICIOUS_LOGIN", Some("MEDIUM"))
        .with_field("source_ip", "192.168.1.100")
        .with_field("failed_attempts", 5)
        .commit();
}
*/
