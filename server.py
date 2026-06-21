import argparse
import ctypes
import io
import json
import queue
import re
import secrets
import shutil
import socket
import subprocess
import threading
import time
import warnings
import wave
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from PIL import ImageGrab

ROOT = Path(__file__).parent
WEB = ROOT / "web"
RECEIVED_FILES = ROOT / "received_files"
SHARED_FILES = ROOT / "shared_files"
TOKEN = ""
JPEG_QUALITY = 55
input_lock = threading.Lock()
user32 = ctypes.windll.user32
TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
MAX_UPLOAD_SIZE = 512 * 1024 * 1024

try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort),
                ("wParamH", ctypes.c_ushort)]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", INPUT_UNION)]


user32.SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = ctypes.c_uint


VK = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "shift": 0x10,
    "ctrl": 0x11, "alt": 0x12, "esc": 0x1B, "space": 0x20,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "delete": 0x2E, "home": 0x24, "end": 0x23, "c": 0x43, "v": 0x56,
}


class CameraHub:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None
        self.error = ""
        self.thread = None
        self.stop_event = threading.Event()
        self.ready = threading.Event()

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.frame = None
            self.error = ""
            self.stop_event.clear()
            self.ready.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def _run(self):
        capture = None
        try:
            import cv2
            capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
            if not capture.isOpened():
                raise RuntimeError("无法打开电脑摄像头")
            while not self.stop_event.is_set():
                ok, image = capture.read()
                if not ok:
                    raise RuntimeError("无法读取摄像头画面")
                ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 72])
                if ok:
                    with self.lock:
                        self.frame = encoded.tobytes()
                    self.ready.set()
                self.stop_event.wait(0.06)
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
            self.ready.set()
        finally:
            if capture is not None:
                capture.release()

    def get_frame(self):
        self.start()
        self.ready.wait(5)
        with self.lock:
            if self.error:
                raise RuntimeError(self.error)
            if not self.frame:
                raise RuntimeError("摄像头尚未准备好")
            return self.frame

    def stop(self):
        self.stop_event.set()
        thread = self.thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self.lock:
            self.thread = None
            self.frame = None


camera_hub = CameraHub()


class PhoneMicPlayer:
    def __init__(self):
        self.chunks = queue.Queue(maxsize=24)
        self.thread = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.error = ""

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.error = ""
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def add(self, pcm, sample_rate):
        self.start()
        item = (sample_rate, pcm)
        try:
            self.chunks.put_nowait(item)
        except queue.Full:
            try:
                self.chunks.get_nowait()
            except queue.Empty:
                pass
            self.chunks.put_nowait(item)

    def clear(self):
        while True:
            try:
                self.chunks.get_nowait()
            except queue.Empty:
                return

    def _run(self):
        import numpy as np
        import soundcard as sc

        context = None
        player = None
        active_rate = None
        try:
            speaker = sc.default_speaker()
            if speaker is None:
                raise RuntimeError("未找到电脑扬声器")
            while not self.stop_event.is_set():
                try:
                    sample_rate, pcm = self.chunks.get(timeout=0.2)
                except queue.Empty:
                    continue
                if sample_rate != active_rate:
                    if context is not None:
                        context.__exit__(None, None, None)
                    context = speaker.player(samplerate=sample_rate, channels=1)
                    player = context.__enter__()
                    active_rate = sample_rate
                samples = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
                player.play(samples.reshape(-1, 1))
        except Exception as exc:
            self.error = str(exc)
        finally:
            if context is not None:
                context.__exit__(None, None, None)

    def stop(self):
        self.stop_event.set()
        self.clear()
        thread = self.thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self.lock:
            self.thread = None


phone_mic_player = PhoneMicPlayer()


def screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def mouse(flags, x=0, y=0, data=0):
    user32.mouse_event(flags, int(x), int(y), int(data), 0)


def key_vk(code, up=False):
    user32.keybd_event(code, 0, KEYEVENTF_KEYUP if up else 0, 0)


def type_text(text):
    raw = text.encode("utf-16-le")
    for i in range(0, len(raw), 2):
        code = raw[i] | (raw[i + 1] << 8)
        events = (INPUT * 2)(
            INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, 0))),
            INPUT(type=1, u=INPUT_UNION(ki=KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0))),
        )
        if user32.SendInput(2, events, ctypes.sizeof(INPUT)) != 2:
            raise ValueError("Windows rejected keyboard input")


