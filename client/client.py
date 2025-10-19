import sys
import socket
import cv2
import requests
import subprocess
import threading
import queue
import time

SERVER_URL = "http://127.0.0.1:5000/upload"


def _writer_loop(ffmpeg, frame_queue, stop_event):
    """Write raw frames into ffmpeg stdin."""
    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=1)
            ffmpeg.stdin.write(frame.tobytes())
        except queue.Empty:
            continue
        except BrokenPipeError:
            break


def _reader_loop(ffmpeg, cam_unique_id, stop_event):
    """Read encoded chunks from ffmpeg stdout and send to server."""
    while not stop_event.is_set():
        data = ffmpeg.stdout.read(4096)
        if not data:
            time.sleep(0.01)
            continue
        try:
            requests.post(
                SERVER_URL,
                data=data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Camera-ID": str(cam_unique_id)
                },
                timeout=1
            )
        except requests.exceptions.RequestException:
            pass  # drop chunk if server unreachable


class CameraController:
    """Encapsulate camera capture, ffmpeg and network threads for one camera."""

    def __init__(self, device_index: int, unique_id: str):
        self.device_index = device_index
        self.unique_id = unique_id
        self.stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            print(f"Camera {self.unique_id} already running")
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.stop_event.set()
        # tell server we're stopping
        try:
            requests.delete(SERVER_URL, headers={"Camera-ID": str(self.unique_id)}, timeout=1)
        except requests.exceptions.RequestException:
            pass
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        cap = cv2.VideoCapture(self.device_index)
        if not cap.isOpened():
            print(f"Camera {self.device_index} not available")
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
        writer = threading.Thread(target=_writer_loop, args=(ffmpeg, frame_queue, self.stop_event), daemon=True)
        reader = threading.Thread(target=_reader_loop, args=(ffmpeg, self.unique_id, self.stop_event), daemon=True)
        writer.start()
        reader.start()

        print(f"Started camera {self.unique_id} (device {self.device_index})")

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
            try:
                frame_queue.put_nowait(frame)
            except queue.Full:
                pass  # drop if queue is overloaded

        cap.release()
        try:
            ffmpeg.stdin.close()
        except Exception:
            pass
        ffmpeg.wait()


def detect_cameras(max_test=5):
    cams = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cams.append(i)
        cap.release()
    return cams


def make_unique_id(hostname: str, index: int) -> str:
    # produce hostname-index so cameras across machines don't collide
    return f"{hostname}-{index}"


def interactive_menu():
    hostname = socket.gethostname()
    detected = detect_cameras()
    controllers = {}

    # Initialize controllers for detected cameras but don't start them
    for i, dev in enumerate(detected):
        uid = make_unique_id(hostname, i)
        controllers[uid] = CameraController(device_index=dev, unique_id=uid)

    def print_menu():
        print('\nAvailable cameras:')
        for uid, ctrl in controllers.items():
            status = 'running' if ctrl._thread and ctrl._thread.is_alive() else 'stopped'
            print(f" - {uid}: device {ctrl.device_index} ({status})")
        print('\nCommands (single-char):')
        print(' l  - list cameras')
        print(' s  - start all cameras')
        print(' t  - stop all cameras')
        print(' q  - quit (stop all and exit)')

    print('Detected cameras:', [controllers[k].device_index for k in controllers])
    print_menu()

    while True:
        try:
            cmd = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            cmd = 'quit'

        if not cmd:
            continue
        c = cmd[0].lower()
        if c == 'l':
            print_menu()
        elif c == 's':
            for ctrl in controllers.values():
                ctrl.start()
        elif c == 't':
            for ctrl in controllers.values():
                ctrl.stop()
        elif c == 'q':
            for ctrl in controllers.values():
                ctrl.stop()
            print('Exiting')
            break
        else:
            print('Unknown command, press l/s/t/q')


if __name__ == '__main__':
    interactive_menu()
