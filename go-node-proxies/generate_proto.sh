#!/bin/bash
# generate_proto.sh - Generate Go gRPC code from proto/fabric.proto
set -e

PROTO_DIR="$(dirname "$0")/proto"
OUT_DIR="$(dirname "$0")/fabricpb"
PROTO_PATHS="-I$PROTO_DIR -I$(dirname "$0")/third_party"

mkdir -p "$OUT_DIR"

# Add Go bin to PATH for protoc plugins
export PATH="$PATH:$(go env GOPATH)/bin"

# Generate Go code with proto3 optional support
protoc $PROTO_PATHS --experimental_allow_proto3_optional --go_out="$OUT_DIR" --go-grpc_out="$OUT_DIR" "$PROTO_DIR/fabric.proto"

echo "Go gRPC code generated in $OUT_DIR."
