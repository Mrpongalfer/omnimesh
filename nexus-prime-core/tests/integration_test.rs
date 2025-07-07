// Integration test for Nexus Prime gRPC server

use tonic::transport::Channel;
use tonic::Request;
use tokio::time::{sleep, Duration, timeout};
use nexus_prime_core::fabric_proto::fabric::fabric_service_client::FabricServiceClient;
use nexus_prime_core::fabric_proto::fabric::*;
use tokio::sync::oneshot;

#[tokio::test]
async fn integration_nexus_prime_grpc() {
    // Create a shutdown channel
    let (shutdown_tx, shutdown_rx) = oneshot::channel();
    // Start the server in a background task with shutdown support
    let server_handle = tokio::spawn(async move {
        nexus_prime_core::spawn_server_with_shutdown(Some(shutdown_rx)).await.unwrap();
    });
    sleep(Duration::from_secs(1)).await; // Wait for server to start

    let mut client = FabricServiceClient::connect("http://[::1]:50051").await.unwrap();

    // Subscribe to StreamFabricEvents before sending any events
    let mut event_stream = client.stream_fabric_events(Request::new(())).await.unwrap().into_inner();

    // 1. RegisterAgent for a PC type
    let reg_req = AgentRegistrationRequest {
        agent_type: 1, // AGENT_TYPE_PC
        ip_address: "127.0.0.1".to_string(),
        capabilities: "CPU:4,RAM:16GB".to_string(),
    };
    let reg_resp = client.register_agent(Request::new(reg_req)).await.unwrap().into_inner();
    assert!(!reg_resp.node_id.is_empty());

    // 2. UpdateAgentStatus for the registered node
    let status_req = AgentStatusUpdate {
        node_id: reg_resp.node_id.clone(),
        status_type: 1, // STATUS_TYPE_NODE
        status_value: "Online".to_string(),
        telemetry_data: None,
        current_task: None,
        task_progress: None,
    };
    let status_resp = client.update_agent_status(Request::new(status_req)).await.unwrap().into_inner();
    assert_eq!(status_resp.status, "OK");

    // 3. UpdateAgentStatus for a dummy AI_AGENT
    let ai_status_req = AgentStatusUpdate {
        node_id: "dummy-agent".to_string(),
        status_type: 2, // STATUS_TYPE_AI_AGENT
        status_value: "Idle".to_string(),
        telemetry_data: None,
        current_task: Some("Thinking".to_string()),
        task_progress: Some(0.0),
    };
    let ai_status_resp = client.update_agent_status(Request::new(ai_status_req)).await.unwrap().into_inner();
    assert_eq!(ai_status_resp.status, "OK");

    // 4. Collect a few events (with timeout)
    let mut events = Vec::new();
    for _ in 0..3 {
        let event = timeout(Duration::from_secs(2), event_stream.message()).await;
        if let Ok(Ok(Some(ev))) = event {
            println!("Received event_type: {}", ev.event_type);
            events.push(ev.event_type);
        }
    }
    // Print all collected event types for debugging
    println!("Collected event types: {:?}", events);
    assert!(events.iter().any(|e|
        e.contains("NODE_REGISTERED") || e.contains("NODE_STATUS_UPDATE") ||
            e.contains("AGENT_STATUS_UPDATE")));

    // 5. SendFabricCommand (e.g., REBOOT_NODE)
    let cmd = FabricCommand {
        command_id: "cmd-1".to_string(),
        target_id: reg_resp.node_id,
        command_type: "REBOOT_NODE".to_string(),
        parameters: Default::default(),
    };
    let cmd_resp = client.send_fabric_command(Request::new(cmd)).await.unwrap().into_inner();
    assert_eq!(cmd_resp.status, "COMMAND_SENT");

    // Drop the event stream to close the connection
    drop(event_stream);
    // Trigger server shutdown and wait for server task to finish
    let _ = shutdown_tx.send(());
    let _ = server_handle.await;
}
