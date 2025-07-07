#!/bin/bash

# Simple verification script
echo "🔧 Omnitide Fabric - Quick Verification"
echo "======================================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "✅ Project Structure:"
echo "  - Root README.md: $([ -f README.md ] && echo 'Present' || echo 'Missing')"
echo "  - CONTRIBUTING.md: $([ -f CONTRIBUTING.md ] && echo 'Present' || echo 'Missing')"
echo "  - Makefile: $([ -f Makefile ] && echo 'Present' || echo 'Missing')"
echo "  - Docker Compose: $([ -f docker-compose.yml ] && echo 'Present' || echo 'Missing')"

echo ""
echo "✅ Rust Components:"
echo "  - Cargo.toml: $([ -f nexus-prime-core/Cargo.toml ] && echo 'Present' || echo 'Missing')"
echo "  - Main source: $([ -f nexus-prime-core/src/main.rs ] && echo 'Present' || echo 'Missing')"
echo "  - Config module: $([ -f nexus-prime-core/src/config.rs ] && echo 'Present' || echo 'Missing')"
echo "  - Storage module: $([ -f nexus-prime-core/src/storage.rs ] && echo 'Present' || echo 'Missing')"
echo "  - Security module: $([ -f nexus-prime-core/src/security.rs ] && echo 'Present' || echo 'Missing')"
echo "  - Telemetry module: $([ -f nexus-prime-core/src/telemetry.rs ] && echo 'Present' || echo 'Missing')"

echo ""
echo "✅ Go Components:"
echo "  - go.mod: $([ -f go-node-proxies/go.mod ] && echo 'Present' || echo 'Missing')"
echo "  - Main source: $([ -f go-node-proxies/main.go ] && echo 'Present' || echo 'Missing')"
echo "  - Protobuf files: $([ -f go-node-proxies/internal/fabricpb/fabric.pb.go ] && echo 'Present' || echo 'Missing')"
echo "  - Container module: $([ -f go-node-proxies/internal/container/manager.go ] && echo 'Present' || echo 'Missing')"
echo "  - Monitor module: $([ -f go-node-proxies/internal/monitor/monitor.go ] && echo 'Present' || echo 'Missing')"

echo ""
echo "✅ Build Status:"
cd go-node-proxies
if go build . 2>/dev/null; then
    echo "  - Go build: Success"
    rm -f go-node-proxies
else
    echo "  - Go build: Failed"
fi

cd "$PROJECT_ROOT"

echo ""
echo "✅ Dependencies:"
echo "  - Go version: $(go version 2>/dev/null | cut -d' ' -f3 || echo 'Not installed')"
echo "  - Rust version: $(rustc --version 2>/dev/null | cut -d' ' -f2 || echo 'Not installed')"
echo "  - Docker: $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo 'Not installed')"
echo "  - Protoc: $(protoc --version 2>/dev/null | cut -d' ' -f2 || echo 'Not installed')"

echo ""
echo "🎉 Quick verification completed!"
echo ""
echo "To run the full system:"
if go build . 2>/dev/null; then
    echo "  - Go build: Success"
    rm -f go-node-proxies
else
    echo "  - Go build: Failed"
fi

echo ""
echo "✅ Dependencies:"
echo "  - Go version: $(go version 2>/dev/null | cut -d' ' -f3 || echo 'Not installed')"
echo "  - Rust version: $(rustc --version 2>/dev/null | cut -d' ' -f2 || echo 'Not installed')"
echo "  - Docker: $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo 'Not installed')"
echo "  - Protoc: $(protoc --version 2>/dev/null | cut -d' ' -f2 || echo 'Not installed')"

echo ""
echo "🎉 Quick verification completed!"
echo ""
echo "To run the full system:"
echo "  make dev"
echo ""
echo "To run individual components:"
echo "  cd nexus-prime-core && cargo run"
echo "  cd go-node-proxies && go run ."
