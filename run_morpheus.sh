#!/bin/bash

# ─── Usage ─────────────────────────────────────────────────────────────────────
# ./run_morpheus.sh --venv /path/to/venv --mode serve
# Modes: serve, crew, dapp, cli
# Default mode: serve

# ─── Input Parsing ────────────────────────────────────────────────────────────
MODE="serve"
VENV=""

for arg in "$@"; do
  case $arg in
    --venv=*)
      VENV="${arg#*=}"
      ;;
    --mode=*)
      MODE="${arg#*=}"
      ;;
    *)
      ;;
  esac
done

# Manually expand ~ to $HOME
VENV="${VENV/#\~/$HOME}"

if [[ -z "$VENV" ]]; then
  echo "❌ Please provide your virtualenv path with --venv=/path/to/venv"
  exit 1
fi

echo "✅ Using virtualenv at: $VENV"
source "$VENV/bin/activate"

# ─── Port Cleanup ──────────────────────────────────────────────────────────────
echo "🧹 Cleaning up old Ray and API ports…"
ray stop --force > /dev/null 2>&1

for PORT in 8000 8001 8265; do
  PID=$(lsof -t -i:$PORT -sTCP:LISTEN 2>/dev/null)
  if [[ -n "$PID" ]]; then
    echo "⛔ Killing process on port $PORT (PID: $PID)"
    kill -9 $PID
  fi
done

# ─── PYTHONPATH Setup ─────────────────────────────────────────────────────────
PROJECT_ROOT=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
echo "📂 PYTHONPATH set to: $PYTHONPATH"

# ─── Launch Mode Dispatcher ───────────────────────────────────────────────────
if [[ "$MODE" == "serve" ]]; then
  echo "🚀 Launching full Morpheus API on http://localhost:8000"
  uvicorn src.drmz.api.main:app --host 0.0.0.0 --port 8000 --reload

elif [[ "$MODE" == "crew" ]]; then
  echo "🤖 Launching Crew Gateway API on http://localhost:8001"
  echo "🌀 Starting Ray Serve deployment on port 8001..."

  # ✅ Start Ray with dashboard only
  ray start --head --dashboard-port=8265 --disable-usage-stats

  # ✅ Set HTTP port override for Ray Serve
  RAY_SERVE_HTTP_PORT=8001 python -m src.drmz.api.serve_gateway

elif [[ "$MODE" == "dapp" ]]; then
  echo "💠 Launching DRMZ DApp API on http://localhost:8000"
  uvicorn src.drmz.api.drmz_dapp_api:app --host 0.0.0.0 --port 8000 --reload

elif [[ "$MODE" == "cli" ]]; then
  echo "🧠 Running CLI mode with drmz/main.py"
  python src/drmz/main.py "$@"

else
  echo "❌ Unknown mode: $MODE"
  exit 1
fi
