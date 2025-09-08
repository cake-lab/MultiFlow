from flask import Flask, request
import subprocess
import threading
import cv2
import numpy as np
import queue

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


def reader_thread(ffmpeg, camera_id, width=640, height=480):
    """Continuously read decoded frames from ffmpeg stdout and display."""
    frame_size = width * height * 3
    while True:
        raw_frame = ffmpeg.stdout.read(frame_size)
        if not raw_frame:
            continue
        frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
        cv2.imshow(f"Camera {camera_id}", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyWindow(f"Camera {camera_id}")
    ffmpeg.terminate()


def start_decoder(camera_id, width=640, height=480):
    """Start a new ffmpeg decoder process and threads for a camera."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "pipe:0",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-"
    ]
    ffmpeg = subprocess.Popen(
        ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    q = queue.Queue()
    camera_streams[camera_id] = q

    # One thread feeds encoded chunks
    threading.Thread(target=writer_thread, args=(ffmpeg, q), daemon=True).start()

    # Another thread reads decoded frames
    threading.Thread(target=reader_thread, args=(ffmpeg, camera_id, width, height), daemon=True).start()


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
