"""
Test client that uses mp4 files under `client/testing/tests/<testname>/` as camera sources.
Operates similarly to `client.py` but replaces physical cameras with video files.

Commands (single-char or with name):
 l               - list test sets and their cameras
 s <testname>    - start all cameras in test set
 t <testname>    - stop all cameras in test set
 q               - quit (stop everything)

Place mp4 files in `client/testing/tests/<testname>/` directories.
"""
import sys
import socket
import cv2
import requests
import subprocess
import threading
import queue
import time
import argparse
from pathlib import Path
import urllib.parse

DEFAULT_SERVER_URL = "http://127.0.0.1:5000/upload"
SERVER_URL = DEFAULT_SERVER_URL


def build_server_url(host: str, port: int) -> str:
    base = f"http://{host}:{port}"
    return urllib.parse.urljoin(base, "/upload")

def _reader_loop(ffmpeg, cam_unique_id, stop_event):
    while not stop_event.is_set():
        data = ffmpeg.stdout.read(4096)
        if not data:
            if ffmpeg.poll() is not None:
                break
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
            pass


class CameraController:
    """Camera controller that accepts either an integer device index or a file path as source."""

    def __init__(self, source, unique_id: str):
        self.source = source
        self.unique_id = unique_id
        self.stop_event = threading.Event()
        self._thread = None
        self.unique_id_timestamped = None

    def start(self):
        if self._thread and self._thread.is_alive():
            print(f"Camera {self.unique_id} already running")
            return
        self.stop_event.clear()
        self.unique_id_timestamped = f"{self.unique_id}-{time.strftime('%Y.%m.%d.%H.%M.%S')}"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def _run(self):
        print(self.source)
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",
            "-nostdin",
            "-i", f"{self.source}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",
            "-f", "rawvideo",
            "-"
        ]

        ffmpeg = subprocess.Popen(
            ffmpeg_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        reader = threading.Thread(target=_reader_loop, args=(ffmpeg, self.unique_id_timestamped, self.stop_event), daemon=True)
        reader.start()

        print(f"Started camera {self.unique_id_timestamped} (source {self.source})")

        reader.join()
        if not self.stop_event.is_set():
            print(f"Camera {self.unique_id_timestamped} stream ended")
            self.stop_event.set()
        ffmpeg.terminate()
        try:
            ffmpeg.wait()
        except Exception:
            pass
        if self.unique_id_timestamped:
            try:
                requests.delete(SERVER_URL, headers={"Camera-ID": str(self.unique_id_timestamped)}, timeout=1)
            except requests.exceptions.RequestException:
                pass


def detect_tests(tests_dir: Path):
    sets = {}
    if not tests_dir.exists():
        return sets
    for p in tests_dir.iterdir():
        if p.is_dir():
            # gather mp4 files (case-insensitive)
            files = sorted([f for f in p.iterdir() if f.is_file() and f.suffix.lower() == '.mp4'])
            if files:
                sets[p.name] = files
    return sets


def make_unique_id(hostname: str, testname: str, index: int) -> str:
    return f"{hostname}-{testname}-{index}-test"


def interactive_menu(server_url: str = DEFAULT_SERVER_URL):
    hostname = socket.gethostname()
    base_tests_dir = Path(__file__).parent / 'tests'
    controllers_by_set = {}

    def print_menu(sets):
        print('\nAvailable test sets:')
        for name, files in sets.items():
            print(f" - {name}: {len(files)} file(s)")
        print('\nCommands:')
        print(' l <opt> - list test sets or list <setname> to see files')
        print(' s <set> - start all cameras in <set>')
        print(' t <set> - stop all cameras in <set>')
        print(' q       - quit (stop all and exit)')

    sets = detect_tests(base_tests_dir)
    print('Detected test sets:', list(sets.keys()))
    print_menu(sets)

    while True:
        try:
            cmd = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            cmd = 'q'

        if not cmd:
            continue
        parts = cmd.split()
        c = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if c == 'l':
            if arg:
                if arg in sets:
                    print(f"Files in {arg}:")
                    for i, f in enumerate(sets[arg]):
                        print(f"  {i}: {f}")
                else:
                    print(f"Unknown set {arg}")
            else:
                print_menu(sets)
        elif c == 's':
            if not arg:
                print('Specify test set name to start: s <setname>')
                continue
            if arg not in sets:
                print('Unknown test set')
                continue
            if arg in controllers_by_set and any(c._thread and c._thread.is_alive() for c in controllers_by_set[arg].values()):
                print('Set already running')
                continue

            ctrls = {}
            for i, fp in enumerate(sets[arg]):
                uid = make_unique_id(hostname, arg, i)
                ctrls[uid] = CameraController(str(fp), uid)
            controllers_by_set[arg] = ctrls
            for ctrl in ctrls.values():
                ctrl.start()
        elif c == 't':
            if not arg:
                print('Specify test set name to stop: t <setname>')
                continue
            if arg not in controllers_by_set:
                print('Set not running')
                continue
            for ctrl in controllers_by_set[arg].values():
                ctrl.stop()
            del controllers_by_set[arg]
        elif c == 'q':
            for ctrls in list(controllers_by_set.values()):
                for ctrl in ctrls.values():
                    ctrl.stop()
            print('Exiting')
            break
        else:
            print('Unknown command')


def main(argv=None):
    parser = argparse.ArgumentParser(description='MultiFlow test client (uses mp4 test files)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--server-url', help='Full server upload URL (overrides --host/--port)')
    parser.add_argument('--host', help='Server host to connect to (used with --port)', default='127.0.0.1')
    parser.add_argument('--port', type=int, help='Server port to connect to (used with --host)', default=5000)
    args = parser.parse_args(argv)

    if args.server_url:
        server_url = args.server_url
    else:
        server_url = build_server_url(args.host, args.port)

    global SERVER_URL
    SERVER_URL = server_url

    interactive_menu(server_url=server_url)


if __name__ == '__main__':
    main()
