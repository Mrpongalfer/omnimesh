# 📚 OMNIMESH API Reference

**Complete API documentation for the Trinity Convergence Platform**

## 🎯 Overview

The OMNIMESH Trinity platform provides multiple API interfaces:
- **Natural Language CLI**: Conversational command interface
- **REST API**: HTTP-based programmatic interface  
- **gRPC API**: High-performance binary protocol
- **Python SDK**: Native Python integration

## 🗣️ Natural Language CLI API

### Command Execution
```bash
./interfaces/cli/nexus_cli.py [OPTIONS] COMMAND
```

#### Options
- `--interactive, -i`: Enter interactive mode
- `--json`: Output results in JSON format
- `--verbose, -v`: Enable verbose output
- `--help`: Show help message

#### Examples
```bash
# Basic command execution
./interfaces/cli/nexus_cli.py "check system health"

# JSON output for scripting
./interfaces/cli/nexus_cli.py --json "deploy in production mode"

# Interactive mode
./interfaces/cli/nexus_cli.py --interactive
```

### Supported Commands

#### Health Commands
```bash
"check system health"
"health check"  
"show system status"
"is everything operational?"
```

**Response Format:**
```json
{
  "success": true,
  "message": "Trinity health check completed",
  "health_status": {
    "core_orchestrator": "operational",
    "exwork_agent": "operational",
    "rust_engine": "operational", 
    "fabric_proxies": "operational",
    "web_frontend": "operational",
    "global_commands": "operational"
  }
}
```

#### Deployment Commands
```bash
"deploy in production mode"
"start production deployment"
"go live"
"deploy everything"
```

**Response Format:**
```json
{
  "success": true,
  "message": "LoL Nexus Compute Fabric deployed successfully",
  "deployment": {
    "status": "completed",
    "components_deployed": ["core", "agents", "proxies", "frontend"],
    "deployment_time": "2025-07-25T20:43:30Z"
  }
}
```

#### Build Commands
```bash
"build trinity system"
"compile everything"
"build all components"
"make the system"
```

**Response Format:**
```json
{
  "success": true,
  "message": "Trinity system build completed",
  "build": {
    "status": "success",
    "components": {
      "rust_engine": "compiled",
      "go_proxies": "compiled", 
      "python_orchestrator": "ready",
      "web_frontend": "built"
    },
    "build_time": "25m 32s"
  }
}
```

## 🌐 REST API

### Base URL
```
http://localhost:8080/api/v1
```

### Authentication
```bash
# Include API key in headers
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:8080/api/v1/health
```

### Endpoints

#### GET /health
Check system health status

**Request:**
```bash
curl -X GET http://localhost:8080/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T20:43:30Z",
  "components": {
    "core_orchestrator": {
      "status": "operational",
      "uptime": "5h 23m",
      "memory_usage": "245MB"
    },
    "exwork_agent": {
      "status": "operational", 
      "active_tasks": 3,
      "completed_tasks": 157
    },
    "rust_engine": {
      "status": "operational",
      "threads": 8,
      "processed_requests": 1024
    },
    "fabric_proxies": {
      "status": "operational",
      "active_connections": 12,
      "throughput": "1.2GB/s"
    }
  }
}
```

#### POST /execute
Execute natural language commands

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/execute \
     -H "Content-Type: application/json" \
     -d '{
       "command": "check system health",
       "timeout": 30,
       "format": "json"
     }'
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "command": "check system health",
  "action": "health_check",
  "result": {
    "success": true,
    "execution_time": "0.234s",
    "data": { /* health check results */ }
  }
}
```

#### POST /deploy
Deploy system components

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/deploy \
     -H "Content-Type: application/json" \
     -d '{
       "environment": "production",
       "components": ["all"],
       "strategy": "rolling_update"
     }'
```

**Response:**
```json
{
  "deployment_id": "deploy_xyz789",
  "status": "in_progress",
  "components": {
    "core_orchestrator": "deploying",
    "agents": "queued",
    "proxies": "queued",
    "frontend": "queued"
  },
  "estimated_completion": "2025-07-25T21:00:00Z"
}
```

