// nexus-prime-core/src/main.rs - The Unyielding Heart of the Nexus Prime

use nexus_prime_core::*;
use nexus_prime_core::fabric_proto::fabric::{
    fabric_service_server::{FabricService, FabricServiceServer},
    *,
};
use tokio_stream::wrappers::BroadcastStream;
use futures::StreamExt;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc};
use log::{info, warn};
use uuid::Uuid;
use tonic::{Request, Response, Status};
use tonic::transport::Server;
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::IntoResponse,
    routing::get,
    Router,
};
use std::net::SocketAddr;
use std::time::Duration;

// FabricServiceServerImpl: Implements the gRPC service definition for Nexus Prime
#[derive(Clone)] // Derive Clone for easy sharing in async contexts
pub struct FabricServiceServerImpl {
    fabric_manager: FabricManager,
    // For streaming fabric events to the UI/other listeners
    event_stream_tx: broadcast::Sender<FabricEvent>,
}

#[tonic::async_trait]
impl FabricService for FabricServiceServerImpl {
    type StreamFabricEventsStream =
        std::pin::Pin<Box<dyn tokio_stream::Stream<Item = Result<FabricEvent, tonic::Status>> + Send + 'static>>;

    // Handles registration of new compute nodes/proxies
    async fn register_agent(
        &self,
        request: Request<AgentRegistrationRequest>,
    ) -> Result<Response<AgentRegistrationResponse>, Status> {
        let req = request.into_inner();
        info!("[gRPC] Received registration request: {:?}", req);

        // Assign a unique Node ID
        let node_id = format!("node-{}", Uuid::new_v4());
        let node = ComputeNode {
            id: node_id.clone(),
            node_type: match AgentType::from_i32(req.agent_type) {
                Some(AgentType::Pc) => "PC".to_string(),
                Some(AgentType::Unspecified) => "Unknown".to_string(),
                _ => "Other".to_string(),
            },
            last_seen: chrono::Utc::now(),
            status: "Online".to_string(),
            capabilities: req.capabilities,
            ip_address: req.ip_address,
        };
        self.fabric_manager.register_node(node).await;

        Ok(Response::new(AgentRegistrationResponse {
            node_id,
            status: "REGISTERED".to_string(),
            message: "Successfully registered compute node.".to_string(),
        }))
    }

    // Handles status updates from compute nodes/proxies or AI agents
    async fn update_agent_status(
        &self,
        request: Request<AgentStatusUpdate>,
    ) -> Result<Response<CommandResponse>, Status> {
        let req = request.into_inner();
        info!("[gRPC] Received status update: {:?}", req);

        if req.node_id.is_empty() {
            return Err(Status::invalid_argument("Node ID cannot be empty."));
        }

        match StatusType::from_i32(req.status_type) {
            Some(StatusType::Node) => {
                self.fabric_manager
                    .update_node_status(
                        req.node_id.clone(),
                        req.status_value.clone(),
                        req.telemetry_data.clone(),
                    )
                    .await;
            }
            Some(StatusType::AiAgent) => {
                self.fabric_manager
                    .update_ai_agent_status(
                        req.node_id.clone(),
                        req.status_value.clone(),
                        req.current_task.clone(),
                        req.task_progress,
                    )
                    .await;
            }
            _ => {
                warn!("[gRPC] Received unknown status type in update: {}", req.status_type);
            }
        }

        Ok(Response::new(CommandResponse {
            status: "ACK".to_string(),
            message: "Status update received.".to_string(),
        }))
    }

    // Allows UI or other services to subscribe to fabric events
    async fn stream_fabric_events(
        &self,
        _request: tonic::Request<()>,
    ) -> Result<tonic::Response<Self::StreamFabricEventsStream>, tonic::Status> {
        info!("[gRPC] Client subscribed to fabric events.");
        let rx = self.event_stream_tx.subscribe();
        let stream = BroadcastStream::new(rx).map(|result| match result {
            Ok(event) => Ok(event),
            Err(e) => Err(tonic::Status::unknown(format!("Broadcast error: {}", e))),
        });
        Ok(tonic::Response::new(Box::pin(stream) as Self::StreamFabricEventsStream))
    }

    // Architect issues commands to the fabric (e.g., via UI)
    async fn send_fabric_command(
        &self,
        request: Request<FabricCommand>,
    ) -> Result<Response<CommandResponse>, Status> {
        let cmd = request.into_inner();
        self.fabric_manager.issue_command(cmd).await;
        Ok(Response::new(CommandResponse {
            status: "COMMAND_SENT".to_string(),
            message: "Command dispatched to fabric.".to_string(),
        }))
    }
}

// WebSocket handler
async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    ws.on_upgrade(|socket| handle_socket(socket, state))
}

async fn handle_socket(mut socket: WebSocket, state: Arc<AppState>) {
    // Subscribe to the event bus
    let mut rx = state.event_bus_tx.subscribe();

    // Send a welcome message
    if socket
        .send(Message::Text(
            "Connected to Nexus Prime WebSocket!".into(),
        ))
        .await
        .is_err()
    {
        return;
    }

    // Spawn a task to send events to the client
    tokio::spawn(async move {
        while let Ok(event) = rx.recv().await {
            let event_json = serde_json::to_string(&event).unwrap_or_else(|_| "{\"error\":\"Failed to serialize event\"}".to_string());
            if socket.send(Message::Text(event_json)).await.is_err() {
                break;
            }
        }
    });
}

