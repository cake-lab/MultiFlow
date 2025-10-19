from flask import Flask, request, send_from_directory, render_template
import subprocess
import threading
import cv2
import numpy as np
import queue
import os
import signal
import sys
import time

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../client/web"))
app = Flask(__name__, template_folder=template_dir)

camera_streams = {}
download_streams = {}


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
    out_dir = f"./chunks/{camera_id}"
    os.makedirs(out_dir, exist_ok=True)
    out_dir = f"./recordings"
    os.makedirs(out_dir, exist_ok=True)
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
        "-seg_duration", "2",
        "-frag_duration", "1",
        "-window_size", "6",
        "-extra_window_size", "2",
        "-remove_at_exit", "1",
        f"./chunks/{camera_id}/manifest.mpd"
    ]
    ffmpeg = subprocess.Popen(
        ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    ffmpeg_download_cmd = [
        "ffmpeg",
        "-y",
        "-f", "h264",
        "-i", "pipe:0",
        "-preset", "ultrafast",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-f", "mp4",
        f"./recordings/{camera_id}.mp4"
    ]
    ffmpeg_download = subprocess.Popen(
        ffmpeg_download_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    q = queue.Queue()
    q_download = queue.Queue()
    camera_streams[camera_id] = q
    download_streams[camera_id] = q_download
    threading.Thread(target=writer_thread, args=(ffmpeg, q), daemon=True).start()
    threading.Thread(target=writer_thread, args=(ffmpeg_download, q_download), daemon=True).start()

@app.route("/upload", methods=["POST", "DELETE"])
def upload():
    cam_id = request.headers.get("Camera-ID", "0")
    if request.method == "DELETE":
        if cam_id in camera_streams:
            camera_streams[cam_id].put(None)
            download_streams[cam_id].put(None)
            del camera_streams[cam_id]
            del download_streams[cam_id]
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
        download_streams[cam_id].put(chunk)
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
    return send_from_directory(f"./chunks/{camera_id}", filename)
def reset_chunks_dir(base_dir="./chunks"):
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
        try:
            download_streams[cam_id].put(None)
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
if __name__ == "__main__":
    import os
    reset_chunks_dir()
    threading.Thread(target=menu_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)

