#!/bin/bash
# Script để chạy ứng dụng Flask ở chế độ development
# Usage: bash run_dev.sh

set -euo pipefail

cd "$(dirname "$0")"

echo "=== Starting Flask app in development mode ==="

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
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Kiểm tra database
if [ ! -d "instance" ]; then
    echo "Creating instance directory..."
    mkdir -p instance
fi

# Set environment variables (optional)
export FLASK_APP=app.py
export FLASK_ENV=development

echo ""
echo "=== Starting Flask development server ==="
echo "App will be available at: http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

# Chạy Flask app
python app.py
