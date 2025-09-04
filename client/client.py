import cv2
import socket
import subprocess
import threading

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
WIDTH, HEIGHT = 640, 480

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))

# FFmpeg encoder
ffmpeg_cmd = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-r", "30",
    "-i", "-",                 # stdin raw frames
    "-an",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-f", "mpegts", "-"         # stdout H264
]
ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)


def feed_frames():
    """Capture frames and write to ffmpeg stdin."""
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        try:
            ffmpeg.stdin.write(frame.tobytes())
        except BrokenPipeError:
            break


def send_stream():
    """Read encoded data from ffmpeg stdout and send to server."""
    while True:
        data = ffmpeg.stdout.read1(4096)
        if not data:
            break
        sock.sendall(data)


# Start threads
t1 = threading.Thread(target=feed_frames, daemon=True)
t2 = threading.Thread(target=send_stream, daemon=True)
t1.start()
t2.start()

try:
    t1.join()
    t2.join()
except KeyboardInterrupt:
    pass

cap.release()
ffmpeg.terminate()
sock.close()
