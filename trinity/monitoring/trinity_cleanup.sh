#!/bin/bash
# OMNIMESH Trinity Cleanup Script
# Removes old OMNIMESH bloat, keeps only Trinity Phases 1-4

set -e

echo "🚀 Starting OMNIMESH Trinity Cleanup..."
echo "This will remove old OMNIMESH components and keep only Trinity architecture"
echo ""

# Backup current state
echo "📦 Creating backup..."
tar -czf omnimesh_backup_$(date +%Y%m%d_%H%M%S).tar.gz . --exclude='.git' --exclude='venv'

# Remove old OMNIMESH directories
echo "🗑️ Removing old OMNIMESH directories..."
rm -rf "BACKEND/"
rm -rf "FRONTEND/"
rm -rf "venv/"
rm -rf "__pycache__/"
rm -rf ".git/"
rm -rf "docs/operational-runbooks/"
rm -rf "kubernetes/"
rm -rf "infrastructure/"

# Remove old OMNIMESH files  
echo "🗑️ Removing old OMNIMESH files..."
rm -f "omni"
rm -f "omnimesh"
rm -f "omni-c2-center.py"
rm -f "behavior_patterns.db"
rm -f "drap_knowledge.db"
rm -f "pig_knowledge.db"
rm -f "trinity_startup.log"
rm -f "=23.2.0"

# Clean up Python cache and temporary files
echo "🧹 Cleaning temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete
find . -name "*.tmp" -delete

# Reorganize Trinity structure (optional)
echo "📁 Trinity structure preserved in current organization"

echo ""
echo "✅ Trinity Cleanup Complete!"
echo "📊 Workspace now contains only Trinity Phases 1-4 architecture"
echo "🚀 Ready for clean deployment to GitHub"
