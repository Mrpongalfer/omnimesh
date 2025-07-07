# Dockerfile for Go Compute Node Proxy (GCNP)
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN ./generate_proto.sh
RUN go build -o gcnp main.go

FROM alpine:3.19
WORKDIR /app
# Add non-root user for security (optional, recommended)
RUN adduser -D -u 10001 omnimesh
COPY --from=builder /app/gcnp ./gcnp
COPY --from=builder /app/copilot-instructions-go-node-proxies.md ./
COPY --from=builder /app/README.md ./
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
# Expose healthcheck and telemetry endpoints
EXPOSE 8080 9090
# Healthcheck for orchestration self-healing (expects /healthz endpoint)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget --no-verbose --tries=1 --spider http://localhost:8080/healthz || exit 1
# Use non-root user
USER omnimesh
# Entrypoint for full automation, auto-provisioning, and future hooks
ENTRYPOINT ["./entrypoint.sh"]
# Environment variables for automation (documented)
ENV OMNITIDE_PROVISION_URL="" \
    OMNITIDE_TELEMETRY_URL=""
# Future: Add CMD/ENV for cloud, monitoring, etc.
