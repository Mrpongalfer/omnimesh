#!/bin/sh
set -e

# Omnitide GCNP Entrypoint: One-touch autodetect, autoconfig, autodeploy

# --- 1. Detect Orchestration Environment ---
MODE="standalone"
if [ -f /var/run/secrets/kubernetes.io/serviceaccount/token ] || [ "$KUBERNETES_SERVICE_HOST" ]; then
  MODE="kubernetes"
elif [ -S /var/run/docker.sock ]; then
  # Docker socket present, check for Swarm
  if docker info 2>/dev/null | grep -q 'Swarm: active'; then
    MODE="swarm"
  else
    MODE="docker"
  fi
fi

echo "[Entrypoint] Detected mode: $MODE"

# --- 2. Auto-generate config if missing ---
CONFIG_FILE="/app/gcnp-config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "[Entrypoint] No config found, generating default config..."
  cat <<EOF > "$CONFIG_FILE"
mode: $MODE
node_id: $(hostname)
controller_url: ${OMNITIDE_PROVISION_URL}
telemetry_url: ${OMNITIDE_TELEMETRY_URL}
EOF
fi

# --- 3. Auto-register with controller if URL is set ---
if [ -n "$OMNITIDE_PROVISION_URL" ]; then
  echo "[Entrypoint] Auto-registering node with $OMNITIDE_PROVISION_URL ..."
  # Placeholder: curl -X POST "$OMNITIDE_PROVISION_URL/register" -d "node_id=$(hostname)&mode=$MODE"
  # Future: Add secure registration logic here
fi

# --- 4. Auto-join Swarm/K8s if tokens/endpoints are present ---
if [ "$MODE" = "swarm" ] && [ -n "$SWARM_JOIN_TOKEN" ] && [ -n "$SWARM_MANAGER_ADDR" ]; then
  echo "[Entrypoint] Auto-joining Docker Swarm..."
  docker swarm join --token "$SWARM_JOIN_TOKEN" "$SWARM_MANAGER_ADDR" || true
fi
if [ "$MODE" = "kubernetes" ]; then
  echo "[Entrypoint] Running in Kubernetes, using service DNS for discovery."
  # Future: Add K8s-specific config/discovery here
fi

# --- 5. Telemetry/Monitoring ---
if [ -n "$OMNITIDE_TELEMETRY_URL" ]; then
  echo "[Entrypoint] Telemetry endpoint: $OMNITIDE_TELEMETRY_URL"
  # Placeholder: ./telemetry_exporter.sh &
fi

# --- 6. Print config and start service ---
echo "[Entrypoint] Final config:"
cat "$CONFIG_FILE"
echo "[Entrypoint] Starting Go Compute Node Proxy..."
exec ./gcnp "$@"
