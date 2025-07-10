#!/bin/bash

# 🚀 OMNIMESH Auto-Push Script
# Automated git operations for the OMNIMESH ecosystem

set -euo pipefail

echo "🌊 OMNIMESH Auto-Push Utility"
echo "📂 Working directory: $(pwd)"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for changes
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to commit"
    exit 0
fi

# Stage all changes
echo "📝 Staging changes..."
git add .

# Commit with timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
commit_msg="🌊 OMNIMESH Auto-update: ${timestamp}"

echo "💾 Committing changes: ${commit_msg}"
git commit -m "${commit_msg}"

# Push if remote exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "🚀 Pushing to remote..."
    git push origin $(git branch --show-current)
    echo "✅ Push completed successfully"
else
    echo "⚠️  No remote configured - changes committed locally only"
fi

echo "🎉 Auto-push operation completed!"
