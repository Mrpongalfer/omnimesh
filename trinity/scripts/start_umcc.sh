#!/bin/bash
# UMCC Start Script - Trinity Enhanced v5.0

echo "🚀 Starting UMCC Server..."
echo "=========================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

# Start UMCC Server
cd "$(dirname "$0")/.."
python3 core/shared/umcc_server.py &
UMCC_PID=$!

echo "✅ UMCC Server started (PID: $UMCC_PID)"
echo "📡 Listening on localhost:50051"
echo "🔧 To stop: ./scripts/stop_umcc.sh"

# Save PID for stop script
echo $UMCC_PID > /tmp/umcc_server.pid
