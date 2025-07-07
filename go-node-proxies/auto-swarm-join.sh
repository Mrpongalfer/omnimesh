#!/bin/bash
# auto-swarm-join.sh - One-touch Docker Swarm node join script
# Usage: Run on a new node with the manager's IP as argument

MANAGER_IP=${1:-""}
if [ -z "$MANAGER_IP" ]; then
  echo "Usage: $0 <manager-ip>"
  exit 1
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
  echo "Docker not found. Installing..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
fi

# Join the Swarm
JOIN_CMD=$(ssh $MANAGER_IP "docker swarm join-token worker -q")
if [ -z "$JOIN_CMD" ]; then
  echo "Failed to get join token from manager."
  exit 1
fi
MANAGER_ADDR="$MANAGER_IP:2377"
sudo docker swarm join --token $JOIN_CMD $MANAGER_ADDR
