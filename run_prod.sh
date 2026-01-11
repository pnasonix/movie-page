#!/bin/bash
# Script để chạy ứng dụng Flask ở chế độ production với Gunicorn
# Usage: bash run_prod.sh

set -euo pipefail

cd "$(dirname "$0")"

echo "=== Starting Flask app in production mode ==="

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Kiểm tra dependencies
if ! python -c "import gunicorn" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Kiểm tra database
if [ ! -d "instance" ]; then
    echo "Creating instance directory..."
    mkdir -p instance
fi

# Set environment variables
export FLASK_APP=app.py

# Workers và port có thể override bằng environment variables
WORKERS=${WORKERS:-4}
PORT=${PORT:-5001}
BIND=${BIND:-0.0.0.0:${PORT}}

echo ""
echo "=== Starting Gunicorn production server ==="
echo "Workers: $WORKERS"
echo "Bind: $BIND"
echo "App will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

# Chạy với Gunicorn
gunicorn --workers "$WORKERS" \
         --bind "$BIND" \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         app:app