#### GET /deploy/{deployment_id}
Check deployment status

**Request:**
```bash
curl -X GET http://localhost:8080/api/v1/deploy/deploy_xyz789
```

**Response:**
```json
{
  "deployment_id": "deploy_xyz789",
  "status": "completed",
  "progress": 100,
  "components": {
    "core_orchestrator": "deployed",
    "agents": "deployed", 
    "proxies": "deployed",
    "frontend": "deployed"
  },
  "completion_time": "2025-07-25T20:58:42Z"
}
```

#### POST /build
Build system components

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/build \
     -H "Content-Type: application/json" \
     -d '{
       "components": ["rust_engine", "go_proxies"],
       "optimization": "release",
       "parallel": true
     }'
```

**Response:**
```json
{
  "build_id": "build_def456",
  "status": "started",
  "components": {
    "rust_engine": "compiling",
    "go_proxies": "queued"
  },
  "estimated_time": "25m"
}
```

## ⚡ gRPC API

### Service Definition
```protobuf
syntax = "proto3";

package omnimesh.v1;

service TrinityService {
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
  rpc ExecuteCommand(ExecuteCommandRequest) returns (ExecuteCommandResponse);
  rpc Deploy(DeployRequest) returns (stream DeployResponse);
  rpc Build(BuildRequest) returns (stream BuildResponse);
}

message HealthCheckRequest {
  repeated string components = 1;
}

message HealthCheckResponse {
  bool healthy = 1;
  map<string, ComponentHealth> components = 2;
}

message ComponentHealth {
  string status = 1;
  map<string, string> metrics = 2;
}

message ExecuteCommandRequest {
  string command = 1;
  int32 timeout_seconds = 2;
  string format = 3;
}

message ExecuteCommandResponse {
  string request_id = 1;
  string action = 2;
  bool success = 3;
  string message = 4;
  bytes data = 5;
}
```

### Usage Examples

#### Python Client
```python
import grpc
from omnimesh.grpc import trinity_pb2, trinity_pb2_grpc

# Create connection
channel = grpc.insecure_channel('localhost:9090')
client = trinity_pb2_grpc.TrinityServiceStub(channel)

# Health check
request = trinity_pb2.HealthCheckRequest(
    components=['core_orchestrator', 'rust_engine']
)
response = client.HealthCheck(request)
print(f"System healthy: {response.healthy}")

# Execute command
request = trinity_pb2.ExecuteCommandRequest(
    command="check system health",
    timeout_seconds=30,
    format="json"
)
response = client.ExecuteCommand(request)
print(f"Command result: {response.success}")
```

#### Go Client
```go
package main

import (
    "context"
    "log"
    
    "google.golang.org/grpc"
    pb "github.com/mrpongalfer/omnimesh/grpc"
)

func main() {
    conn, err := grpc.Dial("localhost:9090", grpc.WithInsecure())
    if err != nil {
        log.Fatal(err)
    }
    defer conn.Close()
    
    client := pb.NewTrinityServiceClient(conn)
    
    // Health check
    resp, err := client.HealthCheck(context.Background(), &pb.HealthCheckRequest{
        Components: []string{"core_orchestrator", "rust_engine"},
    })
    if err != nil {
        log.Fatal(err)
    }
    log.Printf("System healthy: %v", resp.Healthy)
}
```

## 🐍 Python SDK

### Installation
```bash
pip install omnimesh-sdk
```

### Usage

#### Basic Client
```python
from omnimesh import TrinityClient

# Initialize client
client = TrinityClient(
    host="localhost",
    port=8080,
    api_key="your_api_key"
)

# Health check
health = client.health_check()
print(f"System status: {health.status}")

# Execute command
result = client.execute("check system health")
print(f"Command success: {result.success}")

# Deploy
deployment = client.deploy(
    environment="production",
    components=["all"]
)
print(f"Deployment ID: {deployment.id}")
```

#### Async Client
```python
import asyncio
from omnimesh import AsyncTrinityClient

