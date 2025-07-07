// nexus-prime-core/src/lib.rs - Core library for Nexus Prime

pub mod fabric_proto {
    pub mod fabric {
        include!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/fabric_proto/fabric.rs"));
    }
}

use crate::fabric_proto::fabric::FabricEvent;
use crate::fabric_proto::fabric::node_proxy_service_client::NodeProxyServiceClient;
use crate::fabric_proto::fabric::{DeployAgentRequest, StopAgentRequest};
use chrono::Utc;
use log::{error, info, warn};
use std::{collections::HashMap, sync::Arc};
use tokio::sync::{broadcast, mpsc, Mutex};
use tonic::transport::{Server, Channel};
use tonic::Request;
use uuid::Uuid;
use serde::{Deserialize, Serialize};

// --- Core Data Structures ---
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComputeNode {
    pub id: String,
    pub node_type: String,
    pub last_seen: chrono::DateTime<Utc>,
    pub status: String,
    pub capabilities: String,
    pub ip_address: String,
    pub proxy_listen_address: Option<String>, // Added to store the proxy's gRPC address
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIAgent {
    pub id: String,
    pub name: String,
    pub agent_type: String,
    pub assigned_node_id: Option<String>,
    pub status: String,
    pub current_task: Option<String>,
    pub task_progress: Option<f32>,
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct FabricState {
    pub compute_nodes: HashMap<String, ComputeNode>,
    pub ai_agents: HashMap<String, AIAgent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InternalFabricEvent {
    NodeRegistered(ComputeNode),
    NodeStatusUpdate(String, String, Option<String>), // Simplified: removed TelemetryData
    NodePruned(String),
    AgentRegistered(AIAgent),
    AgentStatusUpdate(String, String, Option<String>, Option<f32>),
    FabricCommandIssued(String, String), // Simplified: command_type and target_id only
}

#[derive(Clone)]
pub struct FabricManager {
    pub state: Arc<Mutex<FabricState>>,
    pub event_bus_tx: broadcast::Sender<InternalFabricEvent>,
    pub event_stream_tx: broadcast::Sender<FabricEvent>,
    pub command_tx: mpsc::Sender<fabric_proto::fabric::FabricCommand>,
    db: sled::Db,
    node_clients: Arc<Mutex<HashMap<String, NodeProxyServiceClient<Channel>>>>, // gRPC clients for each node
}

impl FabricManager {
    pub fn new(
        event_bus_tx: broadcast::Sender<InternalFabricEvent>,
        event_stream_tx: broadcast::Sender<FabricEvent>,
        command_tx: mpsc::Sender<fabric_proto::fabric::FabricCommand>,
        db: sled::Db,
    ) -> Self {
        let state = Self::load_state_from_db(&db).unwrap_or_default();
        FabricManager { 
            state: Arc::new(Mutex::new(state)), 
            event_bus_tx, 
            event_stream_tx,
            command_tx, 
            db,
            node_clients: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    fn load_state_from_db(db: &sled::Db) -> Result<FabricState, Box<dyn std::error::Error>> {
        let state_bytes = db.get("fabric_state")?.ok_or("No state found in DB")?;
        let state: FabricState = bincode::deserialize(&state_bytes)?;
        info!("Successfully loaded fabric state from database.");
        Ok(state)
    }

    async fn save_state(&self) -> Result<(), Box<dyn std::error::Error>> {
        let state = self.state.lock().await;
        let state_bytes = bincode::serialize(&*state)?;
        self.db.insert("fabric_state", state_bytes)?;
        self.db.flush_async().await?;
        info!("Successfully saved fabric state to database.");
        Ok(())
    }

    fn convert_event(event: &InternalFabricEvent) -> FabricEvent {
        use crate::fabric_proto::fabric::FabricEvent;
        use chrono::Utc;
        use std::collections::HashMap;
        match event {
            InternalFabricEvent::NodeRegistered(node) => {
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "NODE_REGISTERED".to_string(),
                    message: format!("Node registered: {}", node.id),
                    metadata: HashMap::new(),
                    telemetry: None,
                }
            },
            InternalFabricEvent::NodeStatusUpdate(node_id, status, _telemetry_summary) => {
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "NODE_STATUS_UPDATE".to_string(),
                    message: format!("Node {} status updated: {}", node_id, status),
                    metadata: HashMap::new(),
                    telemetry: None, // We'll keep telemetry in the original gRPC call
                }
            },
            InternalFabricEvent::NodePruned(node_id) => {
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "NODE_PRUNED".to_string(),
                    message: format!("Node pruned: {}", node_id),
                    metadata: HashMap::new(),
                    telemetry: None,
                }
            },
            InternalFabricEvent::AgentRegistered(agent) => {
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "AGENT_REGISTERED".to_string(),
                    message: format!("Agent registered: {}", agent.id),
                    metadata: HashMap::new(),
                    telemetry: None,
                }
            },
            InternalFabricEvent::AgentStatusUpdate(agent_id, status, task, progress) => {
                let mut metadata = HashMap::new();
                if let Some(task) = task { metadata.insert("current_task".to_string(), task.clone()); }
                if let Some(progress) = progress { metadata.insert("task_progress".to_string(), progress.to_string()); }
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "AGENT_STATUS_UPDATE".to_string(),
                    message: format!("Agent {} status updated: {}", agent_id, status),
                    metadata,
                    telemetry: None,
                }
            },
            InternalFabricEvent::FabricCommandIssued(command_type, target_id) => {
                FabricEvent {
                    event_id: uuid::Uuid::new_v4().to_string(),
                    timestamp: Utc::now().to_rfc3339(),
                    event_type: "FABRIC_COMMAND_ISSUED".to_string(),
                    message: format!("Command issued: {} to {}", command_type, target_id),
                    metadata: HashMap::new(),
                    telemetry: None,
                }
            },
        }
    }

    async fn broadcast_event(&self, event: InternalFabricEvent) {
        // Send the internal event to internal listeners
        if self.event_bus_tx.send(event.clone()).is_err() {
            warn!("No internal listeners for event bus, event was dropped.");
        }
        
        // Convert the internal event to an external FabricEvent and broadcast it
        let fabric_event = Self::convert_event(&event);
        if self.event_stream_tx.send(fabric_event).is_err() {
            warn!("No external listeners for event stream, event was dropped.");
        }
    }

    // Register a new compute node (e.g., when it's first connected)
    pub async fn register_node(&self, node: ComputeNode) {
        let mut state = self.state.lock().await;
        info!("[FabricManager] Registering node: {:?}", node);
        
        // If the node has a proxy listen address, create a gRPC client for it
        if let Some(proxy_addr) = &node.proxy_listen_address {
            if let Ok(channel) = tonic::transport::Channel::from_shared(format!("http://{}", proxy_addr)) {
                if let Ok(channel) = channel.connect().await {
                    let client = NodeProxyServiceClient::new(channel);
                    let mut clients = self.node_clients.lock().await;
                    clients.insert(node.id.clone(), client);
                    info!("[FabricManager] Created gRPC client for node {} at {}", node.id, proxy_addr);
                } else {
                    warn!("[FabricManager] Failed to connect to node proxy at {}", proxy_addr);
                }
            }
        }
        
        state.compute_nodes.insert(node.id.clone(), node.clone());
        self.broadcast_event(InternalFabricEvent::NodeRegistered(node)).await;
        if let Err(e) = self.save_state().await {
            error!("Failed to save state after registering node: {}", e);
        }
    }

    // Update compute node status
    pub async fn update_node_status(&self, node_id: String, status: String, _telemetry: Option<fabric_proto::fabric::TelemetryData>) {
        let mut state = self.state.lock().await;
        if let Some(node) = state.compute_nodes.get_mut(&node_id) {
            info!("[FabricManager] Updating node {}: status to {}", node_id, status);
            node.status = status.clone();
            node.last_seen = chrono::Utc::now();
            self.broadcast_event(InternalFabricEvent::NodeStatusUpdate(node_id, status, None)).await;
            if let Err(e) = self.save_state().await {
                error!("Failed to save state after updating node status: {}", e);
            }
        } else {
            warn!("[FabricManager] Attempted to update status for unknown node: {}", node_id);
        }
    }

    // Register a new AI agent (e.g., when it's deployed to a node)
    pub async fn register_ai_agent(&self, agent: AIAgent) {
        let mut state = self.state.lock().await;
        info!("[FabricManager] Registering AI agent: {:?}", agent);
        state.ai_agents.insert(agent.id.clone(), agent.clone());
        self.broadcast_event(InternalFabricEvent::AgentRegistered(agent)).await;
        if let Err(e) = self.save_state().await {
            error!("Failed to save state after registering agent: {}", e);
        }
    }

    // Update AI agent status
    pub async fn update_ai_agent_status(&self, agent_id: String, status: String, current_task: Option<String>, task_progress: Option<f32>) {
        let mut state = self.state.lock().await;
        if let Some(agent) = state.ai_agents.get_mut(&agent_id) {
            info!("[FabricManager] Updating AI agent {}: status to {}", agent_id, status);
            agent.status = status.clone();
            agent.current_task = current_task.clone();
            agent.task_progress = task_progress;
            self.broadcast_event(InternalFabricEvent::AgentStatusUpdate(agent_id, status, current_task, task_progress)).await;
            if let Err(e) = self.save_state().await {
                error!("Failed to save state after updating agent status: {}", e);
            }
        } else {
            warn!("[FabricManager] Attempted to update status for unknown AI agent: {}", agent_id);
        }
    }

    pub async fn issue_command(&self, command: fabric_proto::fabric::FabricCommand) {
        info!("[FabricManager] Issuing command: {:?}", command);
        let _ = self.command_tx.send(command.clone()).await;
        self.broadcast_event(InternalFabricEvent::FabricCommandIssued(command.command_type, command.target_id)).await;
    }

    pub async fn prune_stale_entities(&self) {
        let mut state = self.state.lock().await;
        let now = chrono::Utc::now();
        let mut stale_nodes = Vec::new();
        let mut stale_agents = Vec::new();
        for (id, node) in &state.compute_nodes {
            if (now - node.last_seen).num_minutes() > 5 {
                stale_nodes.push(id.clone());
            }
        }
        for id in stale_nodes.clone() {
            warn!("[FabricManager] Pruning stale node: {}", id);
            state.compute_nodes.remove(&id);
            self.broadcast_event(InternalFabricEvent::NodePruned(id)).await;
        }
        for (id, agent) in &state.ai_agents {
            if (now - agent.assigned_node_id.as_ref().map_or(now, |_| chrono::Utc::now())).num_minutes() > 10 {
                stale_agents.push(id.clone());
            }
        }
        for id in stale_agents.clone() {
            warn!("[FabricManager] Pruning stale AI agent: {}", id);
            state.ai_agents.remove(&id);
            // Consider an event for AgentPruned too
        }
        if !stale_nodes.is_empty() || !stale_agents.is_empty() {
            if let Err(e) = self.save_state().await {
                error!("Failed to save state after pruning entities: {}", e);
            }
        }
    }

    // --- Agent Lifecycle Management ---

    pub async fn deploy_agent(&self, target_node_id: String, name: String, agent_type: String) {
        let state = self.state.lock().await;
        if let Some(node) = state.compute_nodes.get(&target_node_id) {
            if node.status == "Online" {
                let agent_id = format!("agent-{}", Uuid::new_v4());
                let new_agent = AIAgent {
                    id: agent_id.clone(),
                    name: name.clone(),
                    agent_type: agent_type.clone(),
                    assigned_node_id: Some(target_node_id.clone()),
                    status: "Deploying".to_string(),
                    current_task: None,
                    task_progress: None,
                };
                
                info!("[FabricManager] Deploying new agent {:?} to node {}", new_agent, target_node_id);
                
                // Get the gRPC client for this node
                let clients = self.node_clients.lock().await;
                if let Some(client) = clients.get(&target_node_id) {
                    let mut client = client.clone();
                    drop(state);
                    drop(clients);
                    
                    // Send the deploy command to the node proxy
                    let deploy_req = DeployAgentRequest {
                        agent_id: agent_id.clone(),
                        agent_type: agent_type.clone(),
                        name: name.clone(),
                        parameters: HashMap::new(),
                    };
                    
                    match client.deploy_agent(Request::new(deploy_req)).await {
                        Ok(response) => {
                            let resp = response.into_inner();
                            info!("[FabricManager] Deploy command sent successfully: {}", resp.message);
                            
                            // Update the agent status to "Running" if deployment was successful
                            let mut state = self.state.lock().await;
                            if let Some(agent) = state.ai_agents.get_mut(&agent_id) {
                                agent.status = if resp.status == "SUCCESS" { "Running".to_string() } else { "Failed".to_string() };
                            } else {
                                state.ai_agents.insert(agent_id.clone(), new_agent.clone());
                            }
                            drop(state);
                            
                            self.broadcast_event(InternalFabricEvent::AgentRegistered(new_agent)).await;
                        }
                        Err(e) => {
                            error!("[FabricManager] Failed to send deploy command to node {}: {}", target_node_id, e);
                        }
                    }
                } else {
                    warn!("[FabricManager] No gRPC client available for node {}", target_node_id);
                }
            } else {
                warn!("[FabricManager] Cannot deploy agent to node {} because it is not Online", target_node_id);
            }
        } else {
            warn!("[FabricManager] Cannot deploy agent to non-existent node {}", target_node_id);
        }
        
        if let Err(e) = self.save_state().await {
            error!("Failed to save state after deploying agent: {}", e);
        }
    }

    pub async fn stop_agent(&self, agent_id: String) {
        let mut state = self.state.lock().await;
        if let Some(agent) = state.ai_agents.get_mut(&agent_id) {
            if let Some(node_id) = &agent.assigned_node_id {
                info!("[FabricManager] Stopping agent {}", agent_id);
                
                // Get the gRPC client for the node this agent is running on
                let clients = self.node_clients.lock().await;
                if let Some(client) = clients.get(node_id) {
                    let mut client = client.clone();
                    let node_id_clone = node_id.clone();
                    drop(state);
                    drop(clients);
                    
                    // Send the stop command to the node proxy
                    let stop_req = StopAgentRequest {
                        agent_id: agent_id.clone(),
                    };
                    
                    match client.stop_agent(Request::new(stop_req)).await {
                        Ok(response) => {
                            let resp = response.into_inner();
                            info!("[FabricManager] Stop command sent successfully: {}", resp.message);
                            
                            // Update the agent status
                            let mut state = self.state.lock().await;
                            if let Some(agent) = state.ai_agents.get_mut(&agent_id) {
                                agent.status = if resp.status == "SUCCESS" { "Stopped".to_string() } else { "Error".to_string() };
                                
                                let agent_clone = agent.clone();
                                drop(state);
                                
                                self.broadcast_event(InternalFabricEvent::AgentStatusUpdate(
                                    agent_id, 
                                    agent_clone.status, 
                                    agent_clone.current_task, 
                                    agent_clone.task_progress
                                )).await;
                            }
                        }
                        Err(e) => {
                            error!("[FabricManager] Failed to send stop command to node {}: {}", node_id_clone, e);
                        }
                    }
                } else {
                    warn!("[FabricManager] No gRPC client available for node {}", node_id);
                }
            } else {
                warn!("[FabricManager] Agent {} is not assigned to any node", agent_id);
            }
        } else {
            warn!("[FabricManager] Attempted to stop non-existent agent {}", agent_id);
        }

        if let Err(e) = self.save_state().await {
            error!("Failed to save state after stopping agent: {}", e);
        }
    }

    pub async fn migrate_agent(&self, agent_id: String, destination_node_id: String) {
        let mut state = self.state.lock().await;
        if state.compute_nodes.get(&destination_node_id).is_none() {
            warn!("[FabricManager] Cannot migrate agent to non-existent node {}", destination_node_id);
            return;
        }

        if let Some(agent) = state.ai_agents.get_mut(&agent_id) {
            info!("[FabricManager] Migrating agent {} to node {}", agent_id, destination_node_id);
            agent.assigned_node_id = Some(destination_node_id.clone());
            agent.status = "Migrating".to_string();
            
            let agent_clone = agent.clone();
            drop(state);

            self.broadcast_event(InternalFabricEvent::AgentStatusUpdate(
                agent_id, 
                agent_clone.status, 
                agent_clone.current_task, 
                agent_clone.task_progress
            )).await;

            if let Err(e) = self.save_state().await {
                error!("Failed to save state after migrating agent: {}", e);
            }
        } else {
            warn!("[FabricManager] Attempted to migrate non-existent agent {}", agent_id);
        }
    }
}

