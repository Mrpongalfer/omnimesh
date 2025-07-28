# Copilot Agent Mode Instructions: PHASE 1 - Building Nexus Prime Rust Core

## Mission Briefing: Constructing the Fabric's Core

Your mission, as the assigned development agent, is to meticulously build out the foundational Rust core for the Nexus Prime. **You MUST operate with the complete, overarching context provided in the `OMNITIDE_CODEX.md`**. Refer to it for all architectural patterns, security mandates, performance targets, and integration protocols.

**Current Directory Context:** You are operating within the `nexus-prime-core/` subdirectory of the main project.

---

## Directives:

1.  **Initial Project Setup & Dependencies (`Cargo.toml`):**
    * **Verify `Cargo.toml`:** Ensure the `Cargo.toml` file (at `nexus-prime-core/Cargo.toml`) correctly defines the Rust project (`nexus-prime-core`) and includes all necessary dependencies **exactly as specified in the OMNITIDE_CODEX.md, Section II.B, "Core Orchestration Engine (NPE)" -> "Framework/Libraries" and the `Cargo.toml` content in the OMNITIDE_MANIFEST_PRIME.**
    * **Verify `build.rs`:** Confirm that `nexus-prime-core/build.rs` exists and is correctly configured to generate protobufs into `src/fabric_proto/`.

2.  **Protobuf Definition (`proto/fabric.proto`) Completion:**
    * **Verify `fabric.proto`:** Ensure the `nexus-prime-core/proto/fabric.proto` file is **complete and precise**, matching the definition provided in **Section 1.1 of the OMNITIDE_MANIFEST_PRIME** (which is a copy of `OMNITIDE_CODEX.md`, Section II.B). This file is critical for `tonic_build` generation.

3.  **Rust Core Implementation (`src/main.rs` and `src/fabric_proto/`):**
    * **Integrate Base Code:** Ensure the `src/main.rs` file contains the complete, foundational Rust code provided in **Section 1.4 of the OMNITIDE_MANIFEST_PRIME.**
    * **Review and Refine `FabricManager`:**
        * Confirm the `register_node`, `update_node_status`, `register_ai_agent`, `update_ai_agent_status`, `issue_command`, and `prune_stale_entities` methods are implemented as per the provided `main.rs` content.
        * **CRITICAL:** Ensure `prune_stale_entities` correctly handles **both `ComputeNode` and `AIAgent` timeouts/stale detections** based on `last_seen` timestamps or absence of heartbeats.
    * **Refine `FabricServiceServerImpl`:**
        * Confirm `register_agent`, `update_agent_status`, `stream_fabric_events`, and `send_fabric_command` are correctly implemented.
        * Ensure `stream_fabric_events` accurately maps all `InternalFabricEvent` types to `FabricEvent` types for external consumption, including relevant metadata.
    * **Refine `command_rx` processing loop (in `main()`):**
        * This loop (currently a placeholder) is responsible for taking commands from the `FabricManager` and dispatching them. For *this phase*, ensure it *logs* the command and *simulates* dispatch as detailed in the `main.rs` comments. **Do not attempt actual network dispatch to non-existent proxies yet.** Its primary purpose here is to confirm the command flow from the `FabricManager`.
    * **Logging:** Verify `env_logger::init()` is called in `main()` and that `log::info!`, `warn!`, `error!` macros are used consistently throughout `main.rs` for clear operational feedback.

4.  **Unit & Integration Tests (Kratos Aspect Mandate):**
    * **Create `nexus-prime-core/tests/` directory.**
    * **Unit Tests:** Implement comprehensive unit tests for key `FabricManager` methods.
        * `test_register_node`
        * `test_update_node_status`
        * `test_register_ai_agent`
        * `test_update_ai_agent_status`
        * `test_issue_command_sends_to_channel`
        * `test_prune_stale_entities` (verify nodes/agents are removed after timeout)
    * **Integration Tests (`tests/integration_test.rs`):**
        * Write an integration test that:
            1.  Starts the Nexus Prime gRPC server in a separate Tokio task.
            2.  Creates a `tonic` gRPC client to connect to the server.
            3.  Performs the following sequence:
                * Calls `RegisterAgent` for a `PC` type. Verify response.
                * Calls `UpdateAgentStatus` for the registered node (Node StatusType) with telemetry. Verify response.
                * Calls `UpdateAgentStatus` to simulate an `AI_AGENT` reporting status (AI Agent StatusType, use a dummy agent ID).
                * Subscribes to `StreamFabricEvents` and asynchronously collects a few events.
                * Calls `SendFabricCommand` (e.g., "REBOOT_NODE").
            4.  Verifies that the collected `FabricEvent`s match the expected types and content (e.g., `NODE_REGISTERED`, `NODE_STATUS_UPDATE`, `AI_AGENT_STATUS_UPDATE`, `FABRIC_COMMAND_ISSUED`).
            5.  Ensures the server logs (visible in agent's output) reflect these interactions.

---

## Final Validation & Readiness Check for Phase 1:

* **Execute `../build.sh` from the root directory.** This will orchestrate the build process for this phase.
* **Confirm Successful Build:** Ensure `cargo build --release` completes successfully within `nexus-prime-core/`.
* **Confirm All Tests Pass:** Ensure `cargo test --release` within `nexus-prime-core/` shows all unit and integration tests passing.
* **Run Executable & Observe Logs:** Execute `target/release/nexus-prime-core` (from `nexus-prime-core/` directory) and verify its console output demonstrates correct initialization, simulated command processing, and event broadcasting.

---

**Architect's Will is Absolute.** Proceed with the utmost precision and efficiency. Your comprehensive understanding of the `OMNITIDE_CODEX.md` is vital for successful execution.