def open_windows_keyboard():
    # Starting osk.exe directly can be rejected by Windows UIAccess rules.
    # Using the normal Win+R route behaves exactly like a local user opening it.
    win_key = 0x5B
    r_key = 0x52
    enter_key = 0x0D
    key_vk(win_key)
    key_vk(r_key)
    key_vk(r_key, True)
    key_vk(win_key, True)
    time.sleep(0.25)
    type_text("osk")
    key_vk(enter_key)
    key_vk(enter_key, True)


class AudioCaptureHub:
    def __init__(self, source):
        self.source = source
        self.sample_rate = 48000
        self.blocks = queue.Queue(maxsize=40)
        self.stop_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()
        self.read_lock = threading.Lock()
        self.error = ""

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.error = ""
            self.stop_event.clear()
            self.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def clear(self):
        while True:
            try:
                self.blocks.get_nowait()
            except queue.Empty:
                return

    def _run(self):
        import soundcard as sc

        try:
            if self.source == "system":
                speaker = sc.default_speaker()
                if speaker is None:
                    raise RuntimeError("未找到电脑播放设备")
                device = sc.get_microphone(id=str(speaker.name), include_loopback=True)
            else:
                device = sc.default_microphone()
                if device is None:
                    raise RuntimeError("未找到电脑麦克风")
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="data discontinuity in recording")
                with device.recorder(samplerate=self.sample_rate) as recorder:
                    while not self.stop_event.is_set():
                        block = recorder.record(numframes=4800)
                        try:
                            self.blocks.put_nowait(block)
                        except queue.Full:
                            try:
                                self.blocks.get_nowait()
                            except queue.Empty:
                                pass
                            self.blocks.put_nowait(block)
        except Exception as exc:
            self.error = str(exc)

    def read(self, duration):
        import numpy as np

        wanted = int(self.sample_rate * max(0.5, min(2.5, duration)))
        self.start()
        with self.read_lock:
            self.clear()
            chunks = []
            received = 0
            deadline = time.monotonic() + duration + 5
            while received < wanted:
                if self.error:
                    raise RuntimeError(self.error)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("等待音频数据超时")
                try:
                    block = self.blocks.get(timeout=min(0.5, remaining))
                except queue.Empty:
                    continue
                chunks.append(block)
                received += len(block)
            samples = np.concatenate(chunks, axis=0)[:wanted]
            return samples

    def stop(self):
        self.stop_event.set()
        thread = self.thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self.lock:
            self.thread = None
        self.clear()


audio_capture_hubs = {
    "system": AudioCaptureHub("system"),
    "microphone": AudioCaptureHub("microphone"),
}


def record_audio(source, duration):
    import numpy as np

    if source not in audio_capture_hubs:
        raise ValueError("unknown audio source")
    samples = audio_capture_hubs[source].read(duration)
    if samples.ndim == 1:
        samples = samples.reshape(-1, 1)
    samples = np.nan_to_num(samples)
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(pcm.shape[1])
        wav.setsampwidth(2)
        wav.setframerate(audio_capture_hubs[source].sample_rate)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def safe_file(directory, supplied_name):
    name = Path(unquote(supplied_name)).name
    if not name or name in (".", ".."):
        raise ValueError("invalid file name")
    directory.mkdir(exist_ok=True)
    path = (directory / name).resolve()
    if path.parent != directory.resolve():
        raise ValueError("invalid file path")
    return path


def available_name(directory, supplied_name):
    path = safe_file(directory, supplied_name)
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for number in range(1, 10000):
        candidate = path.with_name(f"{stem} ({number}){suffix}")
        if not candidate.exists():
            return candidate
    raise ValueError("too many files with the same name")


def focused_accepts_text():
    try:
        import uiautomation as automation
        control = automation.GetFocusedControl()
        if control is None:
            return False
        return control.ControlTypeName in {
            "EditControl",
            "ComboBoxControl",
            "SpinnerControl",
        } and bool(control.IsKeyboardFocusable)
    except Exception:
        return False


def button_flag(button, down):
    if button == "right":
        return MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP
    return MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP


