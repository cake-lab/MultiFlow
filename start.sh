#!/usr/bin/env bash
# Start script for MultiFlow (Linux/macOS)
# Usage: ./start.sh       # build client if needed, start server, open browser
#        ./start.sh -r    # force rebuild

set -euo pipefail

REBUILD=0
while getopts "r" opt; do
  case $opt in
    r) REBUILD=1 ;;
    *) ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VITE_DIR="$ROOT_DIR/client/vite"
WEB_INDEX="$ROOT_DIR/client/web/index.html"

function info { echo "[INFO] $*"; }
function err { echo "[ERROR] $*" >&2; }

if [ $REBUILD -eq 1 ] || [ ! -f "$WEB_INDEX" ]; then
  info "Building frontend (client/vite)..."
  if ! command -v npm >/dev/null 2>&1; then
    err "npm not found. Install Node.js and npm to build the frontend."
    exit 1
  fi

  if [ ! -d "$VITE_DIR/node_modules" ]; then
    # Prefer a clean, reproducible install when lockfile exists
    if [ -f "$VITE_DIR/package-lock.json" ] || [ -f "$VITE_DIR/npm-shrinkwrap.json" ]; then
      info "node_modules not found in client/vite. Lockfile detected - running 'npm ci'..."
      (cd "$VITE_DIR" && npm ci)
    else
      info "node_modules not found in client/vite. Running 'npm install'..."
      (cd "$VITE_DIR" && npm install)
    fi
  fi

  (cd "$VITE_DIR" && npm run build)
  info "Frontend build finished."
else
  info "Frontend already built (client/web/index.html exists). Use -r to force a rebuild."
fi

SERVER_PY="$ROOT_DIR/server/server.py"
if [ ! -f "$SERVER_PY" ]; then
  err "Server file not found: $SERVER_PY"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  err "python not found. Install Python to run the server."
  exit 1
fi

info "Starting Python server (server/server.py) in background..."
pushd "$ROOT_DIR/server" >/dev/null
nohup python "server.py" > "$ROOT_DIR/server/server.log" 2>&1 &
popd >/dev/null
sleep 1
info "Starting client (client/client.py) in background..."
CLIENT_PY="$ROOT_DIR/client/client.py"
if [ -f "$CLIENT_PY" ]; then
  pushd "$ROOT_DIR/client" >/dev/null
  nohup python "client.py" > "$ROOT_DIR/client/client.log" 2>&1 &
  popd >/dev/null
  info "Started client in background. Logs: client/client.log"
else
  info "Client script not found ($CLIENT_PY). Started server only."
fi

info "Started Python server in background. Logs are in server.log"


