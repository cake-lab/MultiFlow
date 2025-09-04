import cv2
import numpy as np
import socket
import subprocess
import threading

HOST = "0.0.0.0"
PORT = 5000
WIDTH, HEIGHT = 640, 480

# Socket setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print("Waiting for client...")
conn, addr = server.accept()
print(f"Client connected: {addr}")

# FFmpeg decoder
ffmpeg_cmd = [
    "ffmpeg",
    "-i", "pipe:0",             # stdin = h264 mpegts
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-"
]
ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def recv_stream():
    """Receive encoded data from client and feed to ffmpeg stdin."""
    while True:
        data = conn.recv(4096)
        if not data:
            break
        try:
            ffmpeg.stdin.write(data)
        except BrokenPipeError:
            break


def display_frames():
    """Read raw frames from ffmpeg stdout and display with OpenCV."""
    frame_size = WIDTH * HEIGHT * 3
    while True:
        raw_frame = ffmpeg.stdout.read(frame_size)
        if len(raw_frame) < frame_size:
            break
        frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))
        cv2.imshow("Server", frame)
        if cv2.waitKey(1) == 27:  # ESC
            break


# Start threads
t1 = threading.Thread(target=recv_stream, daemon=True)
t2 = threading.Thread(target=display_frames, daemon=True)
t1.start()
t2.start()

try:
    t1.join()
    t2.join()
except KeyboardInterrupt:
    pass

ffmpeg.terminate()
conn.close()
server.close()
cv2.destroyAllWindows()
