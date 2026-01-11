#!/bin/bash
# Script để push code lên GitHub
# Usage: bash push_to_github.sh <github-repo-url>
# Example: bash push_to_github.sh https://github.com/username/gporn-me.git

set -euo pipefail

cd /var/www/gporn.me

if [ $# -eq 0 ]; then
    echo "Usage: $0 <github-repo-url>"
    echo "Example: $0 https://github.com/username/gporn-me.git"
    echo "Or:     $0 git@github.com:username/gporn-me.git"
    exit 1
fi

REPO_URL="$1"

echo "=== Setting up GitHub remote ==="

# Check if remote already exists
if git remote | grep -q origin; then
    echo "Remote 'origin' already exists. Updating..."
    git remote set-url origin "$REPO_URL"
else
    echo "Adding remote 'origin'..."
    git remote add origin "$REPO_URL"
fi

echo "Remote configured:"
git remote -v

echo ""
echo "=== Pushing to GitHub ==="
echo "Branch: master"

# Try to push
if git push -u origin master 2>&1; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "Repository: $REPO_URL"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "1. Repository doesn't exist on GitHub - create it first"
    echo "2. Authentication required - set up SSH keys or use HTTPS with token"
    echo "3. Branch name mismatch - GitHub might use 'main' instead of 'master'"
    echo ""
    echo "If GitHub uses 'main' branch, try:"
    echo "  git branch -m master main"
    echo "  git push -u origin main"
    exit 1
fi
