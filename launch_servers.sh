#!/usr/bin/env bash
# set -e  # ← disable for debugging

echo "🧪 Launch script starting..."

# DRMZ DApp API (port 8000)
echo "🚀 Starting DRMZ DApp API on port 8000..."
uvicorn src.drmz.api.drmz_dapp_api:app --port 8000 --reload &

# Crew Gateway API (port 8001)
echo "🤖 Starting Crew Gateway API on port 8001..."
uvicorn src.drmz.api.crew_gateway:app --port 8001 --reload &

# Show background PIDs
echo "🧭 Servers launched in background. Use Ctrl+C to exit."
wait
