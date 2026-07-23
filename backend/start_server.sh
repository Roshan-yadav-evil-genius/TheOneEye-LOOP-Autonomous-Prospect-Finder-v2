#!/bin/bash
# Navigate to the backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Locate python executable in virtualenv directly (bypasses broken/relocated shebangs)
if [ -f "$SCRIPT_DIR/../venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/../venv/bin/python3"
elif [ -f "$SCRIPT_DIR/../venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/../venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
elif [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

export PYTHONPATH=src

echo "🚀 Starting FastAPI server on port 7878 using $PYTHON_BIN..."
exec "$PYTHON_BIN" -m uvicorn main:app --reload --port 7878
