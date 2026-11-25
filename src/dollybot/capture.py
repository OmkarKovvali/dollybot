import json
import math
import time
import sys
from typing import Callable
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dollybot.adapters.moblin import Moblin, MoblinError
from dollybot.media import inspect_video


def capture(camera: Moblin, seconds: float, output: Path, verify_copy: bool = False, tail_seconds: float = 0,
            record_action: Callable[[], object] | None = None,
            wait: Callable[[float], None] = time.sleep,
            on_state: Callable[[bool], None] | None = None):
    if not math.isfinite(seconds) or not 0.1 <= seconds <= 60:
        raise ValueError("Recording duration must be between 0.1 and 60 seconds")
    if not math.isfinite(tail_seconds) or not 0 <= tail_seconds <= 10:
        raise ValueError("Recording tail must be between zero and ten seconds")
    take_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:8]
    folder = output / take_id
    folder.mkdir(parents=True)
    report = {"take_id": take_id, "started_at": datetime.now(timezone.utc).isoformat(),
              "requested_recording_seconds": seconds, "phone_url": camera.url, "outcome": "pending",
              "tail_seconds": tail_seconds,
              "timing_definition": "Mac monotonic elapsed times; acknowledgements/state are not sensor exposure timestamps",
              "transfer_mode": "original HTTP file download after recording stops; no transcoding"}
    report_path = folder / "report.json"

    def save():
        temp = report_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(report_path)

    save()
    started = time.perf_counter()
    try:
        report["initial_status"] = camera.status()
        if report["initial_status"]["recording"] is not False:
            raise MoblinError("Phone is already recording or its state is unknown; leaving it untouched")
        previous = {r["name"] for r in camera.recordings()}
        report["outcome"] = "starting"
        save()
        wait(0)
        record_started = time.perf_counter()
        try:
            report["start"] = camera.set_recording(True)
            if on_state:
                on_state(True)
            report["outcome"] = "recording"
            save()
            print(f"Recording {seconds:g}s: {take_id}", flush=True, file=sys.stderr)
            if record_action is None:
                wait(seconds)
            else:
                report["motion"] = record_action()
            if tail_seconds:
                print(f"Recording tail: {tail_seconds:g}s", flush=True, file=sys.stderr)
                wait(tail_seconds)
        finally:
            stop_started = time.perf_counter()
            report["start_command_to_stop_command_ms"] = round((stop_started - record_started) * 1000, 3)
            report["stop"] = camera.stop_recording()
            if on_state:
                on_state(False)
            report["outcome"] = "stopped"
            save()
        recording = camera.wait_for_recording(previous)
        report["source_filename"] = recording["name"]
        report["stop_to_file_listed_ms"] = round((time.perf_counter() - stop_started) * 1000, 3)
        report["outcome"] = "downloading"
        save()
        destination = folder / "original.mp4"
        report["transfer"] = camera.download(recording["name"], destination)
        report["stop_to_download_complete_ms"] = round((time.perf_counter() - stop_started) * 1000, 3)
        partial = Path(report["transfer"]["partial_path"])
        report["video"] = inspect_video(partial)
        actual = report["video"]["duration_seconds"]
        report["duration_check"] = {
            "tolerance_seconds": 0.5,
            "requested_main_duration_covered": actual >= seconds - 0.5,
            "shortfall_vs_main_plus_tail_seconds": round(max(0, seconds + tail_seconds - actual), 4),
            "matches_main_plus_tail_within_tolerance": actual >= seconds + tail_seconds - 0.5,
        }
        if not report["duration_check"]["matches_main_plus_tail_within_tolerance"]:
            print(f"DURATION WARNING: requested {seconds + tail_seconds:g}s; video contains {actual:.3f}s", flush=True, file=sys.stderr)
        partial.replace(destination)
        report["local_path"] = str(destination)
        report["stop_to_validated_clip_ms"] = round((time.perf_counter() - stop_started) * 1000, 3)
        if verify_copy:
            check = camera.download(recording["name"])
            report["repeat_download"] = check
            report["byte_identical_repeat_download"] = check["sha256"] == report["transfer"]["sha256"]
            if not report["byte_identical_repeat_download"]:
                raise MoblinError("Phone file changed between downloads")
        report["outcome"] = "complete"
        return report
    except BaseException as error:
        report["outcome"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        save()
        print(f"Report: {report_path}", flush=True, file=sys.stderr)
