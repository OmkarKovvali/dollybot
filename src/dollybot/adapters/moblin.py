import hashlib
import json
import re
import time
import threading
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import ProxyHandler, build_opener

from websockets.sync.client import connect


class MoblinError(RuntimeError):
    pass


class Moblin:
    def __init__(self, url: str, timeout: float = 5):
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Supply Moblin's http:// or https:// address")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Use the server address without credentials, query, or fragment")
        self.url = f"{parsed.scheme}://{parsed.netloc}"
        self.timeout = timeout
        self.http = build_opener(ProxyHandler({}))
        self.ws = None
        self.sequence = 0
        self.recording = None
        self.recording_observed_at = 0.0
        self._condition = threading.Condition()
        self._request_lock = threading.Lock()
        self._responses = {}
        self._failure = None
        self._reader = None

    @property
    def connected(self) -> bool:
        from websockets.protocol import State
        return self.ws is not None and self.ws.state is State.OPEN and self._failure is None

    def get(self, path: str):
        return self.http.open(self.url + path, timeout=self.timeout)

    def connect(self):
        self.close()
        started = time.perf_counter()
        with self.get("/js/config.mjs") as response:
            config = response.read().decode()
        match = re.search(r"\bwebsocketPort\s*=\s*(\d+)", config)
        if not match or not 0 < int(match[1]) < 65536:
            raise MoblinError("Moblin did not advertise a valid WebSocket port")
        parsed = urlsplit(self.url)
        host = parsed.hostname
        if ":" in host:
            host = f"[{host}]"
        scheme = "wss" if parsed.scheme == "https" else "ws"
        self.ws = connect(f"{scheme}://{host}:{match[1]}", open_timeout=self.timeout,
                          close_timeout=1, ping_interval=None, proxy=None, max_size=4 * 1024 * 1024)
        self._responses.clear()
        self._failure = None
        self._reader = threading.Thread(target=self._receive, args=(self.ws,), daemon=True)
        self._reader.start()
        return round((time.perf_counter() - started) * 1000, 3)

    def close(self):
        if self.ws is not None:
            self.ws.close()
            self.ws = None
        if self._reader is not None:
            self._reader.join(timeout=2)
            self._reader = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    def _receive(self, ws):
        try:
            for raw in ws:
                message = json.loads(raw)
                if 'ping' in message:
                    ws.send(json.dumps({'pong': {}}))
                with self._condition:
                    event = message.get('event', {}).get('data', {}).get('state', {}).get('data', {})
                    if isinstance(event.get('recording'), bool):
                        self.recording = event['recording']
                        self.recording_observed_at = time.perf_counter()
                    response = message.get('response', {})
                    if response.get('id') == self.sequence:
                        self._responses[self.sequence] = response
                    self._condition.notify_all()
        except Exception as error:
            with self._condition:
                self._failure = error
                self._condition.notify_all()
        finally:
            with self._condition:
                if self._failure is None:
                    self._failure = ConnectionError('Moblin connection closed')
                self._condition.notify_all()

    def request(self, data: dict):
        with self._request_lock:
            if self.ws is None:
                raise MoblinError('Connect before sending a command')
            started = time.perf_counter()
            with self._condition:
                if self._failure is not None:
                    raise ConnectionError(f'Moblin connection failed: {self._failure}')
                self.sequence += 1
                request_id = self.sequence
                self._responses.clear()
                self.ws.send(json.dumps({'request': {'id': request_id, 'data': data}}))
                deadline = started + self.timeout
                while request_id not in self._responses:
                    if self._failure is not None:
                        raise ConnectionError(f'Moblin connection failed: {self._failure}')
                    remaining = deadline - time.perf_counter()
                    if remaining <= 0:
                        raise TimeoutError(f'Moblin did not acknowledge request {request_id}')
                    self._condition.wait(remaining)
                response = self._responses.pop(request_id)
            result = response.get('result', {})
            if not isinstance(result, dict) or 'ok' not in result or result['ok'] is False:
                raise MoblinError(f'Moblin rejected request {request_id}: {result}')
            return response.get('data') or {}, round((time.perf_counter() - started) * 1000, 3)

    def status(self):
        data, elapsed = self.request({"getStatus": {}})
        status = data.get("getStatus", {})
        general = status.get("general") or {}
        if isinstance(general.get("isRecording"), bool):
            self.recording = general["isRecording"]
            self.recording_observed_at = time.perf_counter()
        return {"recording": self.recording, "status_rtt_ms": elapsed,
                "battery_level": general.get("batteryLevel"),
                "camera": status.get("topLeft", {}).get("camera"),
                "recording_display": status.get("topRight", {}).get("recording")}

    def set_recording(self, on: bool):
        started = time.perf_counter()
        _, ack_ms = self.request({"setRecord": {"on": on}})
        deadline = started + self.timeout
        while time.perf_counter() < deadline:
            status = self.status()
            if status["recording"] is on and self.recording_observed_at >= started:
                return {"ack_ms": ack_ms,
                        "state_confirmed_ms": round((time.perf_counter() - started) * 1000, 3)}
            time.sleep(0.05)
        raise MoblinError(f"Recording state was not confirmed as {on}; do not retry a take blindly")

    def stop_recording(self):
        started = time.perf_counter()
        reconnected = False
        try:
            result = self.set_recording(False)
        except Exception:
            self.connect()
            reconnected = True
            result = self.set_recording(False)
        result["reconnected"] = reconnected
        result["total_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return result

    def recordings(self):
        with self.get("/recordings.json") as response:
            recordings = json.load(response)
        if not isinstance(recordings, list) or any(not isinstance(r, dict) or not isinstance(r.get("name"), str) for r in recordings):
            raise MoblinError("Unexpected recording list")
        return recordings

    def wait_for_recording(self, previous_names: set[str], timeout: float = 30):
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            new = [r for r in self.recordings() if r["name"] not in previous_names]
            if len(new) > 1:
                raise MoblinError("Multiple new recordings appeared; refusing to guess which is this take")
            if len(new) == 1:
                return new[0]
            time.sleep(0.1)
        raise TimeoutError("No new recording appeared after stop")

    def download(self, name: str, destination: Path | None = None):
        if not name or Path(name).name != name or "\\" in name or name in (".", ".."):
            raise ValueError("Invalid recording filename")
        if destination is not None and destination.exists():
            raise FileExistsError(destination)
        partial = destination.with_name(destination.name + ".partial") if destination else None
        started = time.perf_counter()
        digest = hashlib.sha256()
        size = 0
        output = None
        created = False
        try:
            if partial:
                partial.parent.mkdir(parents=True, exist_ok=True)
                output = partial.open("xb")
                created = True
            with self.get("/recordings/" + quote(name, safe="")) as response:
                expected = response.headers.get("Content-Length")
                content_type = response.headers.get("Content-Type", "")
                if "video/" not in content_type and "application/octet-stream" not in content_type:
                    raise MoblinError(f"Unexpected recording content type: {content_type}")
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    digest.update(chunk)
                    if output:
                        output.write(chunk)
            if size == 0 or (expected is not None and size != int(expected)):
                raise MoblinError(f"Incomplete download: {size} bytes, expected {expected}")
            if output:
                output.close()
                output = None
            elapsed = time.perf_counter() - started
            return {"bytes": size, "sha256": digest.hexdigest(),
                    "download_ms": round(elapsed * 1000, 3),
                    "megabits_per_second": round(size * 8 / elapsed / 1_000_000, 3),
                    "partial_path": str(partial) if partial else None}
        except BaseException:
            if output:
                output.close()
            if created:
                partial.unlink(missing_ok=True)
            raise
