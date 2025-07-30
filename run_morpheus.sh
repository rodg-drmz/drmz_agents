#!/bin/bash
#
# Usage:
#   ./run_morpheus.sh --venv=/abs/path/to/venv --mode crew
# Modes: serve | crew | dapp | cli      (default = serve)
#

# ──────────────────── argument parsing ────────────────────
MODE="serve"
VENV=""

for arg in "$@"; do
  case $arg in
    --venv=*) VENV="${arg#*=}"        ;;
    --mode=*) MODE="${arg#*=}"        ;;
  esac
done

# expand ~ → $HOME
VENV="${VENV/#\~/$HOME}"

if [[ -z "$VENV" ]]; then
  echo "❌  pass your virtual-env with  --venv=/absolute/path"
  exit 1
fi

echo "✅  using virtual-env at $VENV"
source "$VENV/bin/activate"

# ──────────────────── port cleanup ────────────────────────
echo "🧹  stopping old Ray & APIs"
ray stop --force >/dev/null 2>&1

for PORT in 8000 8001 8265; do
  if PID=$(lsof -t -i :"$PORT" -s TCP:LISTEN 2>/dev/null); then
    echo "⛔  killing PID $PID on :$PORT"
    kill -9 "$PID"
  fi
done

# PYTHONPATH
PROJECT_ROOT=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
echo "📂  PYTHONPATH → $PYTHONPATH"

# ──────────────────── launch modes ────────────────────────
if [[ "$MODE" == "serve" ]]; then
  echo "🚀  full DRMZ API on :8000"
  uvicorn src.drmz.api.main:app --host 0.0.0.0 --port 8000 --reload

elif [[ "$MODE" == "crew" ]]; then
  echo "🤖  Crew-mode: Ray Serve (Morpheus) + plain FastAPI (other agents)"
  echo "🌀  starting local Ray head w/ dashboard on :8265 …"
  ray start --head --dashboard-port=8265 --disable-usage-stats

  # 1) Morpheus onboarding flow ─ Ray Serve on :8001  (/morpheus/send)
  echo "🌌  deploying Morpheus Serve app on :8001/morpheus …"
  RAY_SERVE_HTTP_PORT=8001 \
    python -m src.drmz.api.serve_morpheus_chat &

  # 2) YAML-based agents ─ plain FastAPI on :8000  (/chat/stream)
  echo "📚  launching crew_gateway FastAPI on :8000 …"
  uvicorn src.drmz.api.crew_gateway:app --host 0.0.0.0 --port 8000 --reload &

  # Keep foreground alive so Ctrl-C stops both
  wait

elif [[ "$MODE" == "dapp" ]]; then
  echo "💠  DRMZ DApp API on :8000"
  uvicorn src.drmz.api.drmz_dapp_api:app --host 0.0.0.0 --port 8000 --reload

elif [[ "$MODE" == "cli" ]]; then
  echo "🧠  running CLI entrypoint"
  python src/drmz/main.py "${@:2}"

else
  echo "❌  unknown mode: $MODE"
  exit 1
fi
