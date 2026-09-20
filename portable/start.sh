#!/bin/bash
# ============================================================================
# Diligence — Self-hosted fitness rewards platform (Mac/Linux)
#
# This launcher is for systems that already have Python 3.11+ installed.
# It uses the bundled dependencies from lib/ but your system Python.
#
# Usage: ./start.sh
# ============================================================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$APP_DIR/data"

export PYTHONPATH="$APP_DIR/lib:$APP_DIR:$PYTHONPATH"

echo ""
echo "  Diligence"
echo "  ========="
echo ""
echo "  Starting up..."
echo "  Data folder: $DATA_DIR"
echo "  Press Ctrl+C to stop."
echo ""

# Try bundled python first, then system python3
if [ -x "$APP_DIR/python/python3" ]; then
    "$APP_DIR/python/python3" -m diligence --data-dir "$DATA_DIR" "$@"
elif command -v python3 &>/dev/null; then
    python3 -m diligence --data-dir "$DATA_DIR" "$@"
else
    echo "  ERROR: Python 3 not found."
    echo "  Install Python 3.11+ or use the pip install path:"
    echo "    pip install diligence"
    echo "    diligence"
    exit 1
fi
