import cv2
import socket
import subprocess
import threading
import struct
import random

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
WIDTH, HEIGHT = 640, 480

# assign a unique id for this client (in real world: could be UUID)
CLIENT_ID = random.randint(1, 1_000_000)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))


def camera_worker(cam_index):
    cap = cv2.VideoCapture(cam_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", "30",
        "-i", "-",
        "-an",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-f", "mpegts", "-"
    ]
    ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def feed_frames():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            try:
                ffmpeg.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break

    def send_stream():
        while True:
            data = ffmpeg.stdout.read1(4096)
            if not data:
                break
            # prepend: client_id(4) + cam_index(1) + length(4)
            header = struct.pack("!IBI", CLIENT_ID, cam_index, len(data))
            sock.sendall(header + data)

    threading.Thread(target=feed_frames, daemon=True).start()
    threading.Thread(target=send_stream, daemon=True).start()


# Example: 2 cameras per client
for cam_index in [0, 1]:
    threading.Thread(target=camera_worker, args=(cam_index,), daemon=True).start()

try:
    while True:
        pass
except KeyboardInterrupt:
    sock.close()
