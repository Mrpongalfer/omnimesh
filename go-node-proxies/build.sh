#!/bin/bash
# build.sh - Build script for Go Compute Node Proxy (GCNP)
set -e

echo "--- Building Go Compute Node Proxy (GCNP) ---"
go mod tidy
go build -o gcnp main.go
echo "Build complete. Binary: ./gcnp"

# Docker build convenience
if command -v docker &> /dev/null; then
  echo "--- Optionally building Docker image for GCNP ---"
  docker build -t omnimesh/gcnp .
else
  echo "Docker not found, skipping Docker image build."
fi
