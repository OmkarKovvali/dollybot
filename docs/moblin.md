# Moblin camera adapter

The Moblin adapter remotely starts and stops an iPhone recording, retrieves the original MP4, and measures control and transfer timing. It does not move the gimbal or base.

## Setup

Requires Python 3.12+, uv, and ffmpeg/ffprobe. The only application Python dependency is the pinned `websockets` library.

```sh
uv sync --frozen
```

On the phone, open Moblin → Settings → Remote control → Web, enable it, and copy a reachable Wi-Fi address from URLs. Return to the camera screen and leave Moblin open. Use the address shown by your phone; `127.0.0.1` would refer to the Mac when used by this program. Moblin's web remote has no authentication or encryption; keep it on a trusted network.

## Use

```sh
uv run dollybot --url http://10.2.0.181 status
uv run dollybot --url http://10.2.0.181 record --seconds 10 --verify-copy
uv run dollybot --url http://10.2.0.181 record --seconds 10 --trials 3
uv run dollybot --url http://10.2.0.181 record --seconds 10 --tail-seconds 3
uv run dollybot --url http://10.2.0.181 stop
```

Each take saves `original.mp4` and `report.json` under `~/Movies/Dollybot/moblin-tests/<take-id>/`. Use `--output` to choose another directory. No phone recordings are deleted, and existing Mac files are not overwritten.

```python
from pathlib import Path
from dollybot.adapters.moblin import Moblin
from dollybot.capture import capture

with Moblin("http://10.2.0.181") as camera:
    report = capture(camera, seconds=10, output=Path.home() / "Movies/Dollybot",
                     verify_copy=True, tail_seconds=3)
```

The adapter refuses to start if the phone is already recording or its recording state is unknown. A lost start acknowledgement still triggers a stop attempt; a failed stop reconnects once and retries. Ctrl-C and SIGTERM attempt cleanup. A dead process, force kill or unreachable phone cannot guarantee remote stopping; the phone remains the fallback. Use one controlling client during a take.

## What the measurements mean

- `start.ack_ms` / `stop.ack_ms`: command send to matching application response.
- `state_confirmed_ms`: command send to observed recording state. This is not a sensor exposure timestamp or proof that the first frame was saved.
- `stop.total_ms`: complete stop attempt including a reconnect if needed; `reconnected` distinguishes that case from an ordinary stop response.
- `stop_to_file_listed_ms`: stop command to observing the new filename, including network and polling time. It is not an exact internal finalization measurement.
- `transfer.download_ms`: HTTP request through completion of the original-file copy, including local writes.
- `stop_to_download_complete_ms`: stop command through completion of that copy.
- `stop_to_validated_clip_ms`: includes ffprobe's full video-frame decode and validation.
- `video`: actual coded dimensions, codec, nominal and average FPS, decoded-frame timestamp cadence, frame count and duration.
- `duration_check`: flags a video more than 0.5 seconds shorter than the requested interval. A complete transfer may still contain a short recording; review this separately from `outcome`.

`--verify-copy` downloads the same phone file again to a SHA-256 digest without saving another copy. Matching hashes establish identical server-file bytes across the two reads. The adapter never transcodes. Preserving the encoded file preserves its resolution and FPS; it does not prove sensor-level frame completeness, absence of duplicated images, or performance relative to a manually started recording.

On the first hardware benchmark, one requested 10-second recording contained about 8 seconds; three subsequent recordings contained about 10 seconds. A 10-second recording plus a 3-second tail contained about 12 seconds. Moblin's current upstream recorder emits two-second MP4 segments. Segment handling is a possible explanation, not a confirmed cause on the installed app. The adapter reports this difference and supports explicit tail padding. Do not claim frame-accurate shot timing from recording-state acknowledgements or that a duration check proves a particular action was captured. Measure optical timing separately before synchronizing critical action.

## Tests

```sh
uv run python -m unittest discover -s tests -v
```

Tests use local HTTP and WebSocket servers plus an ffmpeg-generated fixture. They cover the end-to-end transfer, decoded FPS, file hashes, existing-recording protection, missing acknowledgements, stop reconnection, ambiguous files and truncated downloads. Hardware recordings are a separate manual integration check.

## Protocol references

- [Moblin web server and download routes](https://github.com/eerimoq/moblin/blob/main/Moblin/RemoteControl/RemoteControlWeb.swift)
- [Moblin web remote request format](https://github.com/eerimoq/moblin/blob/main/WebRemoteControlFrontend/src/utils.ts)
- [Moblin recorder](https://github.com/eerimoq/moblin/blob/main/Moblin/Media/HaishinKit/Media/Recorder.swift)

The adapter discovers the WebSocket port through `/js/config.mjs`, correlates JSON request IDs, sends `setRecord`, confirms `getStatus`, identifies the new recording through `/recordings.json`, and retrieves `/recordings/<encoded-filename>`. These are Moblin's web-remote interfaces, not a separately versioned public API.
