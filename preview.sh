#!/usr/bin/env bash
# One command to get the preview up on a fresh machine or a fresh session.
# Installs what is missing, rebuilds the front end if it is gone, then serves on 8100.
set -e
cd "$(dirname "$0")"

python3 -c "import fastapi, uvicorn, gtts, multipart, pypdf" 2>/dev/null || {
  echo "[1/3] installing python packages..."
  python3 -m pip install --quiet --disable-pip-version-check \
    fastapi "uvicorn[standard]" gtts python-multipart pypdf
}

if [ ! -f web/dist/index.html ]; then
  echo "[2/3] building the front end..."
  cd web
  [ -d node_modules ] || npm install --silent
  npm run build
  cd ..
fi

echo "[3/3] serving on http://localhost:8100"
exec python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8100
