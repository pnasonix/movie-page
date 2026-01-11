#!/bin/bash
# Script để push lên GitHub với Personal Access Token
# Usage: bash push_with_token.sh
# Hoặc: GITHUB_TOKEN=your_token bash push_with_token.sh

set -euo pipefail

cd /var/www/gporn.me

echo "=== Push to GitHub with Personal Access Token ==="
echo ""

# Kiểm tra token
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "⚠️  GITHUB_TOKEN not set in environment"
    echo ""
    echo "Cách 1: Set token trước khi chạy script:"
    echo "  export GITHUB_TOKEN=your_personal_access_token"
    echo "  bash push_with_token.sh"
    echo ""
    echo "Cách 2: Nhập token khi chạy:"
    echo "  GITHUB_TOKEN=your_token bash push_with_token.sh"
    echo ""
    echo "Cách 3: Push thủ công:"
    echo "  git remote set-url origin https://\${GITHUB_TOKEN}@github.com/pnasonix/movie-page.git"
    echo "  git push -u origin main"
    echo ""
    read -sp "Nhập GitHub Personal Access Token (hoặc Enter để bỏ qua): " token
    echo ""
    if [ -z "$token" ]; then
        echo "❌ Token required. Exiting."
        exit 1
    fi
    GITHUB_TOKEN="$token"
fi

# Set remote URL với token
echo "Setting remote URL with token..."
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/pnasonix/movie-page.git"

# Push
echo "Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "Repository: https://github.com/pnasonix/movie-page"
    echo ""
    # Remove token from remote URL for security
    git remote set-url origin https://github.com/pnasonix/movie-page.git
    echo "✓ Remote URL reset (token removed for security)"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "1. Token has 'repo' permissions"
    echo "2. Repository exists and you have access"
    echo "3. Branch name is correct (main)"
    exit 1
fi
