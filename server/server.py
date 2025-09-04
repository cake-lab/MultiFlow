import cv2
import numpy as np
import socket
import subprocess
import threading
import struct
from flask import Flask, Response, render_template_string

HOST = "0.0.0.0"
PORT = 5000
WIDTH, HEIGHT = 640, 480

frames = {}      # frames[client_id][cam_index] = latest frame
decoders = {}    # decoders[(client_id, cam_index)] = ffmpeg proc

app = Flask(__name__)


def get_decoder(client_id, cam_index):
    key = (client_id, cam_index)
    if key not in decoders:
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "pipe:0",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-"
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        decoders[key] = proc

        def read_frames():
            frame_size = WIDTH * HEIGHT * 3
            while True:
                raw = proc.stdout.read(frame_size)
                if len(raw) < frame_size:
                    break
                frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 3))
                frames.setdefault(client_id, {})[cam_index] = frame

        threading.Thread(target=read_frames, daemon=True).start()
    return decoders[key]


def handle_client(conn):
    buf = b""
    while True:
        while len(buf) < 9:  # header size = 4+1+4
            data = conn.recv(4096)
            if not data:
                return
            buf += data

        client_id, cam_index, length = struct.unpack("!IBI", buf[:9])
        buf = buf[9:]

        while len(buf) < length:
            data = conn.recv(4096)
            if not data:
                return
            buf += data

        payload, buf = buf[:length], buf[length:]

        decoder = get_decoder(client_id, cam_index)
        try:
            decoder.stdin.write(payload)
        except BrokenPipeError:
            break


def socket_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("Waiting for clients...")
    while True:
        conn, addr = server.accept()
        print(f"Client connected: {addr}")
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


def generate_mjpeg(client_id, cam_index):
    while True:
        if client_id in frames and cam_index in frames[client_id]:
            ret, jpeg = cv2.imencode(".jpg", frames[client_id][cam_index])
            if ret:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")


@app.route("/camera/<int:client_id>/<int:cam_index>")
def camera_feed(client_id, cam_index):
    return Response(generate_mjpeg(client_id, cam_index),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    html = """
    <html><body>
    <h1>Multi-Client Multi-Camera Stream</h1>
    {% for client, cams in frames.items() %}
      <h2>Client {{client}}</h2>
      {% for cam in cams.keys() %}
        <h3>Camera {{cam}}</h3>
        <img src="{{url_for('camera_feed', client_id=client, cam_index=cam)}}" width="320">
      {% endfor %}
    {% endfor %}
    </body></html>
    """
    return render_template_string(html, frames=frames)


if __name__ == "__main__":
    threading.Thread(target=socket_listener, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
