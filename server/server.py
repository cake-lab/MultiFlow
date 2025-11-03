from flask import Flask, request, send_from_directory, render_template
import subprocess
import threading
import cv2
import numpy as np
import queue
import os
import argparse
import signal
import sys
import time
import logging

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../client/web"))
app = Flask(__name__, template_folder=template_dir)

camera_streams = {}
telemetry_data_amounts = {}
telemetry_data_locks = {}

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

SERVER_ROOT = os.path.abspath(os.path.dirname(__file__))


def writer_thread(ffmpeg, frame_queue):
    """Continuously feed encoded chunks into ffmpeg stdin."""
    while True:
        try:
            chunk = frame_queue.get(timeout=1)
            if chunk is None:
                ffmpeg.stdin.close()
                break
            ffmpeg.stdin.write(chunk)
        except queue.Empty:
            continue
        except BrokenPipeError as e:
            print("FFmpeg process ended:", e)
            break

def start_decoder(camera_id):
    """Start a new ffmpeg decoder process and threads for a camera."""
    # Ensure chunks/ and recordings/ are created under the server package directory
    chunks_dir = os.path.join(SERVER_ROOT, "chunks", camera_id)
    os.makedirs(chunks_dir, exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg",
        # Ensure ffmpeg generates proper PTS when reading from a pipe
        "-fflags", "+genpts",
        # Use wallclock timestamps to keep segment timing consistent for live
        "-use_wallclock_as_timestamps", "1",
        "-i", "pipe:0",
        # Low-latency encoding settings
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        # Force a frame rate to stabilize segment durations (matching your source fps)
        "-r", "30",
        "-c:a", "aac",
        "-f", "dash",
        "-use_template", "1",
        "-use_timeline", "1",
        os.path.join(chunks_dir, "manifest.mpd")
    ]
    ffmpeg = subprocess.Popen(
        ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=chunks_dir
    )
    q = queue.Queue()
    camera_streams[camera_id] = q
    telemetry_data_amounts[camera_id] = 0
    telemetry_data_locks[camera_id] = threading.Lock()
    threading.Thread(target=writer_thread, args=(ffmpeg, q), daemon=True).start()

def aggregate_telemetry():
    while True:
        time.sleep(1)
        total_traffic = 0
        for cam_id in list(telemetry_data_amounts.keys()):
            with telemetry_data_locks[cam_id]:
                amount = telemetry_data_amounts[cam_id]
                telemetry_data_amounts[cam_id] = 0
            total_traffic += amount
        print(f"[Telemetry] {time.strftime('%Y-%m-%d %H:%M:%S')} - Total incoming data: {total_traffic / 1024:.2f} KB/s")

@app.route("/upload", methods=["POST", "DELETE"])
def upload():
    cam_id = request.headers.get("Camera-ID", "0")
    if request.method == "DELETE":
        if cam_id in camera_streams:
            camera_streams[cam_id].put(None)
            del camera_streams[cam_id]
            del telemetry_data_amounts[cam_id]
            del telemetry_data_locks[cam_id]
            return f"Closed camera {cam_id}", 200
        else:
            return f"Camera {cam_id} not found", 404 
    else:
        chunk = request.data
        if not chunk:
            return "No data", 400

        # Start a decoder thread per new camera
        if cam_id not in camera_streams:
            start_decoder(cam_id)
        camera_streams[cam_id].put(chunk)
        with telemetry_data_locks[cam_id]:
            telemetry_data_amounts[cam_id] += len(chunk)
        return "OK", 200
@app.route("/")
def live_frontend():
    return render_template("index.html")
@app.route("/<path:filename>")
def base_files(filename):
    return send_from_directory(f"../client/web", filename)
@app.route("/assets/<path:filename>")
def assets_files(filename):
    return send_from_directory(f"../client/web/assets", filename)
@app.route("/info")
def num_cameras():
    return {
        "num_cameras": len(camera_streams),
        "cameras": list(camera_streams.keys())
        }
@app.route("/dash/<camera_id>/<path:filename>")
def dash_files(camera_id, filename):
    # Serve chunk files from the server's chunks directory
    return send_from_directory(os.path.join(SERVER_ROOT, "chunks", camera_id), filename)
def reset_chunks_dir(base_dir="./chunks"):
    # Normalize base_dir to be inside the server package unless an absolute path was provided
    if not os.path.isabs(base_dir):
        base_dir = os.path.join(SERVER_ROOT, base_dir)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        return
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            # recursively remove subfolders using only os
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(path)

def stop_all_streams():
    for cam_id in list(camera_streams.keys()):
        try:
            camera_streams[cam_id].put(None)
        except Exception:
            pass

def menu_loop():
    """Interactive single-char menu:
    l - list cameras
    t - stop all streams
    q - quit (stop all and exit)
    """
    print("Server interactive menu: l=list, t=stop all, q=quit")
    while True:
        try:
            c = sys.stdin.read(1)
        except Exception:
            c = 'q'
        if not c:
            time.sleep(0.1)
            continue
        c = c.strip().lower()
        if not c:
            continue
        if c == 'l':
            print(f"Open camera streams: {list(camera_streams.keys())}")
        elif c == 't':
            print("Stopping all streams...")
            stop_all_streams()
        elif c == 'q':
            print("Quitting: stopping all streams and exiting")
            stop_all_streams()
            # Attempt to gracefully stop Flask by sending SIGINT to this process
            try:
                os.kill(os.getpid(), signal.SIGINT)
            except Exception:
                pass
            break
        else:
            print('Unknown command, use l/t/q')
def main(argv=None):
    parser = argparse.ArgumentParser(description='MultiFlow server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable Flask debug mode')
    args = parser.parse_args(argv)

    reset_chunks_dir()
    threading.Thread(target=menu_loop, daemon=True).start()
    threading.Thread(target=aggregate_telemetry, daemon=True).start()
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()

