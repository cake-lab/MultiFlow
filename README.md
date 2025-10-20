MultiFlow
=========

This project explores compressing and streaming camera frames to a local Flask server using ffmpeg + DASH. It includes a small React frontend (Vite) to view live streams and per-camera recordings.

Quick manual run (what the scripts do)
------------------------------------

Run the Python client:

```
cd client
python client.py
```

Build the frontend and start the server:

```
cd client/vite
npm install
npm run build

cd ../..
cd server
python server.py
```

Start scripts (recommended)
--------------------------

Two convenience scripts are provided to build what's needed and start the project:

- `start.ps1` — Windows PowerShell
- `start.sh` — Linux / macOS (bash)

What they do:
- Build the frontend (runs `npm install` and `npm run build` in `client/vite`) if the build output doesn't exist or if you force a rebuild.
- Start the Python server (`server/server.py`) and the camera client (`client/client.py`).
- They do NOT open a browser for you; they leave servers running so you can inspect logs and control processes.

Examples
--------

Windows (PowerShell):

```powershell
# build if needed and start server+client
.\start.ps1

# force a frontend rebuild and start everything
.\start.ps1 -Rebuild
```

Linux / macOS (bash):

```bash
# build if needed and start server+client
./start.sh

# force a frontend rebuild and start everything
./start.sh -r
```

Notes & prerequisites
---------------------
- Requires Node.js (npm) and Python available on PATH.
- The scripts start the Python server and client such that generated `chunks/` and `recordings/` folders are created under the `server/` folder (so artifacts stay with the server files).
- If you prefer to run pieces manually, the "Quick manual run" instructions above show the equivalent commands.

CLI options
-----------
Both the server and client Python scripts accept command-line options to control host/port and server URL.

Server (`server/server.py`)
- --host: Host/IP to bind the Flask server to (default: 0.0.0.0)
- --port: Port to listen on (default: 5000)

Examples (PowerShell):

```powershell
# run server on default 0.0.0.0:5000
python server/server.py

# run server on localhost port 8080
python server/server.py --host 127.0.0.1 --port 8080

# run server with debug enabled
python server/server.py --debug
```

Client (`client/client.py`)
- --host: Server host used to construct the upload endpoint (default: 127.0.0.1)
- --port: Server port used to construct the upload endpoint (default: 5000)
- --server-url: Full upload URL (overrides --host/--port), e.g. http://example.com:5000/upload

Examples (PowerShell):

```powershell
# run client with default server URL (http://127.0.0.1:5000/upload)
python client/client.py

# point client at a server on 192.168.1.10:5000
python client/client.py --host 192.168.1.10 --port 5000

# use a full server URL
python client/client.py --server-url http://example.com:5000/upload
```

Notes:
- If `--server-url` is supplied it takes precedence over `--host`/`--port`.
- These options are designed to be backward compatible with existing behavior.