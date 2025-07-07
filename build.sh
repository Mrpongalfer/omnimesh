#!/bin/bash

# build.sh - Omnitide Compute Fabric: Master Build Orchestrator

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Building The Distributed Omnitide Compute Fabric ---"
echo "--- Architect's Will is Absolute. ---"

# 1. Validate Core Prerequisites for the entire fabric
echo "Checking for essential build tools..."
if ! command -v rustup &> /dev/null
then
    echo "ERROR: rustup (Rust toolchain manager) not found. Install from https://rustup.rs/"
    exit 1
fi
if ! command -v protoc &> /dev/null
then
    echo "ERROR: protoc (Protocol Buffers compiler) not found. Install it."
    echo "  - Debian/Ubuntu: sudo apt-get install protobuf-compiler"
    echo "  - macOS: brew install protobuf"
    echo "  - Windows: Follow instructions on https://grpc.io/docs/protoc-installation/"
    exit 1
fi
if ! command -v go &> /dev/null
then
    echo "WARNING: Go not found. Required for Go Compute Node Proxies (Phase 2)."
fi
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null
then
    echo "WARNING: Node.js/npm not found. Required for Chrome OS PWA/Wasm agents (Phase 3) and Solid.js UI (Phase 5)."
fi
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null
then
    echo "WARNING: Python3/pip3 not found. Required for AI Agents (Phase 4)."
fi
if ! command -v flutter &> /dev_null
then
    echo "WARNING: Flutter not found. Required for Mobile UI (Phase 5)."
fi
echo "Core build tools checked. Proceeding."

# 2. Update Rust Toolchain (Essential for Nexus Prime)
echo "Updating Rust toolchain to ensure compatibility..."
rustup update stable
echo "Rust toolchain updated."

# 3. Build Phases Orchestration
echo "Initiating phased build process. Each phase will build within its respective directory."

# Phase 1: Build Nexus Prime Rust Core
echo "--- PHASE 1: Building Nexus Prime Rust Core ---"
if [ -d "nexus-prime-core" ]; then
    (cd nexus-prime-core && ./build.sh) # Execute build script within nexus-prime-core directory
else
    echo "ERROR: 'nexus-prime-core' directory not found. Please ensure project structure is correct."
    echo "Refer to OMNITIDE_CODEX.md and README.md for expected structure."
    exit 1
fi
echo "--- PHASE 1 COMPLETE ---"

# Add placeholders for future phases
echo "--- PHASE 2: (Future) Building Go Compute Node Proxies ---"
# if [ -d "go-node-proxies" ]; then
#     (cd go-node-proxies && ./build.sh)
# else
#     echo "Skipping Phase 2: 'go-node-proxies' directory not found. This will be built in a later stage."
# fi

echo "--- PHASE 3: (Future) Building Chrome OS Compute Atomix Nodes (CCN Agents) ---"
echo "--- PHASE 4: (Future) Building AI Agents ---"
echo "--- PHASE 5: (Future) Building Architect's Omnitide Control Panel (UI) ---"
echo "--- PHASE 6: (Future) Building Omnitide Data Fabric Implementation ---"

echo "--- Master Build Orchestration Complete! ---"
echo "The Nexus Prime Rust Core should now be built and ready for execution."
echo "Refer to the OMNITIDE_CODEX.md for the complete fabric blueprint."
