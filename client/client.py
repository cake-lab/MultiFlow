import sys
import cv2
import requests
import subprocess
import threading
import queue

SERVER_URL = "http://127.0.0.1:5000/upload"
closed = False

def writer_thread(ffmpeg, frame_queue):
    """Write raw frames into ffmpeg stdin."""
    while not closed:
        try:
            frame = frame_queue.get(timeout=1)
            ffmpeg.stdin.write(frame.tobytes())
        except queue.Empty:
            continue
        except BrokenPipeError:
            break


def reader_thread(ffmpeg, cam_id):
    """Read encoded chunks from ffmpeg stdout and send to server."""
    while not closed:
        data = ffmpeg.stdout.read(4096)
        if not data:
            continue
        try:
            requests.post(
                SERVER_URL,
                data=data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Camera-ID": str(cam_id)
                },
                timeout=1
            )
        except requests.exceptions.RequestException:
            pass  # drop chunk if server unreachable


def camera_thread(cam_id):
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"Camera {cam_id} not available")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-f", "h264",
        "-"
    ]
    ffmpeg = subprocess.Popen(
        ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    frame_queue = queue.Queue()

    # Start writer + reader threads
    threading.Thread(target=writer_thread, args=(ffmpeg, frame_queue), daemon=True).start()
    threading.Thread(target=reader_thread, args=(ffmpeg, cam_id), daemon=True).start()

    print(f"Started camera {cam_id}")

    while not closed:
        ret, frame = cap.read()
        if not ret:
            break
        try:
            frame_queue.put_nowait(frame)
        except queue.Full:
            pass  # drop if queue is overloaded

    cap.release()
    ffmpeg.stdin.close()
    ffmpeg.wait()


# Detect available cameras
def detect_cameras(max_test=5):
    cams = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cams.append(i)
        cap.release()
    return cams
def wait_for_key():
    print("Press any key to shut down...")
    sys.stdin.read(1)  # read 1 character
    print("Key pressed, shutting down...")
    closed = True


if __name__ == "__main__":
    cameras = detect_cameras()
    print("Detected cameras:", cameras)

    for cam in cameras:
        threading.Thread(target=camera_thread, args=(cam,), daemon=True).start()

    # Keep main thread alive
    wait_for_key()
