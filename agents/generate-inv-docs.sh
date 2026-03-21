#!/bin/bash
# Generate inventory documentation using Claude Code skill /generate-inv-docs
#
# Usage:
#   ./agents/generate-inv-docs.sh <path-to-inv-file>
#
# Example:
#   ./agents/generate-inv-docs.sh data/db_inventory_task.inv

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-inv-file>"
    echo ""
    echo "Available .inv files:"
    find "$PROJECT_DIR" -name "*.inv" -maxdepth 2 | sed "s|$PROJECT_DIR/||"
    exit 1
fi

INV_FILE="$1"

# Resolve relative path from project root
if [[ ! "$INV_FILE" = /* ]]; then
    INV_FILE="$PROJECT_DIR/$INV_FILE"
fi

if [ ! -f "$INV_FILE" ]; then
    echo "Error: File not found: $INV_FILE"
    exit 1
fi

echo "Generating documentation for: $INV_FILE"

cd "$PROJECT_DIR"
claude -p "/generate-inv-docs — use file $INV_FILE, process all records, yes to all prompts" \
    --allowedTools "Read,Write,Bash,Glob,Grep,TodoWrite"