pub struct FabricServiceServerImpl {
    pub fabric_manager: FabricManager,
    pub event_stream_tx: broadcast::Sender<fabric_proto::fabric::FabricEvent>,
}

#[tonic::async_trait]
impl fabric_proto::fabric::fabric_service_server::FabricService for FabricServiceServerImpl {
    type StreamFabricEventsStream = std::pin::Pin<Box<dyn tokio_stream::Stream<Item = Result<fabric_proto::fabric::FabricEvent, tonic::Status>> + Send + 'static>>;

    async fn register_agent(
        &self,
        request: tonic::Request<fabric_proto::fabric::AgentRegistrationRequest>,
    ) -> Result<tonic::Response<fabric_proto::fabric::AgentRegistrationResponse>, tonic::Status> {
        let req = request.into_inner();
        info!("[gRPC] Received registration request: {:?}", req);
        let node_id = format!("node-{}", Uuid::new_v4());
        let node = ComputeNode {
            id: node_id.clone(),
            node_type: match req.agent_type {
                x if x == fabric_proto::fabric::AgentType::Pc as i32 => "PC".to_string(),
                x if x == fabric_proto::fabric::AgentType::Unspecified as i32 => "Unknown".to_string(),
                _ => "Other".to_string(),
            },
            last_seen: chrono::Utc::now(),
            status: "Online".to_string(),
            capabilities: req.capabilities,
            ip_address: req.ip_address,
            proxy_listen_address: if req.proxy_listen_address.is_empty() { None } else { Some(req.proxy_listen_address) },
        };
        self.fabric_manager.register_node(node).await;
        Ok(tonic::Response::new(fabric_proto::fabric::AgentRegistrationResponse {
            node_id,
            status: "REGISTERED".to_string(),
            message: "Successfully registered compute node.".to_string(),
        }))
    }

