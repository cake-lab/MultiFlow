import socket
import subprocess

HOST = "0.0.0.0"
PORT = 5000

# Socket setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print("Waiting for client...")
conn, addr = server.accept()
print(f"Client connected: {addr}")

# FFmpeg process: H.264 → raw frames
ffmpeg_cmd = [
    "ffmpeg",
    "-i", "pipe:0",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-"
]
ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

import cv2
import numpy as np

try:
    while True:
        data = conn.recv(4096)
        if not data:
            break
        ffmpeg.stdin.write(data)

        # Try to read one frame worth of bytes (640*480*3)
        frame_size = 640 * 480 * 3
        raw_frame = ffmpeg.stdout.read(frame_size)
        if len(raw_frame) == frame_size:
            frame = np.frombuffer(raw_frame, np.uint8).reshape((480, 640, 3))
            cv2.imshow("Server", frame)
            if cv2.waitKey(1) == 27:  # ESC to quit
                break
except KeyboardInterrupt:
    pass

ffmpeg.terminate()
conn.close()
server.close()
cv2.destroyAllWindows()
