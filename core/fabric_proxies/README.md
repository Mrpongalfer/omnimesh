# 🐹 Go Node Proxies (GCNP)

[![Go](https://img.shields.io/badge/Go-1.23+-00ADD8?style=for-the-badge&logo=go)](https://golang.org/)
[![Docker](https://img.shields.io/badge/Docker-25.0+-2496ED?style=for-the-badge&logo=docker)](https://docker.com/)
[![gRPC](https://img.shields.io/badge/gRPC-1.59+-0F9D58?style=for-the-badge)](https://grpc.io/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Zero_Trust-red?style=for-the-badge&logo=security)](https://security.md)
[![Performance](https://img.shields.io/badge/Performance-Goroutines-cyan?style=for-the-badge&logo=go)](https://performance.md)

> **🚀 Next-Generation Compute Nodes** - Ultra-scalable, cloud-native container orchestration with bleeding-edge Go concurrency patterns

## 🌟 **Mission Statement**

Go Node Proxies represent the pinnacle of distributed edge computing - intelligent, self-managing compute nodes that seamlessly bridge the gap between the Rust orchestration core and heterogeneous workload execution environments. Built with Go's legendary concurrency primitives and modern cloud-native patterns, they establish the gold standard for edge compute management.

### 🎯 **Revolutionary Capabilities**

🚀 **Hyper-Concurrent Architecture**: Goroutine-based processing with work-stealing patterns  
🐋 **Advanced Container Orchestration**: Docker API mastery with lifecycle automation  
⚡ **Sub-Second Response Times**: Ultra-low latency command processing  
🧠 **Intelligent Resource Management**: ML-driven workload placement and optimization  
🛡️ **Zero-Trust Security**: End-to-end encryption with certificate pinning  
📊 **Real-Time Telemetry**: Comprehensive system monitoring with predictive analytics

## 🚀 Quick Start

### Prerequisites

```bash
# Install Go 1.23+
curl -sSL https://go.dev/dl/go1.23.linux-amd64.tar.gz | sudo tar -C /usr/local -xzf -

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Protocol Buffers compiler
sudo apt install -y protobuf-compiler
```

### Build and Run

```bash
# Install dependencies
go mod download

# Build the application
go build -ldflags="-s -w" -o gcnp .

# Run the proxy
./gcnp
```

## ⚙️ Configuration

### Environment Variables

```bash
# Server Configuration
PROXY_GRPC_PORT=50052          # gRPC server port
PROXY_HTTP_PORT=8080           # HTTP health/metrics port
NEXUS_ADDRESS=localhost:50053  # Nexus Prime gRPC address

# Docker Configuration  
DOCKER_HOST=unix:///var/run/docker.sock

# Monitoring Configuration
MONITOR_INTERVAL=30s           # System monitoring interval
CPU_THRESHOLD=80.0            # CPU usage alert threshold
MEMORY_THRESHOLD=85.0         # Memory usage alert threshold
```

## 🧪 Testing

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run benchmarks
go test -bench=. ./...
```

## 📊 Monitoring

### Health Endpoints

```bash
# Basic health check
curl http://localhost:8080/healthz

# System metrics
curl http://localhost:8080/metrics

# Agent status
curl http://localhost:8080/agents
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t omnitide/node-proxy:latest .

# Run container
docker run -d \
  --name omnitide-proxy \
  --restart unless-stopped \
  -p 50052:50052 \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  omnitide/node-proxy:latest
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: omnitide-node-proxy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: omnitide-node-proxy
  template:
    metadata:
      labels:
        app: omnitide-node-proxy
    spec:
      containers:
      - name: node-proxy
        image: omnitide/node-proxy:latest
        ports:
        - containerPort: 50052
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

## 🔐 Security

### Production Security

- **mTLS**: Mutual TLS for gRPC communications
- **Container Security**: Resource limits and capability dropping
- **Network Policies**: Restricted network access
- **Secret Management**: Encrypted configuration storage

## 🛣️ Roadmap

### Version 1.1
- [ ] mTLS Implementation
- [ ] OpenTelemetry Integration
- [ ] Configuration Validation
- [ ] Graceful Shutdown

### Version 1.2
- [ ] Auto-scaling Support
- [ ] Circuit Breaker Pattern
- [ ] Service Mesh Integration
- [ ] Advanced Metrics

## 🤝 Contributing

See the main [Contributing Guide](../CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

<div align="center">
  <strong>Part of the OmniTide Compute Fabric</strong>
</div>
