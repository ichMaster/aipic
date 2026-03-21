#!/bin/bash
# Start Aipic editor
#
# Usage:
#   ./aipic.sh [filename]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/main.py" "$@"
