# RUN — PALASH MTB-MLE

Needs: Python 3.10+ and a browser. No Node.js, no database, no API keys.

## Windows

```
cd C:\mtb-mle
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" gtts python-multipart pypdf
python -m uvicorn server.main:app --host 0.0.0.0 --port 8100
```

## macOS / Linux

cd ~/mtb-mle
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" gtts python-multipart pypdf
python -m uvicorn server.main:app --host 0.0.0.0 --port 8100
```

## Open

```
http://localhost:8100
```

## Stop

```
Ctrl + C
```

## Run again next time

Windows

```
cd C:\mtb-mle
.\.venv\Scripts\Activate.ps1
python -m uvicorn server.main:app --host 0.0.0.0 --port 8100
```

macOS / Linux

```
cd ~/mtb-mle
source .venv/bin/activate
python -m uvicorn server.main:app --host 0.0.0.0 --port 8100
```

## One command (installs and builds whatever is missing)

```
./preview.sh
```

## One-click instead

Windows: double-click `run.bat`

macOS / Linux:

```
chmod +x run.sh
./run.sh
```

## Voice input (optional)

```
pip install faster-whisper python-multipart
```

Restart the server after installing.

## Other port

```
python -m uvicorn server.main:app --host 0.0.0.0 --port 8080
```

## Phone or tablet on the same Wi-Fi

```
ipconfig
```

```
ifconfig
```

```
http://YOUR-LAPTOP-IP:8000
```

## Checks

```
http://localhost:8100/api/health
http://localhost:8100/api/asr/status
http://localhost:8100/api/version
http://localhost:8100/docs
```

## Extra commands

```
python pipelines/prewarm_audio.py
python pipelines/prewarm_audio.py --limit 100
python pipelines/build_language_pack.py
python pipelines/build_dictionary.py
python pipelines/prewarm_audio.py --limit 100
python pipelines/translit.py
```

```
cd web
npm install
npm run build
```

## Errors

```
ModuleNotFoundError: No module named 'server'
```

```
cd C:\mtb-mle
```

```
Address already in use
```

```
python -m uvicorn server.main:app --host 0.0.0.0 --port 8080
```

```
Error loading ASGI app. Could not import module "multipart"
```

```
pip install python-multipart
```

```
Blank page
```

```
Ctrl + Shift + R
```

```
Record button missing
```

```
pip install faster-whisper
```

```
Microphone not working
```

```
http://localhost:8100        (not a 192.168.x.x address)
Chrome or Edge
Use the tap-to-speak board
```
