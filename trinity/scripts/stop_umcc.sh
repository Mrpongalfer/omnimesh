#!/bin/bash
# UMCC Stop Script - Trinity Enhanced v5.0

echo "🛑 Stopping UMCC Server..."
echo "========================="

# Check if PID file exists
if [ -f /tmp/umcc_server.pid ]; then
    PID=$(cat /tmp/umcc_server.pid)
    
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ UMCC Server stopped (PID: $PID)"
        rm -f /tmp/umcc_server.pid
    else
        echo "⚠️  UMCC Server was not running"
        rm -f /tmp/umcc_server.pid
    fi
else
    echo "⚠️  No PID file found"
    # Try to find and kill any running UMCC servers
    pkill -f "umcc_server.py"
    echo "🔍 Attempted to kill any running UMCC processes"
fi

echo "🏁 UMCC shutdown complete"
