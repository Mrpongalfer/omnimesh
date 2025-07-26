#!/bin/bash

# build.sh - Nexus Prime Rust Core Build Script
set -e

echo "--- Building Nexus Prime Rust Core ---"
echo "Running cargo build --release..."
cargo build --release
echo "Build complete."

echo "Running cargo test --release..."
cargo test --release
echo "All tests passed."

echo "--- Build and Test Complete ---"
