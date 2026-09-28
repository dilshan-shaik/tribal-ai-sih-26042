#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PORT="${1:-8100}"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

if [ ! -f .venv/.deps-ok ]; then
  pip install -q --disable-pip-version-check fastapi "uvicorn[standard]" gtts python-multipart
  touch .venv/.deps-ok
fi

if [ ! -f web/dist/index.html ]; then
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    echo "building front-end..."
    if [ ! -d web/node_modules ]; then
      (cd web && npm install --no-audit --no-fund)
    fi
    (cd web && npm run build)
  else
    echo "warning: web/dist is missing and node/npm was not found"
    echo "install Node.js 18+ then run:  cd web && npm install && npm run build"
  fi
fi

if [ -f web/dist/index.html ]; then
  echo "front-end: web/dist (built)"
else
  echo "front-end: not built - the API works, the page will not"
fi

echo "http://localhost:$PORT"
python -m uvicorn server.main:app --host 0.0.0.0 --port "$PORT"
