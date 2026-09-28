@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set PORT=8100) else (set PORT=%~1)

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat

if not exist .venv\.deps-ok (
  pip install -q --disable-pip-version-check fastapi "uvicorn[standard]" gtts python-multipart
  type nul > .venv\.deps-ok
)

if not exist web\dist\index.html (
  where node >nul 2>nul
  if errorlevel 1 (
    echo warning: web\dist is missing and node/npm was not found
    echo install Node.js 18+ then run:  cd web ^&^& npm install ^&^& npm run build
  ) else (
    echo building front-end...
    if not exist web\node_modules (
      pushd web
      call npm install --no-audit --no-fund
      popd
    )
    pushd web
    call npm run build
    popd
  )
)

if exist web\dist\index.html (
  echo front-end: web\dist (built)
) else (
  echo front-end: not built - the API works, the page will not
)

echo http://localhost:%PORT%
python -m uvicorn server.main:app --host 0.0.0.0 --port %PORT%
endlocal
