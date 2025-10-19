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