def perform(data):
    kind = data.get("type")
    if kind == "move":
        dx = max(-500, min(500, float(data.get("dx", 0))))
        dy = max(-500, min(500, float(data.get("dy", 0))))
        mouse(MOUSEEVENTF_MOVE, dx, dy)
    elif kind == "absolute":
        w, h = screen_size()
        x = max(0, min(w - 1, int(float(data.get("x", 0)) * w)))
        y = max(0, min(h - 1, int(float(data.get("y", 0)) * h)))
        mouse(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
              round(x * 65535 / max(1, w - 1)), round(y * 65535 / max(1, h - 1)))
    elif kind == "click":
        flag = button_flag(data.get("button", "left"), True)
        mouse(flag)
        mouse(button_flag(data.get("button", "left"), False))
    elif kind == "button":
        action = data.get("action")
        if action not in ("down", "up"):
            raise ValueError("button action must be down or up")
        mouse(button_flag(data.get("button", "left"), action == "down"))
    elif kind == "scroll":
        amount = max(-10, min(10, float(data.get("amount", 0))))
        mouse(MOUSEEVENTF_WHEEL, data=int(amount * 120))
    elif kind == "text":
        type_text(str(data.get("text", ""))[:1000])
    elif kind == "key":
        codes = [VK[n] for n in data.get("keys", []) if n in VK]
        for code in codes:
            key_vk(code)
        for code in reversed(codes):
            key_vk(code, True)
    elif kind == "open_keyboard":
        open_windows_keyboard()
    else:
        raise ValueError("unknown input type")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

    def authorized(self):
        query = parse_qs(urlparse(self.path).query)
        supplied = self.headers.get("X-Control-Token", "") or query.get("token", [""])[0]
        return secrets.compare_digest(supplied, TOKEN)

    def send_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/status":
            if not self.authorized():
                return self.send_json(403, {"error": "访问密钥不正确"})
            w, h = screen_size()
            return self.send_json(200, {"ok": True, "width": w, "height": h})
        if path == "/api/screen.jpg":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            image = ImageGrab.grab(all_screens=False).convert("RGB")
            image.thumbnail((1280, 720))
            out = io.BytesIO()
            image.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
            body = out.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.end_headers()
            return self.wfile.write(body)
        if path == "/api/camera.jpg":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            try:
                body = camera_hub.get_frame()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.end_headers()
                return self.wfile.write(body)
            except RuntimeError as exc:
                return self.send_json(503, {"error": str(exc)})
        if path == "/api/audio.wav":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            try:
                query = parse_qs(parsed.query)
                source = query.get("source", ["system"])[0]
                duration = float(query.get("duration", ["1.5"])[0])
                body = record_audio(source, duration)
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return self.wfile.write(body)
            except (RuntimeError, ValueError) as exc:
                return self.send_json(503, {"error": str(exc)})
        if path == "/api/focus":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            return self.send_json(200, {"acceptsText": focused_accepts_text()})
        if path == "/api/files":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            SHARED_FILES.mkdir(exist_ok=True)
            files = [
                {"name": item.name, "size": item.stat().st_size,
                 "modified": int(item.stat().st_mtime)}
                for item in SHARED_FILES.iterdir()
                if item.is_file() and not item.name.startswith(".")
            ]
            files.sort(key=lambda item: item["modified"], reverse=True)
            return self.send_json(200, {"files": files})
        if path == "/api/files/download":
            if not self.authorized():
                return self.send_json(403, {"error": "forbidden"})
            try:
                query = parse_qs(parsed.query)
                file_path = safe_file(SHARED_FILES, query.get("name", [""])[0])
                if not file_path.is_file():
                    return self.send_json(404, {"error": "file not found"})
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.send_header(
                    "Content-Disposition",
                    f"attachment; filename*=UTF-8''{quote(file_path.name)}",
                )
                self.end_headers()
                with file_path.open("rb") as source:
                    shutil.copyfileobj(source, self.wfile, length=1024 * 1024)
                return
            except ValueError as exc:
                return self.send_json(400, {"error": str(exc)})
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if not self.authorized():
            return self.send_json(403, {"error": "访问密钥不正确"})
        if path == "/api/camera/stop":
            camera_hub.stop()
            return self.send_json(200, {"ok": True})
        if path == "/api/phone-mic":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                sample_rate = int(self.headers.get("X-Sample-Rate", "48000"))
                if length <= 0 or length > 262144 or length % 2:
                    raise ValueError("invalid microphone audio block")
                if sample_rate < 8000 or sample_rate > 96000:
                    raise ValueError("invalid microphone sample rate")
                pcm = self.rfile.read(length)
                if len(pcm) != length:
                    raise ValueError("microphone audio block was interrupted")
                phone_mic_player.add(pcm, sample_rate)
                if phone_mic_player.error:
                    raise RuntimeError(phone_mic_player.error)
                return self.send_json(200, {"ok": True})
            except (RuntimeError, ValueError) as exc:
                return self.send_json(400, {"error": str(exc)})
        if path == "/api/phone-mic/stop":
            phone_mic_player.clear()
            return self.send_json(200, {"ok": True})
        if path == "/api/files/upload":
            file_path = None
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_UPLOAD_SIZE:
                    raise ValueError("文件为空或超过 512 MB")
                file_name = self.headers.get("X-File-Name", "")
                file_path = available_name(RECEIVED_FILES, file_name)
                remaining = length
                with file_path.open("wb") as target:
                    while remaining:
                        chunk = self.rfile.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError("上传连接提前中断")
                        target.write(chunk)
                        remaining -= len(chunk)
                return self.send_json(200, {"ok": True, "name": file_path.name})
            except (OSError, ValueError) as exc:
                if file_path and file_path.exists():
                    file_path.unlink()
                return self.send_json(400, {"error": str(exc)})
        if path != "/api/input":
            return self.send_json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 8192:
                raise ValueError("request too large")
            data = json.loads(self.rfile.read(length))
            with input_lock:
                perform(data)
            return self.send_json(200, {"ok": True})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.send_json(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        quiet_paths = ("/api/screen.jpg", "/api/camera.jpg", "/api/audio.wav")
        if not any(path in str(args) for path in quiet_paths):
            super().log_message(fmt, *args)


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def start_tunnel(port, executable=None):
    cloudflared = executable or shutil.which("cloudflared")
    if not cloudflared:
        raise RuntimeError(
            "未找到 cloudflared。请先运行 start-internet.bat 安装，"
            "或执行：winget install --id Cloudflare.cloudflared"
        )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        [cloudflared, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=flags,
    )
    ready = threading.Event()
    result = {"url": ""}

    def read_output():
        assert process.stdout is not None
        for line in process.stdout:
            match = TUNNEL_URL_RE.search(line)
            if match and not result["url"]:
                result["url"] = match.group(0)
                ready.set()

    threading.Thread(target=read_output, daemon=True).start()
    if not ready.wait(30):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError("公网隧道创建超时，请检查网络后重试")
    return process, result["url"]


def main():
    global TOKEN, JPEG_QUALITY
    parser = argparse.ArgumentParser(description="用手机浏览器控制 Windows")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", help="指定访问密钥（默认随机生成）")
    parser.add_argument("--quality", type=int, default=55)
    parser.add_argument("--internet", action="store_true", help="通过 HTTPS 隧道启用外网控制")
    parser.add_argument("--cloudflared", help="cloudflared.exe 的路径")
    args = parser.parse_args()
    TOKEN = args.token or secrets.token_urlsafe(18)
    JPEG_QUALITY = max(25, min(90, args.quality))
    RECEIVED_FILES.mkdir(exist_ok=True)
    SHARED_FILES.mkdir(exist_ok=True)
    bind_host = "127.0.0.1" if args.internet else "0.0.0.0"
    server = ThreadingHTTPServer((bind_host, args.port), Handler)
    tunnel = None
    try:
        if args.internet:
            print("\n正在创建加密公网隧道，请稍候……")
            tunnel, public_url = start_tunnel(args.port, args.cloudflared)
            url = f"{public_url}/?token={TOKEN}"
            print("外网控制已启动，手机可使用移动网络访问：")
        else:
            url = f"http://{local_ip()}:{args.port}/?token={TOKEN}"
            print("\n局域网控制已启动（电脑和手机需连接同一 Wi-Fi）")
        print(f"手机打开：{url}")
        print("按 Ctrl+C 停止。请勿截图或转发此地址。\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    except RuntimeError as exc:
        print(f"\n启动失败：{exc}")
    finally:
        camera_hub.stop()
        phone_mic_player.stop()
        for audio_hub in audio_capture_hubs.values():
            audio_hub.stop()
        if tunnel and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.kill()
        server.server_close()


if __name__ == "__main__":
    main()
