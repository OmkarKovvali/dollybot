import json
import statistics
import subprocess
from fractions import Fraction
from pathlib import Path


def inspect_video(path: Path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"ffprobe could not read the recording: {result.stderr.strip()}")
    metadata = json.loads(result.stdout)
    video = next((s for s in metadata["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise RuntimeError("Recording has no video stream")
    frames = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
                             "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=120)
    if frames.returncode or frames.stderr.strip():
        raise RuntimeError(f"Video frame validation failed: {frames.stderr.strip()}")
    times = [float(f["best_effort_timestamp_time"]) for f in json.loads(frames.stdout)["frames"]
             if "best_effort_timestamp_time" in f]
    if len(times) < 2:
        raise RuntimeError("Not enough decoded video frames")
    intervals = [b - a for a, b in zip(times, times[1:])]
    positive = [v for v in intervals if v > 0]
    if not positive:
        raise RuntimeError("Video has no increasing frame timestamps")
    median = statistics.median(positive)
    fps = lambda value: float(Fraction(value)) if value and value != "0/0" else None
    return {"width": video["width"], "height": video["height"], "codec": video["codec_name"],
            "pixel_format": video.get("pix_fmt"), "nominal_fps": fps(video.get("r_frame_rate")),
            "average_fps": fps(video.get("avg_frame_rate")), "decoded_frames": len(times),
            "timestamp_fps": round((len(times) - 1) / (times[-1] - times[0]), 5),
            "duration_seconds": float(video.get("duration") or metadata["format"]["duration"]),
            "container_duration_seconds": float(metadata["format"]["duration"]),
            "bit_rate": int(video.get("bit_rate") or metadata["format"].get("bit_rate", 0)),
            "median_frame_interval_ms": round(median * 1000, 4),
            "max_frame_interval_ms": round(max(intervals) * 1000, 4),
            "gaps_over_1_5x_median": sum(v > 1.5 * median for v in intervals),
            "nonincreasing_timestamps": sum(v <= 0 for v in intervals),
            "rotation_degrees": next((s["rotation"] for s in video.get("side_data_list", []) if "rotation" in s), 0)}
