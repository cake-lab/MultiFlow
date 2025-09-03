import cv2
import socket
import subprocess

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

# OpenCV capture
cap = cv2.VideoCapture(0)  # webcam
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))

# FFmpeg process: raw frames → H.264 stream
ffmpeg_cmd = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", "640x480",
    "-r", "30",
    "-i", "-",                # input from stdin
    "-an",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-f", "mpegts", "-"        # output to stdout
]
ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Write frame to ffmpeg stdin
        ffmpeg.stdin.write(frame.tobytes())
        # Read encoded chunk and send to server
        data = ffmpeg.stdout.read1(4096)
        if data:
            sock.sendall(data)
except KeyboardInterrupt:
    pass

cap.release()
ffmpeg.stdin.close()
ffmpeg.terminate()
sock.close()