# Copilot Instructions: Go Compute Node Proxies (GCNP)

## Phase 2 Mandate

- Implement a Go-based proxy agent for each traditional compute node (PC) in the Omnitide Fabric.
- The proxy must:
  - Register with Nexus Prime (Rust Core) via gRPC using the shared `fabric.proto`.
  - Send periodic status and telemetry updates.
  - Subscribe to and process real-time fabric events.
  - Support secure communication (mTLS) in future phases.
  - Be cross-platform (Linux, Windows, macOS).
- All code must be idiomatic Go, with clear error handling and test coverage.
- All proto changes must be reflected in both Rust and Go codegen.
- CI must build, test, and verify codegen on every commit.

## Build & Test
- Use `./generate_proto.sh` to regenerate Go code after proto changes.
- Use `go build` and `go test` for local development.
- See `.github/workflows/go-ci.yml` for CI pipeline.

## Next Steps
- Implement advanced status/telemetry reporting.
- Add Dockerfile for containerized deployment (future).
- Integrate mTLS and config management (future).

**Architect's Will is Absolute.**
