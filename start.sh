#!/usr/bin/env bash
# Startup script for GATE CSE Screenshot Organizer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==========================================================="
echo "   🚀 Launching GATE CSE Screenshot Organizer..."
echo "==========================================================="

PORT=8000
# Check if port 8000 is occupied, pick another if needed
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PORT=8080
fi

echo "Serving web app at: http://localhost:$PORT"
echo "Screenshots storage: ~/gate_cse_notes"
echo "Press Ctrl+C to stop the server."
echo "==========================================================="

# Try to launch default browser in background if display is available
if [ -n "$DISPLAY" ]; then
    (sleep 1 && xdg-open "http://localhost:$PORT" >/dev/null 2>&1 || sensible-browser "http://localhost:$PORT" >/dev/null 2>&1) &
fi

python3 -m uvicorn app:app --host 0.0.0.0 --port $PORT
