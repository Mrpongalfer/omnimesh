// nexus-prime-core/src/storage.rs - Advanced Storage Abstraction Layer

use crate::config::{DatabaseConfig, NexusConfig};
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use rocksdb::{DB, Options as RocksOptions};
use serde::{Deserialize, Serialize};
use sqlx::{Pool, Postgres, PgPool, Row};
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

pub type StorageResult<T> = Result<T, StorageError>;

#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("RocksDB error: {0}")]
    RocksDB(#[from] rocksdb::Error),
    #[error("Serialization error: {0}")]
    Serialization(#[from] bincode::Error),
    #[error("Not found: {0}")]
    NotFound(String),
    #[error("Configuration error: {0}")]
    Config(String),
}

// Core storage traits for different data types
#[async_trait]
pub trait NodeStorage: Send + Sync {
    async fn store_node(&self, node: &FabricNode) -> StorageResult<()>;
    async fn get_node(&self, node_id: &str) -> StorageResult<Option<FabricNode>>;
    async fn list_nodes(&self) -> StorageResult<Vec<FabricNode>>;
    async fn update_node_status(&self, node_id: &str, status: NodeStatus) -> StorageResult<()>;
    async fn delete_node(&self, node_id: &str) -> StorageResult<()>;
}

#[async_trait]
pub trait AgentStorage: Send + Sync {
    async fn store_agent(&self, agent: &AIAgent) -> StorageResult<()>;
    async fn get_agent(&self, agent_id: &str) -> StorageResult<Option<AIAgent>>;
    async fn list_agents(&self) -> StorageResult<Vec<AIAgent>>;
    async fn list_agents_by_node(&self, node_id: &str) -> StorageResult<Vec<AIAgent>>;
    async fn update_agent_status(&self, agent_id: &str, status: AgentStatus) -> StorageResult<()>;
    async fn delete_agent(&self, agent_id: &str) -> StorageResult<()>;
}

#[async_trait]
pub trait TelemetryStorage: Send + Sync {
    async fn store_telemetry(&self, telemetry: &TelemetryRecord) -> StorageResult<()>;
    async fn get_latest_telemetry(&self, entity_id: &str) -> StorageResult<Option<TelemetryRecord>>;
    async fn get_telemetry_history(&self, entity_id: &str, hours: u32) -> StorageResult<Vec<TelemetryRecord>>;
    async fn cleanup_old_telemetry(&self, days: u32) -> StorageResult<u64>;
}

// Data structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FabricNode {
    pub node_id: String,
    pub ip_address: String,
    pub proxy_listen_address: String,
    pub capabilities: String,
    pub agent_type: String,
    pub status: NodeStatus,
    pub last_seen: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum NodeStatus {
    Online,
    Offline,
    Maintenance,
    Error(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIAgent {
    pub agent_id: String,
    pub node_id: String,
    pub name: String,
    pub agent_type: String,
    pub status: AgentStatus,
    pub created_at: DateTime<Utc>,
    pub last_active: DateTime<Utc>,
    pub config: HashMap<String, String>,
    pub resources: AgentResources,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentStatus {
    Starting,
    Running,
    Stopping,
    Stopped,
    Error(String),
    Migrating,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentResources {
    pub cpu_cores: f32,
    pub memory_mb: u64,
    pub gpu_units: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryRecord {
    pub id: Uuid,
    pub entity_id: String,
    pub entity_type: String, // "node" or "agent"
    pub timestamp: DateTime<Utc>,
    pub cpu_utilization: f32,
    pub memory_utilization: f32,
    pub network_in_kbps: f32,
    pub network_out_kbps: f32,
    pub custom_metrics: HashMap<String, f32>,
}

// Hybrid storage implementation that can use both RocksDB and PostgreSQL
pub struct HybridStorage {
    config: DatabaseConfig,
    rocksdb: Option<Arc<DB>>,
    postgres: Option<PgPool>,
}

impl HybridStorage {
    pub async fn new(config: DatabaseConfig) -> StorageResult<Self> {
        let rocksdb = if config.use_rocksdb {
            let mut opts = RocksOptions::default();
            opts.create_if_missing(true);
            opts.set_max_open_files(1000);
            opts.set_use_fsync(false);
            opts.set_bytes_per_sync(8388608);
            opts.optimize_for_point_lookup(1024);
            
            let db = DB::open(&opts, &config.embedded_db_path)?;
            Some(Arc::new(db))
        } else {
            None
        };

        let postgres = if let Some(url) = &config.postgres_url {
            let pool = PgPool::connect(url).await?;
            
            // Initialize TimescaleDB if enabled
            if config.use_timescaledb {
                Self::init_timescaledb(&pool).await?;
            }
            
            Some(pool)
        } else {
            None
        };

        Ok(Self {
            config,
            rocksdb,
            postgres,
        })
    }

    async fn init_timescaledb(pool: &PgPool) -> StorageResult<()> {
        // Create TimescaleDB extension and hypertables for telemetry
        sqlx::query("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            .execute(pool)
            .await?;

        // Create telemetry table as hypertable for efficient time-series storage
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS telemetry (
                id UUID PRIMARY KEY,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                cpu_utilization REAL,
                memory_utilization REAL,
                network_in_kbps REAL,
                network_out_kbps REAL,
                custom_metrics JSONB
            );
        "#)
        .execute(pool)
        .await?;

        sqlx::query("SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);")
            .execute(pool)
            .await?;

        Ok(())
    }

    // Helper methods for key generation
    fn node_key(node_id: &str) -> String {
        format!("node:{}", node_id)
    }

    fn agent_key(agent_id: &str) -> String {
        format!("agent:{}", agent_id)
    }

    fn telemetry_key(entity_id: &str, timestamp: DateTime<Utc>) -> String {
        format!("telemetry:{}:{}", entity_id, timestamp.timestamp())
    }
}

#[async_trait]
impl NodeStorage for HybridStorage {
    async fn store_node(&self, node: &FabricNode) -> StorageResult<()> {
        // Store in RocksDB for fast access
        if let Some(rocks) = &self.rocksdb {
            let key = Self::node_key(&node.node_id);
            let value = bincode::serialize(node)?;
            rocks.put(key.as_bytes(), value)?;
        }

        // Store in PostgreSQL for complex queries
        if let Some(pg) = &self.postgres {
            sqlx::query(r#"
                INSERT INTO nodes (node_id, ip_address, proxy_listen_address, capabilities, 
                                 agent_type, status, last_seen, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (node_id) DO UPDATE SET
                    ip_address = EXCLUDED.ip_address,
                    proxy_listen_address = EXCLUDED.proxy_listen_address,
                    capabilities = EXCLUDED.capabilities,
                    status = EXCLUDED.status,
                    last_seen = EXCLUDED.last_seen,
                    metadata = EXCLUDED.metadata
            "#)
            .bind(&node.node_id)
            .bind(&node.ip_address)
            .bind(&node.proxy_listen_address)
            .bind(&node.capabilities)
            .bind(&node.agent_type)
            .bind(serde_json::to_string(&node.status).unwrap_or_default())
            .bind(node.last_seen)
            .bind(node.created_at)
            .bind(serde_json::to_value(&node.metadata).unwrap_or_default())
            .execute(pg)
            .await?;
        }

        Ok(())
    }

    async fn get_node(&self, node_id: &str) -> StorageResult<Option<FabricNode>> {
        // Try RocksDB first for fast access
        if let Some(rocks) = &self.rocksdb {
            let key = Self::node_key(node_id);
            if let Ok(Some(value)) = rocks.get(key.as_bytes()) {
                if let Ok(node) = bincode::deserialize(&value) {
                    return Ok(Some(node));
                }
            }
        }

        // Fallback to PostgreSQL
        if let Some(pg) = &self.postgres {
            let row = sqlx::query("SELECT * FROM nodes WHERE node_id = $1")
                .bind(node_id)
                .fetch_optional(pg)
                .await?;

            if let Some(row) = row {
                // Convert row to FabricNode (implementation depends on exact schema)
                // This is a simplified version
                return Ok(Some(FabricNode {
                    node_id: row.get("node_id"),
                    ip_address: row.get("ip_address"),
                    proxy_listen_address: row.get("proxy_listen_address"),
                    capabilities: row.get("capabilities"),
                    agent_type: row.get("agent_type"),
                    status: serde_json::from_str(&row.get::<String, _>("status")).unwrap_or(NodeStatus::Offline),
                    last_seen: row.get("last_seen"),
                    created_at: row.get("created_at"),
                    metadata: serde_json::from_value(row.get("metadata")).unwrap_or_default(),
                }));
            }
        }

        Ok(None)
    }

    async fn list_nodes(&self) -> StorageResult<Vec<FabricNode>> {
        // Use PostgreSQL for complex queries if available
        if let Some(pg) = &self.postgres {
            let rows = sqlx::query("SELECT * FROM nodes ORDER BY created_at")
                .fetch_all(pg)
                .await?;

            let nodes = rows.into_iter().map(|row| {
                FabricNode {
                    node_id: row.get("node_id"),
                    ip_address: row.get("ip_address"),
                    proxy_listen_address: row.get("proxy_listen_address"),
                    capabilities: row.get("capabilities"),
                    agent_type: row.get("agent_type"),
                    status: serde_json::from_str(&row.get::<String, _>("status")).unwrap_or(NodeStatus::Offline),
                    last_seen: row.get("last_seen"),
                    created_at: row.get("created_at"),
                    metadata: serde_json::from_value(row.get("metadata")).unwrap_or_default(),
                }
            }).collect();

            return Ok(nodes);
        }

        // Fallback to RocksDB iteration (less efficient for this operation)
        if let Some(rocks) = &self.rocksdb {
            let mut nodes = Vec::new();
            let iter = rocks.iterator(rocksdb::IteratorMode::Start);
            
            for (key, value) in iter {
                if let Ok(key_str) = String::from_utf8(key.to_vec()) {
                    if key_str.starts_with("node:") {
                        if let Ok(node) = bincode::deserialize::<FabricNode>(&value) {
                            nodes.push(node);
                        }
                    }
                }
            }
            
            return Ok(nodes);
        }

        Ok(vec![])
    }

    async fn update_node_status(&self, node_id: &str, status: NodeStatus) -> StorageResult<()> {
        // Update in both stores
        if let Some(mut node) = self.get_node(node_id).await? {
            node.status = status;
            node.last_seen = Utc::now();
            self.store_node(&node).await?;
        }
        Ok(())
    }

    async fn delete_node(&self, node_id: &str) -> StorageResult<()> {
        // Delete from RocksDB
        if let Some(rocks) = &self.rocksdb {
            let key = Self::node_key(node_id);
            rocks.delete(key.as_bytes())?;
        }

        // Delete from PostgreSQL
        if let Some(pg) = &self.postgres {
            sqlx::query("DELETE FROM nodes WHERE node_id = $1")
                .bind(node_id)
                .execute(pg)
                .await?;
        }

        Ok(())
    }
}

// Additional implementations for AgentStorage and TelemetryStorage would follow similar patterns
// For brevity, showing the structure for NodeStorage implementation