    async fn update_agent_status(
        &self,
        request: tonic::Request<fabric_proto::fabric::AgentStatusUpdate>,
    ) -> Result<tonic::Response<fabric_proto::fabric::CommandResponse>, tonic::Status> {
        let req = request.into_inner();
        info!("[gRPC] Received status update: {:?}", req);
        if req.node_id.is_empty() {
            return Err(tonic::Status::invalid_argument("Node ID cannot be empty."));
        }
        match req.status_type {
            x if x == fabric_proto::fabric::StatusType::Node as i32 => {
                self.fabric_manager.update_node_status(
                    req.node_id.clone(),
                    req.status_value.clone(),
                    req.telemetry_data.clone(),
                ).await;
            },
            x if x == fabric_proto::fabric::StatusType::AiAgent as i32 => {
                self.fabric_manager.update_ai_agent_status(
                    req.node_id.clone(),
                    req.status_value.clone(),
                    req.current_task.clone(),
                    req.task_progress,
                ).await;
            },
            _ => {}
        }
        Ok(tonic::Response::new(fabric_proto::fabric::CommandResponse {
            status: "OK".to_string(),
            message: "Status update received.".to_string(),
        }))
    }

    async fn stream_fabric_events(
        &self,
        _request: tonic::Request<()>,
    ) -> Result<tonic::Response<Self::StreamFabricEventsStream>, tonic::Status> {
        use async_stream::try_stream;
        let mut rx = self.event_stream_tx.subscribe();
        let stream = try_stream! {
            loop {
                let event = rx.recv().await.map_err(|e| tonic::Status::unknown(format!("Broadcast error: {}", e)))?;
                yield event;
            }
        };
        Ok(tonic::Response::new(Box::pin(stream) as Self::StreamFabricEventsStream))
    }

