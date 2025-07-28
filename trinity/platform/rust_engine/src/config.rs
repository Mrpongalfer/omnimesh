// nexus-prime-core/src/config.rs - Configuration Management for Nexus Prime

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NexusConfig {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub security: SecurityConfig,
    pub telemetry: TelemetryConfig,
    pub consensus: ConsensusConfig,
    pub fabric: FabricConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub grpc_host: String,
    pub grpc_port: u16,
    pub websocket_host: String,
    pub websocket_port: u16,
    pub metrics_port: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub postgres_url: Option<String>,
    pub use_timescaledb: bool,
    pub embedded_db_path: PathBuf,
    pub use_rocksdb: bool,
    pub max_connections: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    pub enable_mtls: bool,
    pub ca_cert_path: Option<PathBuf>,
    pub server_cert_path: Option<PathBuf>,
    pub server_key_path: Option<PathBuf>,
    pub client_cert_path: Option<PathBuf>,
    pub client_key_path: Option<PathBuf>,
    pub auth_token_secret: String,
    pub session_timeout_minutes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryConfig {
    pub enable_prometheus: bool,
    pub enable_jaeger: bool,
    pub jaeger_endpoint: Option<String>,
    pub log_level: String,
    pub enable_detailed_metrics: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusConfig {
    pub enable_raft: bool,
    pub node_id: u64,
    pub cluster_peers: Vec<String>,
    pub data_dir: PathBuf,
    pub heartbeat_interval_ms: u64,
    pub election_timeout_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricConfig {
    pub max_nodes: u32,
    pub max_agents_per_node: u32,
    pub health_check_interval_seconds: u64,
    pub agent_timeout_seconds: u64,
    pub enable_auto_scaling: bool,
    pub enable_load_balancing: bool,
}

impl Default for NexusConfig {
    fn default() -> Self {
        Self {
            server: ServerConfig {
                grpc_host: "0.0.0.0".to_string(),
                grpc_port: 50053,
                websocket_host: "0.0.0.0".to_string(),
                websocket_port: 8080,
                metrics_port: 9090,
            },
            database: DatabaseConfig {
                postgres_url: None,
                use_timescaledb: false,
                embedded_db_path: PathBuf::from("./data/nexus_db"),
                use_rocksdb: true,
                max_connections: 10,
            },
            security: SecurityConfig {
                enable_mtls: false,
                ca_cert_path: None,
                server_cert_path: None,
                server_key_path: None,
                client_cert_path: None,
                client_key_path: None,
                auth_token_secret: "CHANGEME_IN_PRODUCTION".to_string(),
                session_timeout_minutes: 60,
            },
            telemetry: TelemetryConfig {
                enable_prometheus: true,
                enable_jaeger: false,
                jaeger_endpoint: None,
                log_level: "info".to_string(),
                enable_detailed_metrics: true,
            },
            consensus: ConsensusConfig {
                enable_raft: false,
                node_id: 1,
                cluster_peers: vec![],
                data_dir: PathBuf::from("./data/raft"),
                heartbeat_interval_ms: 1000,
                election_timeout_ms: 5000,
            },
            fabric: FabricConfig {
                max_nodes: 100,
                max_agents_per_node: 50,
                health_check_interval_seconds: 30,
                agent_timeout_seconds: 300,
                enable_auto_scaling: true,
                enable_load_balancing: true,
            },
        }
    }
}

impl NexusConfig {
    pub fn load_from_file(path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let config = config::Config::builder()
            .add_source(config::File::with_name(path))
            .add_source(config::Environment::with_prefix("NEXUS"))
            .build()?;
        
        Ok(config.try_deserialize()?)
    }

    pub fn save_to_file(&self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        let toml = toml::to_string_pretty(self)?;
        std::fs::write(path, toml)?;
        Ok(())
    }
}
