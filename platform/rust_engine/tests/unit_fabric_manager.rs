// Unit tests for FabricManager methods

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use tokio::sync::{broadcast, mpsc, Mutex};
    use nexus_prime_core::*;
    use nexus_prime_core::fabric_proto::fabric::FabricCommand;
    use chrono::Utc;

    fn setup_manager() -> FabricManager {
        let state = Arc::new(Mutex::new(FabricState::default()));
        let (event_bus_tx, _) = broadcast::channel(10);
        let (event_stream_tx, _) = broadcast::channel(10);
        let (command_tx, _command_rx) = mpsc::channel(10);
        FabricManager::new(state, event_bus_tx, event_stream_tx, command_tx)
    }

    #[tokio::test]
    async fn test_register_node() {
        let manager = setup_manager();
        let node = ComputeNode {
            id: "node-1".to_string(),
            node_type: "PC".to_string(),
            last_seen: Utc::now(),
            status: "Online".to_string(),
            capabilities: "CPU:4,RAM:16GB".to_string(),
            ip_address: "127.0.0.1".to_string(),
        };
        manager.register_node(node.clone()).await;
        let state = manager.state.lock().await;
        assert!(state.compute_nodes.contains_key("node-1"));
    }

    #[tokio::test]
    async fn test_update_node_status() {
        let manager = setup_manager();
        let node = ComputeNode {
            id: "node-2".to_string(),
            node_type: "PC".to_string(),
            last_seen: Utc::now(),
            status: "Online".to_string(),
            capabilities: "CPU:4,RAM:16GB".to_string(),
            ip_address: "127.0.0.1".to_string(),
        };
        manager.register_node(node.clone()).await;
        manager.update_node_status("node-2".to_string(), "Degraded".to_string(), None).await;
        let state = manager.state.lock().await;
        assert_eq!(state.compute_nodes["node-2"].status, "Degraded");
    }

    #[tokio::test]
    async fn test_register_ai_agent() {
        let manager = setup_manager();
        let agent = AIAgent {
            id: "agent-1".to_string(),
            name: "Synthesizer".to_string(),
            agent_type: "Synthesizer".to_string(),
            assigned_node_id: Some("node-1".to_string()),
            status: "Idle".to_string(),
            current_task: None,
            task_progress: None,
        };
        manager.register_ai_agent(agent.clone()).await;
        let state = manager.state.lock().await;
        assert!(state.ai_agents.contains_key("agent-1"));
    }

    #[tokio::test]
    async fn test_update_ai_agent_status() {
        let manager = setup_manager();
        let agent = AIAgent {
            id: "agent-2".to_string(),
            name: "Protector".to_string(),
            agent_type: "Protector".to_string(),
            assigned_node_id: Some("node-1".to_string()),
            status: "Idle".to_string(),
            current_task: None,
            task_progress: None,
        };
        manager.register_ai_agent(agent.clone()).await;
        manager.update_ai_agent_status("agent-2".to_string(), "Processing".to_string(), Some("TaskA".to_string()), Some(0.5)).await;
        let state = manager.state.lock().await;
        assert_eq!(state.ai_agents["agent-2"].status, "Processing");
        assert_eq!(state.ai_agents["agent-2"].current_task, Some("TaskA".to_string()));
        assert_eq!(state.ai_agents["agent-2"].task_progress, Some(0.5));
    }

    #[tokio::test]
    async fn test_issue_command_sends_to_channel() {
        let state = Arc::new(Mutex::new(FabricState::default()));
        let (event_bus_tx, _) = broadcast::channel(10);
        let (event_stream_tx, _) = broadcast::channel(10);
        let (command_tx, mut command_rx) = mpsc::channel(10);
        let manager = FabricManager::new(state, event_bus_tx, event_stream_tx, command_tx);
        let command = FabricCommand {
            command_id: "cmd-1".to_string(),
            target_id: "node-1".to_string(),
            command_type: "REBOOT_NODE".to_string(),
            parameters: Default::default(),
        };
        manager.issue_command(command.clone()).await;
        let received = command_rx.recv().await.unwrap();
        assert_eq!(received.command_id, "cmd-1");
    }

    #[tokio::test]
    async fn test_prune_stale_entities() {
        let manager = setup_manager();
        let old_time = Utc::now() - chrono::Duration::minutes(10);
        let node = ComputeNode {
            id: "node-stale".to_string(),
            node_type: "PC".to_string(),
            last_seen: old_time,
            status: "Online".to_string(),
            capabilities: "CPU:4,RAM:16GB".to_string(),
            ip_address: "127.0.0.1".to_string(),
        };
        manager.register_node(node.clone()).await;
        manager.prune_stale_entities().await;
        let state = manager.state.lock().await;
        assert!(!state.compute_nodes.contains_key("node-stale"));
    }
}