async def main():
    client = AsyncTrinityClient(
        host="localhost",
        port=8080,
        api_key="your_api_key"
    )
    
    # Async health check
    health = await client.health_check()
    print(f"System status: {health.status}")
    
    # Async command execution
    result = await client.execute("deploy in production mode")
    print(f"Deployment success: {result.success}")

# Run async client
asyncio.run(main())
```

#### Configuration
```python
from omnimesh import TrinityClient, Config

# Custom configuration
config = Config(
    host="localhost",
    port=8080,
    api_key="your_api_key",
    timeout=60,
    retry_attempts=3,
    ssl_enabled=True
)

client = TrinityClient(config=config)
```

## 🔒 Authentication & Security

### API Key Authentication
```bash
# Generate API key
./interfaces/cli/nexus_cli.py "generate api key"

# Use API key in requests
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8080/api/v1/health
```

### JWT Authentication
```python
import jwt
from omnimesh import TrinityClient

# Create JWT token
token = jwt.encode({
    'user': 'admin',
    'permissions': ['read', 'write', 'deploy'],
    'exp': datetime.utcnow() + timedelta(hours=1)
}, 'your-secret-key')

# Use token
client = TrinityClient(
    host="localhost",
    port=8080,
    auth_token=token
)
```

### SSL/TLS Configuration
```python
from omnimesh import TrinityClient

client = TrinityClient(
    host="trinity.example.com",
    port=443,
    ssl_enabled=True,
    ssl_cert="/path/to/cert.pem",
    ssl_key="/path/to/key.pem"
)
```

## 📊 Response Formats

### Standard Response
```json
{
  "success": true|false,
  "message": "Human readable message",
  "data": { /* Response data */ },
  "metadata": {
    "request_id": "req_123",
    "timestamp": "2025-07-25T20:43:30Z",
    "execution_time": "0.234s"
  },
  "errors": [ /* Array of error objects */ ]
}
```

### Error Response
```json
{
  "success": false,
  "message": "Operation failed",
  "errors": [
    {
      "code": "COMPONENT_UNAVAILABLE",
      "message": "Rust engine is not responding",
      "component": "rust_engine",
      "timestamp": "2025-07-25T20:43:30Z"
    }
  ],
  "metadata": {
    "request_id": "req_123",
    "timestamp": "2025-07-25T20:43:30Z"
  }
}
```

## 🔧 Configuration API

### GET /config
Retrieve current configuration

**Response:**
```json
{
  "trinity": {
    "name": "LoL Nexus Compute Fabric",
    "version": "3.0.0",
    "mode": "production"
  },
  "core": {
    "orchestrator_port": 8080,
    "health_check_interval": 30
  },
  "agents": {
    "exwork_enabled": true,
    "auto_scaling": true
  }
}
```

### PUT /config
Update configuration

**Request:**
```json
{
  "core": {
    "health_check_interval": 60
  },
  "agents": {
    "auto_scaling": false
  }
}
```

## 📈 Monitoring API

### GET /metrics
Retrieve system metrics

**Response:**
```json
{
  "timestamp": "2025-07-25T20:43:30Z",
  "metrics": {
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 68.7,
      "disk_usage": 23.1
    },
    "trinity": {
      "requests_per_second": 123.4,
      "active_operations": 5,
      "total_operations": 1024
    },
    "components": {
      "rust_engine": {
        "threads_active": 8,
        "memory_mb": 512,
        "operations_completed": 456
      }
    }
  }
}
```

## 🚨 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = function(event) {
    console.log('Connected to Trinity WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Real-time Health Updates
```javascript
// Subscribe to health updates
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'health',
    interval: 5000
}));

// Receive health updates
ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    if (update.type === 'health_update') {
        console.log('Health status:', update.data);
    }
};
```

---

*For more examples and advanced usage, see our [SDK Documentation](sdk-reference.md) and [Integration Examples](examples.md).*
