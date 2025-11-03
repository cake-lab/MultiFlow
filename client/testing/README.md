# testclient

This is a small test client that streams local MP4 files as virtual camera sources and uploads H.264 stream data to the MultiFlow server upload endpoint.

Location
- `client/testing/testclient.py`

Purpose
- Replace physical cameras with MP4 files for local testing and development.
- Useful for replaying recorded video as camera inputs and exercising the server upload/ingest logic.

Prerequisites
- Python 3.8+ (or a reasonably recent Python 3)
- ffmpeg available on PATH (used to decode and re-encode input files to raw H.264)
- Python dependency: `requests` (install with `pip install requests`)

Test files layout
- Place MP4 files under `client/testing/tests/<testname>/`.
  - Example: `client/testing/tests/kitppad-basic/stream1.mp4`
- Each subdirectory under `tests/` that contains `.mp4` files becomes a test set.

How it works (brief)
- For each MP4 file in the chosen test set, `testclient.py` starts an `ffmpeg` process that outputs H.264 to stdout.
- A background thread reads chunks from ffmpeg's stdout and POSTs them to the server upload URL as `application/octet-stream` with a `Camera-ID` header.
- When a camera stops, the client issues an HTTP DELETE to the same upload URL with the `Camera-ID` header to notify the server.

Running

From the `client/testing` directory:

```powershell
cd client/testing
python testclient.py --host 127.0.0.1 --port 5000
```

Or give a full server URL:

```powershell
python testclient.py --server-url http://127.0.0.1:5000/upload
```

Tip: the repository contains a simple server at `server/server.py` which you can run locally to receive uploads during testing.

Interactive commands
- l [setname]  — list test sets (or list files in a set when a name is given)
- s <setname>  — start all cameras in the named test set
- t <setname>  — stop all cameras in the named test set
- q            — quit (stops running cameras and exits)

Example session
1. Create a test set directory and add MP4s:

```powershell
mkdir -p client/testing/tests/local1
# copy or download some .mp4 files into client/testing/tests/local1
```

2. Start the test client and list sets:

```powershell
python client/testing/testclient.py
> l
```

3. Start streaming the set named `local1`:

```text
> s local1
```

4. Stop it:

```text
> t local1
```

Notes and caveats
- `ffmpeg` must be in your PATH. On Windows, add the ffmpeg binary directory to your system PATH.
- The client expects `.mp4` files (case-insensitive suffix match). Other file types are ignored.
- The script sends small POSTs with raw H.264 byte chunks; ensure the receiver can handle this framing and `Camera-ID` header.
- Timeouts on network requests are short (to avoid blocking on a slow server) and exceptions during POST are ignored so streams continue.

Contact
- If you need changes (different encoding, larger chunking, authentication), edit `client/testing/testclient.py` or open an issue in the repo.
