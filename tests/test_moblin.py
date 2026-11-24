import json
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote

from websockets.sync.server import serve

from dollybot.adapters.moblin import Moblin, MoblinError
from dollybot.capture import capture


class AdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        sample = Path(cls.fixture.name) / "sample.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=size=320x180:rate=30", "-t", "0.6", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(sample)], check=True, timeout=30)
        cls.video = sample.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.state = {"recording": False, "names": ["older.mp4"], "commands": [],
                      "drop_start_ack": False, "disconnect_stop": False, "truncate": False}
        state = self.state
        video = self.video

        def websocket(connection):
            for raw in connection:
                request = json.loads(raw).get("request")
                if request is None:
                    continue
                data = request["data"]
                state["commands"].append(data)
                response = {}
                if "setRecord" in data:
                    on = data["setRecord"]["on"]
                    if not on and state["disconnect_stop"]:
                        state["disconnect_stop"] = False
                        connection.close()
                        break
                    if state["recording"] and not on:
                        state["names"].append(f"clip-{len(state['names'])}.mp4")
                    state["recording"] = on
                    connection.send(json.dumps({"event": {"data": {"state": {"data": {"recording": on}}}}}))
                    if on and state["drop_start_ack"]:
                        continue
                elif "getStatus" in data:
                    response = {"getStatus": {"general": {"isRecording": state["recording"]},
                                              "topLeft": {}, "topRight": {}}}
                connection.send(json.dumps({"response": {"id": request["id"], "result": {"ok": {}}, "data": response}}))

        self.ws_server = serve(websocket, "127.0.0.1", 0)
        ws_port = self.ws_server.socket.getsockname()[1]
        self.ws_thread = threading.Thread(target=self.ws_server.serve_forever, daemon=True)
        self.ws_thread.start()

        class Http(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/js/config.mjs":
                    payload = f"export const websocketPort = {ws_port};".encode()
                    kind = "text/javascript"
                elif self.path == "/recordings.json":
                    payload = json.dumps([{"name": n, "size": "15 KB"} for n in state["names"]]).encode()
                    kind = "application/json"
                elif self.path.startswith("/recordings/") and unquote(self.path[12:]) in state["names"]:
                    payload = video
                    kind = "video/mp4"
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload[:100] if state["truncate"] and kind == "video/mp4" else payload)

            def log_message(self, *_):
                pass

        self.http_server = ThreadingHTTPServer(("127.0.0.1", 0), Http)
        self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.http_thread.start()
        self.url = f"http://127.0.0.1:{self.http_server.server_port}"

    def tearDown(self):
        self.ws_server.shutdown()
        self.http_server.shutdown()
        self.http_server.server_close()
        self.ws_thread.join(timeout=2)
        self.http_thread.join(timeout=2)
        self.directory.cleanup()

    def test_capture_download_and_original_hash(self):
        with Moblin(self.url) as camera:
            report = capture(camera, 0.1, self.root, verify_copy=True)
        self.assertEqual(report["outcome"], "complete")
        self.assertFalse(self.state["recording"])
        self.assertEqual(Path(report["local_path"]).read_bytes(), self.video)
        self.assertTrue(report["byte_identical_repeat_download"])
        self.assertEqual(report["video"]["width"], 320)
        self.assertEqual(report["video"]["height"], 180)
        self.assertEqual(report["video"]["decoded_frames"], 18)
        self.assertAlmostEqual(report["video"]["timestamp_fps"], 30, places=3)
        self.assertEqual(report["video"]["gaps_over_1_5x_median"], 0)

    def test_existing_recording_is_not_interrupted(self):
        self.state["recording"] = True
        with Moblin(self.url) as camera:
            with self.assertRaises(MoblinError):
                capture(camera, 0.1, self.root)
        self.assertTrue(self.state["recording"])
        self.assertFalse(any("setRecord" in c for c in self.state["commands"]))

    def test_lost_start_ack_still_stops_recording(self):
        self.state["drop_start_ack"] = True
        with Moblin(self.url, timeout=0.3) as camera:
            with self.assertRaises(TimeoutError):
                capture(camera, 0.1, self.root)
        self.assertFalse(self.state["recording"])
        reports = list(self.root.glob("*/report.json"))
        self.assertEqual(json.loads(reports[0].read_text())["outcome"], "failed")

    def test_disconnect_during_stop_reconnects_and_stops(self):
        self.state["disconnect_stop"] = True
        with Moblin(self.url) as camera:
            report = capture(camera, 0.1, self.root)
        self.assertFalse(self.state["recording"])
        self.assertEqual(report["outcome"], "complete")
        self.assertTrue(report["stop"]["reconnected"])

    def test_short_file_is_flagged_despite_successful_transfer(self):
        with Moblin(self.url) as camera, patch("dollybot.capture.time.sleep"):
            report = capture(camera, 2, self.root)
        self.assertEqual(report["outcome"], "complete")
        self.assertFalse(report["duration_check"]["requested_main_duration_covered"])
        self.assertFalse(report["duration_check"]["matches_main_plus_tail_within_tolerance"])
        self.assertGreater(report["duration_check"]["shortfall_vs_main_plus_tail_seconds"], 1)

    def test_ambiguous_recording_is_not_selected(self):
        with Moblin(self.url) as camera:
            previous = {r["name"] for r in camera.recordings()}
            self.state["names"].extend(["one.mp4", "two.mp4"])
            with self.assertRaisesRegex(MoblinError, "Multiple"):
                camera.wait_for_recording(previous)

    def test_truncated_download_is_not_promoted(self):
        self.state["truncate"] = True
        with Moblin(self.url) as camera:
            with self.assertRaises(MoblinError):
                camera.download("older.mp4", self.root / "clip.mp4")
        self.assertFalse((self.root / "clip.mp4").exists())
        self.assertFalse((self.root / "clip.mp4.partial").exists())

    def test_existing_file_is_preserved(self):
        destination = self.root / "clip.mp4"
        destination.write_bytes(b"preserve me")
        with Moblin(self.url) as camera:
            with self.assertRaises(FileExistsError):
                camera.download("older.mp4", destination)
        self.assertEqual(destination.read_bytes(), b"preserve me")

    def test_paths_and_invalid_duration_are_rejected(self):
        with Moblin(self.url) as camera:
            with self.assertRaises(ValueError):
                camera.download("../outside.mp4", self.root / "clip.mp4")
            with self.assertRaises(ValueError):
                capture(camera, float("nan"), self.root)


if __name__ == "__main__":
    unittest.main()
