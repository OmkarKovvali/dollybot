# Kino and the shared rig service

Run one hardware-owning process:

```sh
uv run --frozen --extra gimbal dollybot-console
```

The UI remains at http://127.0.0.1:8767. Base, gimbal, and Moblin connections belong to this process. API clients use `ws://127.0.0.1:8767/api`; they do not open Bluetooth, CAN, or phone connections. The endpoint binds to loopback, rejects browser Origin headers, and admits one agent take at a time. This is a local trusted-user interface, not a remotely authenticated service.

## Kino setup

```sh
python3 scripts/install_dollybot_skill.py
```

This installs `dollybot/SKILL.md` under Kino's local skills directory and embeds the absolute checkout path. Refresh Kino skills and select Dollybot. If skill discovery is unavailable, ask Kino to read the installed file explicitly. Its shell command uses the same persistent service as the UI.

For an MCP-capable agent host, configure a stdio server with executable `uv` and arguments:

```json
["run", "--frozen", "--project", "/absolute/path/to/dollybot", "--extra", "agent", "dollybot-agent"]
```

`dollybot-agent` is a thin MCP client of the service. Starting/stopping it does not connect/disconnect hardware or cancel jobs. Tools are get_status, connect, capture_take, get_job, and stop. `dollybot-client` exposes the same operations as JSON CLI requests; `dollybot-rig` is an alias for this client. The former standalone rig CLI interface is replaced. Direct diagnostic base/camera CLIs remain available but must not run alongside an owning service.

Kino's MCP server is the opposite direction: Dollybot calls `addMediaToKino` at `http://127.0.0.1:45680/mcp` after capture. Keep the Kino desktop app open. An import result returns media IDs, not proof that analysis or editing is complete. A local import can trigger Kino's normal proxy/analysis workflow.

## Requests

```sh
uv run --frozen dollybot-client get_status
uv run --frozen dollybot-client connect '{"devices":["camera"]}'
uv run --frozen dollybot-client capture_take '{"request_id":"0123456789abcdef0123456789abcdef","shot":{"goal":"Check a stationary medium shot for framing and exposure","seconds":3,"lead_s":1,"tail_s":3,"import_to_kino":true}}'
uv run --frozen dollybot-client get_job '{"job_id":"0123456789abcdef0123456789abcdef"}'
uv run --frozen dollybot-client stop
```

Generate a new 32-character lowercase hexadecimal request ID for each intentional take. Keep the same ID and parameters when checking/retrying a lost submission response. Reusing it returns the existing job; different parameters are rejected. Interrupted persisted jobs become unknown, never replayed.

A take has a required goal, main recording duration (0.1–30 seconds), lead/tail (0–10 seconds each), optional base velocities and pan OR tilt, and motion duration (at most two seconds, within the main interval). Base translation magnitude is at most 0.1 m/s, yaw 0.2 rad/s; gimbal speed is at most 20 degrees/second. Motion remains open-loop timed velocity; no angle/distance guarantee or collision avoidance is implied. Only supervised movement within clear space is qualified.

The service checks admission, disables Moblin tracking, starts recording, executes the lead/motion/main/tail sequence, stops recording, downloads and validates the original file, and optionally imports it into the Dollybot takes bin. Base and gimbal motion run concurrently through their respective drivers. If either motion fails, both receive stop attempts and camera cleanup runs.

## Ownership, stopping, and recovery

Manual UI actions cannot interrupt an active agent take except through explicit Stop all motion/Space. The UI's key release, blur, and watchdog stop only manual motion. Closing the UI or agent client does not cancel a submitted take; explicit stop signals cancellation and stops both drivers. Poll the job until cleanup finishes.

A manual recording blocks agent admission. A phone recording already running is rejected by capture without stopping it. A failed/uncertain recording start triggers a stop attempt. Failed import preserves the successful capture result/path; do not recapture to retry an import. Import has no exactly-once guarantee if the response is lost, so inspect Kino media before retrying manually.

Jobs live under the selected output directory's `jobs/`, clips and acquisition reports under sibling take directories. The CLI defaults to `~/Movies/Dollybot/console`. Failed/cancelled acquisitions retain their capture reports, but a cancelled take is not automatically imported or accepted. A process crash or power loss can leave recording/device outcomes unknown; the Pi's existing deadman is still the final network-loss timeout for base targets.

UI elapsed time and recording acknowledgements do not establish sensor timing. Inspect `duration_check`, frame metadata, and the actual footage. A returned Kino media ID is the input to review, not an automatic accept/reject result. The Kino skill directs goal-based review and human staging; no unbounded autonomous retake loop is installed.

## Validation

Tests cover shared admission, duplicate requests, unknown jobs after restart, motion bounds, simultaneous drivers, stop during lead, import failure with clip preservation, API/browser disconnect independence, and thin MCP proxy behavior. Hardware and Kino checks are recorded separately from simulated tests.

### Live acceptance — November 24, 2026

Kino's installed Codex agent loaded the local Dollybot skill, called the service through the shell client, submitted stationary job `81ab64f029c64d5fa9b3c025e9128e70`, polled it to completion, and received Kino media ID `7928be89-f68b-40f1-8906-5aa3794d1461`. Base, gimbal, and camera were connected; no motor movement was requested. This verifies the skill/shell route. The thin MCP proxy passes protocol tests; custom MCP registration inside Kino is not claimed.

The original HEVC file was 1920×1080, 30 FPS, 177 decoded frames, 5.943 seconds of video, with no detected frame-timing gaps. Requested lead/main/tail was 1/3/3 seconds; actual duration fell 1.057 seconds short of the full seven seconds. Download took 6.714 seconds; stop-to-validated clip was 8.131 seconds. The returned duration warning is preserved.

Initial testing exposed an expired idle Moblin WebSocket before recording. The adapter now has one receiver thread that answers keepalive pings and dispatches responses while idle or downloading; commands remain serialized. A live idle test and regression test verify this behavior. UI recording state is published immediately on confirmed stop, before file transfer.
