#!/bin/bash
# Script để tạo package copy sang server khác để chạy Docker
# Usage: bash copy_for_docker.sh

set -euo pipefail

cd /var/www/gporn.me

OUTPUT_DIR="gporn-docker-package"
OUTPUT_TAR="gporn-docker-package.tar.gz"

echo "=== Tạo package để deploy Docker ==="

# Tạo thư mục tạm
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "Copying core files..."
cp app.py requirements.txt Dockerfile .dockerignore "$OUTPUT_DIR/"

echo "Copying templates..."
cp -r templates "$OUTPUT_DIR/"

echo "Copying static files..."
cp -r static "$OUTPUT_DIR/"

# Copy optional utilities
if [ -f "add_movie.py" ]; then
    cp add_movie.py "$OUTPUT_DIR/"
fi

if [ -f "create_admin.py" ]; then
    cp create_admin.py "$OUTPUT_DIR/"
fi

if [ -f "README.md" ]; then
    cp README.md "$OUTPUT_DIR/"
fi

if [ -f "DEPLOY.md" ]; then
    cp DEPLOY.md "$OUTPUT_DIR/"
fi

echo "Creating tarball..."
tar -czf "$OUTPUT_TAR" "$OUTPUT_DIR"

echo ""
echo "=== Package created: $OUTPUT_TAR ==="
echo "Size: $(du -h "$OUTPUT_TAR" | cut -f1)"
echo ""
echo "Files included:"
tar -tzf "$OUTPUT_TAR" | head -20
echo "..."
echo ""
echo "=== Next steps ==="
echo "1. Copy $OUTPUT_TAR to new server:"
echo "   scp $OUTPUT_TAR user@new-server:/path/to/destination/"
echo ""
echo "2. On new server, extract and build:"
echo "   tar -xzf $OUTPUT_TAR"
echo "   cd $OUTPUT_DIR"
echo "   docker build -t gporn-me:latest ."
echo "   docker run -d -p 5001:5001 -v \$(pwd)/instance:/app/instance gporn-me:latest"
echo ""
echo "3. Clean up:"
echo "   rm -rf $OUTPUT_DIR"