    async fn send_fabric_command(
        &self,
        request: tonic::Request<fabric_proto::fabric::FabricCommand>,
    ) -> Result<tonic::Response<fabric_proto::fabric::CommandResponse>, tonic::Status> {
        let cmd = request.into_inner();
        self.fabric_manager.issue_command(cmd).await;
        Ok(tonic::Response::new(fabric_proto::fabric::CommandResponse {
            status: "COMMAND_SENT".to_string(),
            message: "Command dispatched to fabric.".to_string(),
        }))
    }
}

pub async fn spawn_server_with_shutdown(shutdown: Option<tokio::sync::oneshot::Receiver<()>>) -> Result<(), Box<dyn std::error::Error>> {
    let (event_bus_tx, _) = broadcast::channel(100);
    let (command_tx, _) = mpsc::channel(100);
    let (event_stream_tx, _) = broadcast::channel(100);
    let db = sled::open("nexus_prime_db")?;
    let fabric_manager = FabricManager::new(event_bus_tx.clone(), event_stream_tx.clone(), command_tx.clone(), db.clone());
    let grpc_service = FabricServiceServerImpl {
        fabric_manager: fabric_manager.clone(),
        event_stream_tx: event_stream_tx.clone(),
    };
    let addr = "[::1]:50053".parse()?;
    let server = Server::builder()
        .add_service(fabric_proto::fabric::fabric_service_server::FabricServiceServer::new(grpc_service));
    match shutdown {
        Some(shutdown_rx) => {
            server.serve_with_shutdown(addr, async {
                shutdown_rx.await.ok();
            }).await?;
        },
        None => {
            server.serve(addr).await?;
        }
    }
    Ok(())
}

// Keep the original spawn_server for normal use
pub async fn spawn_server() -> Result<(), Box<dyn std::error::Error>> {
    spawn_server_with_shutdown(None).await
}

// Advanced modules for production-grade features
pub mod config;
pub mod storage;
pub mod security;
pub mod telemetry;

// Re-export commonly used types from new modules
pub use config::NexusConfig;
pub use storage::{HybridStorage, NodeStorage, AgentStorage, TelemetryStorage};
pub use security::{SecurityManager, Permission, EntityType};
pub use telemetry::{TelemetryManager, SystemMetrics, FabricMetrics};

// Export other core types and logic as needed for tests and main
