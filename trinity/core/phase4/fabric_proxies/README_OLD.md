# Go Compute Node Proxy (GCNP)

This directory contains the Go-based Compute Node Proxy for the Distributed Omnitide Compute Fabric.

## Features
- Registers with Nexus Prime (Rust Core) via gRPC
- Sends status and telemetry updates
- Subscribes to real-time fabric events
- Designed for cross-platform deployment (Linux, Windows, macOS)

## Development

### Prerequisites
- Go 1.22+
- protoc (Protocol Buffers compiler)
- `protoc-gen-go` and `protoc-gen-go-grpc` in your PATH

### Code Generation

```
./generate_proto.sh
```

### Build

```
go build -o gcnp main.go
```

### Test

```
go test -v ./...
```

### CI
- See `.github/workflows/go-ci.yml` for automated build/test pipeline.

## Docker Deployment

Build and run the GCNP in Docker:

```
docker build -t omnimesh/gcnp .
docker run --rm -e NEXUS_PRIME_ADDR=host.docker.internal:50051 omnimesh/gcnp
```

Or with Docker Compose:

```
docker-compose up --build
```

## Docker Swarm: One-Touch Node Join

To add a new node to your Swarm cluster:

1. On the manager node, initialize the swarm (if not already):
   ```
   docker swarm init
   ```
2. On the new node, run:
   ```
   ./auto-swarm-join.sh <manager-ip>
   ```
3. Deploy the stack from the manager:
   ```
   docker stack deploy -c docker-stack.yml omnimesh
   ```

This enables rapid, automated scaling of GCNP nodes across your cluster.

## Orchestration & Automation

- Docker Compose: docker-compose.yml for local multi-service orchestration
- Docker Swarm: docker-stack.yml for cloud/cluster deployment
- auto-swarm-join.sh: One-touch Swarm node join
- HEALTHCHECK: Dockerfile health endpoint (/healthz)
- Future: Kubernetes/Helm manifests for cloud-scale orchestration (see k8s/)
- Future: Auto-provisioning and telemetry endpoints
- entrypoint.sh: Entrypoint for auto-provisioning, telemetry, and future hooks
  - ENV OMNITIDE_PROVISION_URL: Auto-register node if set
  - ENV OMNITIDE_TELEMETRY_URL: Enable telemetry hooks if set
  - ENV SWARM_JOIN_TOKEN, SWARM_MANAGER_ADDR: Auto-join Docker Swarm if set
- gcnp-config.yaml: Auto-generated config at startup if missing
- Prints detected mode and config at startup

### Example: One-touch run (Docker)
```
docker run -e OMNITIDE_PROVISION_URL=... -e OMNITIDE_TELEMETRY_URL=... omnimesh/gcnp
```

### Example: One-touch Swarm join
```
docker service create --env SWARM_JOIN_TOKEN=... --env SWARM_MANAGER_ADDR=... omnimesh/gcnp
```

### Example: One-touch K8s (future)
```
kubectl apply -f k8s/go-node-proxy-deployment.yaml
```

To extend: Add cloud, monitoring, and multi-node automation as per OMNITIDE MANIFEST PRIME.

## Monitoring & Telemetry

- /healthz endpoint for Docker/Swarm healthcheck
- Future: /metrics, /telemetry endpoints for Prometheus, Grafana, etc.

To extend: See OMNITIDE MANIFEST PRIME and OMNITIDE_CODEX.md for next-phase automation, UI, and agent integration.

## License
Architect's Will is Absolute.
