# OM8 control and coordinated capture

Dollybot owns the Bluetooth connection. An agent requests a typed, bounded operation; it does not write motor packets. The code runs on the Mac in one process:

- `controllers/om8.py`: BLE session, DUML speed commands, device observations, serialized writes, motion deadlines and stop attempts.
- `drivers/gimbal.py`: the timed-motion interface. This is intentionally thin until calibrated trajectories are supported.
- `rig.py`: one active job, recording lead-in, movement, stop, recording tail, original-file download, and job reports.
- `agent.py`: a stdio MCP interface over the same executor.

The existing Moblin-only CLI remains available without installing gimbal or agent dependencies. The base simulator remains separate; no base hardware is controlled here.

## Setup

Use macOS, Python 3.12+, uv, and ffmpeg/ffprobe. Install only the extras you need:

```sh
uv sync --extra gimbal
```

Mount the phone securely on the powered, unfolded OM8 with room to move. Verify that it holds level and its joystick works. Keep the tracking module detached and phone Bluetooth off in Settings so another app does not hold the gimbal connection. Enable Moblin's web remote over Wi-Fi and keep its camera screen open for capture. Allow Bluetooth access for the Mac process if macOS prompts.

Supply the gimbal's CoreBluetooth UUID as `--gimbal-address`. This is Mac-specific; it is not the device's advertised name. The earlier tested Mac used `372488CB-D007-3262-1E09-B248B8C63EE9`. Supply the current Moblin URL separately. No address is hardcoded in the controller.

## Local commands

From this checkout, replacing `GIMBAL_UUID` and `PHONE_IP`:

```sh
uv run --extra gimbal dollybot-rig --gimbal-address GIMBAL_UUID status
uv run --extra gimbal dollybot-rig --gimbal-address GIMBAL_UUID move --pan-deg-s 10 --seconds 1
uv run --extra gimbal dollybot-rig --gimbal-address GIMBAL_UUID --url http://PHONE_IP take --pan-deg-s 10 --seconds 1 --lead-s 1 --tail-s 3 --verify-copy
```

Use `--tilt-deg-s` for tilt; signed values select direction. Ctrl-C or SIGTERM requests interruption and waits for cleanup. Each CLI invocation connects and disconnects; use the persistent MCP server for repeated agent operations. Do not run a second controlling client alongside it.

## Agent tools

Configure a stdio MCP-capable agent host to launch:

```sh
uv run --directory /ABSOLUTE/PATH/TO/dollybot --frozen --all-extras dollybot-agent --gimbal-address GIMBAL_UUID --url http://PHONE_IP
```

The server exposes:

| Tool | Input / result |
| --- | --- |
| `get_status` | Connection, telemetry age, and active job ID |
| `move_gimbal` | Typed motion and request ID → job ID |
| `capture_take` | Typed motion, lead/tail, copy verification and request ID → job ID |
| `get_job` | Job ID → status, result, clip path, or error |
| `stop` | Requests cancellation and immediate gimbal stop; poll the job for camera cleanup |

Example `capture_take` arguments:

```json
{
  "request_id": "ad49e452b3844f68a3da58212bd68696",
  "motion": {"pan_deg_s": 10, "tilt_deg_s": 0, "duration_s": 1},
  "lead_s": 1,
  "tail_s": 3,
  "verify_copy": true
}
```

Generate a new UUID hex ID for each intentional operation. Retain that ID on transport retries: the same request returns its original job without repeating motion, and conflicting reuse is rejected. Jobs are serialized, not queued. A second distinct operation while busy is rejected. Reports persist under `~/Movies/Dollybot/takes/jobs/`; captured clips and camera timing reports are in take subdirectories. On restart, an unfinished saved job is reported as `unknown` and never resumed automatically.

The caller polls until the job is terminal. `completed` means the software command/capture pipeline finished, not that framing is good or movement was optically verified. Review the duration warnings and motion result before passing the clip to Kino. `get_job.result.local_path` is the local file to import through Kino's separate media tools. This server does not automatically import, edit, judge, or request retakes.

A director host can connect both Dollybot MCP and Kino MCP. For Kino's shell-capable agent, the local CLI is also usable. Registering custom MCP servers inside Kino itself is not established by this implementation; it does not modify Kino configuration.

## Typed Python interface

```python
from pathlib import Path
from dollybot.controllers.om8 import BleTransport, OM8, VelocityCommand
from dollybot.rig import Rig, TakeRequest

rig = Rig(OM8(BleTransport(gimbal_uuid)), phone_url, Path.home() / "Movies/Dollybot/takes")
await rig.controller.connect()
try:
    job_id = rig.capture_take(TakeRequest(VelocityCommand(10, 0, 1)), request_id=unique_uuid_hex)
    # Poll rig.get_job(job_id); use await rig.stop() to interrupt.
finally:
    await rig.close()
```

## Boundaries and qualification

Motion is limited to one axis at a time, at most 20 degrees/second, and at most two seconds. These are commissioning limits inherited from the earlier tests, not manufacturer specifications. No absolute angles, calibrated relative angles, roll, combined-axis motion, tracking, or acceleration profiles are exposed. The reported angle tuple is experimental vendor telemetry with its sample age; it is not a validated orientation contract and does not drive a feedback loop.

A connected controller refreshes the speed command approximately every 200 ms and sends three zero-speed commands at completion/interruption. BLE writes have bounded waits. `stop_sent` means writes completed without a transport error, not a device acknowledgement or proof of physical stop. The controller cannot guarantee stopping after link loss, process kill, Mac sleep, or power loss. No reconnect automatically resumes a command. The advisory per-device process lock prevents two Dollybot processes for the same peripheral on this Mac; it cannot exclude Mimo, a different implementation, or another computer.

Moblin state confirmation is not a sensor exposure timestamp. The original tests found occasional short recordings; tail padding and file validation do not prove a specific action was captured. See [camera timing](moblin.md).

The original standalone controller was physically tested for timed pan/tilt and stopping. This refactor is tested with fake BLE, local camera fixtures, and MCP sessions; its physical acceptance is still pending. With the setup above, first check status, then a one-second pan, one-second tilt, interruption, and a coordinated take. Confirm visible motion and stop, inspect the downloaded clip, and compare the reports. Link-loss stopping requires its own supervised test before relying on it.

Protocol implementation is derived from [alkersan/om-research](https://github.com/alkersan/om-research), commit `b27c9230166346300af24cda95e487de69fddf5a`, under its retained MIT license in `controllers/vendor/LICENSE`. The vendored parser rejects undersized packets to prevent a malformed length from stalling notification handling. macOS cached-peripheral retrieval uses Bleak internals; Bleak is pinned to the tested 2.1.1 version.
