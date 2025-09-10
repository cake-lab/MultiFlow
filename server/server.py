from flask import Flask, request
import subprocess
import threading
import cv2
import numpy as np
import queue
import os

app = Flask(__name__)

camera_streams = {}


def writer_thread(ffmpeg, frame_queue):
    """Continuously feed encoded chunks into ffmpeg stdin."""
    while True:
        try:
            chunk = frame_queue.get(timeout=1)
            ffmpeg.stdin.write(chunk)
        except queue.Empty:
            continue
        except BrokenPipeError:
            break

def start_decoder(camera_id):
    """Start a new ffmpeg decoder process and threads for a camera."""
    out_dir = f"./chunks/{camera_id}"
    os.makedirs(out_dir, exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "pipe:0",                
        "-c:v", "libx264",
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
    q = queue.Queue()
    camera_streams[camera_id] = q
    threading.Thread(target=writer_thread, args=(ffmpeg, q), daemon=True).start()


@app.route("/upload", methods=["POST"])
def upload():
    cam_id = request.headers.get("Camera-ID", "0")
    chunk = request.data
    if not chunk:
        return "No data", 400

    # Start a decoder thread per new camera
    if cam_id not in camera_streams:
        start_decoder(cam_id)

    camera_streams[cam_id].put(chunk)
    return "OK", 200

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
if __name__ == "__main__":
    import os
    reset_chunks_dir()
    app.run(host="0.0.0.0", port=5000, threaded=True)