// AppState for sharing between handlers
#[derive(Clone)]
struct AppState {
    event_bus_tx: broadcast::Sender<InternalFabricEvent>,
    fabric_manager: FabricManager,
}


// Workaround: define a local Empty struct matching google.protobuf.Empty
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct Empty {}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    info!("Nexus Prime Rust Core: Startup complete. Architect's Will is Absolute.");

    // Initialize shared state and channels
    let (event_bus_tx, _) = broadcast::channel(100);
    let (event_stream_tx, _) = broadcast::channel(100);
    let (command_tx, command_rx) = mpsc::channel(100);

    let db = sled::open("nexus_prime_db")?;

    let fabric_manager =
        FabricManager::new(event_bus_tx.clone(), event_stream_tx.clone(), command_tx, db);
    let grpc_service = FabricServiceServerImpl {
        fabric_manager: fabric_manager.clone(),
        event_stream_tx: event_stream_tx.clone(),
    };

    // Create the application state for Axum
    let app_state = Arc::new(AppState {
        event_bus_tx: event_bus_tx.clone(),
        fabric_manager: fabric_manager.clone(),
    });

    // Spawn the command processor
    tokio::spawn(command_processor(command_rx, fabric_manager.clone()));

    // Spawn the periodic pruner
    tokio::spawn(periodic_pruner(fabric_manager.clone()));


    // Start gRPC server (on 50053) and WebSocket server (on 8081) concurrently
    let grpc_addr = "[::1]:50053".parse()?;
    let ws_addr: SocketAddr = "0.0.0.0:8081".parse()?;

    let grpc = tokio::spawn(async move {
        info!("Starting gRPC server on {}", grpc_addr);
        Server::builder()
            .add_service(FabricServiceServer::new(grpc_service))
            .serve(grpc_addr)
            .await
    });

    let ws = tokio::spawn(async move {
        let app = Router::new()
            .route("/ws", get(ws_handler))
            .with_state(app_state);
        info!("Starting WebSocket server on {}", ws_addr);
        let listener = tokio::net::TcpListener::bind(ws_addr).await.unwrap();
        axum::serve(listener, app)
            .await
            .unwrap();
    });

    let (grpc_res, ws_res) = tokio::join!(grpc, ws);
    grpc_res??;
    ws_res;
    Ok(())
}

async fn command_processor(
    mut command_rx: mpsc::Receiver<FabricCommand>,
    fabric_manager: FabricManager,
) {
    info!("Command processor started.");
    while let Some(command) = command_rx.recv().await {
        info!("[CommandProcessor] Received command: {:?}", command);
        match command.command_type.as_str() {
            "DEPLOY_AGENT" => {
                let agent_name = command
                    .parameters
                    .get("name")
                    .cloned()
                    .unwrap_or_default();
                let agent_type = command
                    .parameters
                    .get("type")
                    .cloned()
                    .unwrap_or_default();
                let target_node_id = command.target_id;

                if agent_name.is_empty() || agent_type.is_empty() || target_node_id.is_empty() {
                    warn!("Invalid DEPLOY_AGENT command: missing parameters.");
                    continue;
                }

                info!(
                    "Executing DEPLOY_AGENT: name={}, type={}, target_node={}",
                    agent_name, agent_type, target_node_id
                );
                fabric_manager
                    .deploy_agent(target_node_id, agent_name, agent_type)
                    .await;
            }
            "STOP_AGENT" => {
                let target_agent_id = command.target_id;
                 if target_agent_id.is_empty() {
                    warn!("Invalid STOP_AGENT command: missing target_id.");
                    continue;
                }
                info!("Executing STOP_AGENT: target_agent={}", target_agent_id);
                fabric_manager.stop_agent(target_agent_id).await;
            }
            "MIGRATE_AGENT" => {
                let target_agent_id = command.target_id;
                let destination_node_id = command
                    .parameters
                    .get("destination_node")
                    .cloned()
                    .unwrap_or_default();

                if target_agent_id.is_empty() || destination_node_id.is_empty() {
                    warn!("Invalid MIGRATE_AGENT command: missing parameters.");
                    continue;
                }

                info!(
                    "Executing MIGRATE_AGENT: agent={}, destination={}",
                    target_agent_id, destination_node_id
                );
                fabric_manager
                    .migrate_agent(target_agent_id, destination_node_id)
                    .await;
            }
            _ => {
                warn!("Received unknown command type: {}", command.command_type);
            }
        }
    }
    info!("Command processor shut down.");
}

async fn periodic_pruner(fabric_manager: FabricManager) {
    info!("Periodic pruner started.");
    let mut interval = tokio::time::interval(Duration::from_secs(300)); // Every 5 minutes
    loop {
        interval.tick().await;
        info!("Running periodic stale entity prune.");
        fabric_manager.prune_stale_entities().await;
    }
}
