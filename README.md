# Dollybot

An agent-directed camera dolly: Kino plans and reviews shots, an iPhone records them, and a motorized base and gimbal move the camera.

## What works today

- **iPhone capture:** start and stop Moblin from the Mac, download the original clip, and measure timing, resolution, and FPS. Tested on an iPhone 14 Plus.
- **Motion rehearsal:** a browser-based Flow Base simulator with a local bridge that Kino can control. It supports driving, turns, orbits, push-ins, and slides.
- **Base access:** a [typed Flow Base controller and bounded-move driver](docs/base.md) for the existing Pi service, with a standalone CLI.
- **References and CAD:** Kino and I2RT documentation, robot geometry, and camera-rig research.

The base and OM8 controllers support bounded physical motion. Moblin records and downloads original clips. The simulator does not move hardware; the automatic Kino review/retake loop remains separate work.

## Kino integration

The [Kino integration guide](docs/kino-integration.md) connects the installed Kino agent through a skill/CLI or thin MCP client to the same persistent service that owns the localhost controls. The `slide` preset records a linear move in a required direction (left/right/forward/backward), defaults to six feet at up to 0.5 m/s with ramps, and preserves Moblin tracking. Distance is estimated from timed velocity. Takes have explicit goals, bounded optional base/gimbal motion, persistent request IDs, original-clip download, and optional Kino import. The service owns hardware; clients never open their own sessions.

## Local control screen

```sh
uv run --frozen --extra gimbal dollybot-console
```

Open <http://127.0.0.1:8767>. Connect the base, Bluetooth gimbal, and Moblin from the same screen. The phone URL is editable. Base address, hardware ID, gimbal address, output folder, and port are CLI options (`--help`). Current defaults are the commissioned local rig; Wi-Fi addresses can change.

Hold Shift + WASD to drive, Shift + Q/E to rotate, or hold the on-screen direction controls. Gimbal buttons pan/tilt at 10 degrees/second. Each hold is limited to two seconds; release and press again to continue. Space, key/pointer release, lost focus, or a stale browser heartbeat stops motion. Close other hardware clients first. Only one browser connection owns this console; the base's local lock does not exclude unrelated clients.

Start recording, then Stop & save downloads the original clip to `~/Movies/Dollybot/console/` and reports resolution, frame rate, and transfer timing. A recording already active when connecting is left running; stopping it does not guess which file to download. Console-started recordings are stopped and collected on browser disconnect when the server and phone remain available. A server crash cannot guarantee camera cleanup. The UI timer is elapsed time observed by this screen, not a sensor timestamp. Status badges reflect the latest command response, not continuous device health monitoring.

The server binds only to loopback and checks browser origin/host. It reuses the typed base and gimbal drivers and the Moblin adapter. Automated tests exercise stale input, motion limits, stop failure isolation, and watchdog behavior alongside the existing driver tests. Connection success does not constitute physical motion acceptance.

## Record from your iPhone

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and ffmpeg/ffprobe on your PATH.

```sh
uv sync --frozen
uv run dollybot --url http://PHONE_IP status
uv run dollybot --url http://PHONE_IP record --seconds 10 --verify-copy
```

On the phone, open **Moblin → Settings → Remote control → Web**, enable it, and use the Wi-Fi address under **URLs** in place of `PHONE_IP`. Keep Moblin on its camera screen. Use a trusted network; its web remote has no authentication or encryption.

Clips and timing reports go to `~/Movies/Dollybot/moblin-tests/`. Downloads preserve the original encoded file. In the five-take hardware benchmark, the median stop-to-downloaded-clip time was about **410 ms**, at **1080p/30 FPS**. Some recordings were about two seconds shorter than requested, so timing acknowledgements do not prove that all intended frames were captured.

See the [camera guide](docs/moblin.md) for options, timing definitions, and limitations, and the [benchmark](docs/benchmarks/2026-11-23.json) for measurements.

## Rehearse moves with Kino

Requires Node.js 22+; the simulator needs no npm dependencies or build step.

```sh
node flowbase-sim/bridge/server.mjs
```

Open <http://127.0.0.1:8766> and keep the simulator visible. In another terminal, install the Kino skill for this checkout:

```sh
python3 scripts/install_kino_skill.py
```

Refresh Kino's local skills and select **flowbase-simulator** in its chat. The [simulator guide](flowbase-sim/README.md) explains commands and behavior. To inspect the bridge directly:

```sh
python3 flowbase-sim/bridge/kino_sim.py status
```

## Repository

| Path | Contents |
| --- | --- |
| `src/dollybot/` | Camera adapter, gimbal controller/driver, shot executor, CLI, MCP tools, and media validation |
| `tests/` | Camera adapter tests with local HTTP/WebSocket fixtures |
| `flowbase-sim/` | Browser simulator, local Kino bridge, skill, and simulator tests |
| `scripts/` | Local setup helpers |
| `docs/moblin.md` | Phone setup, commands, and recording limitations |
| `docs/benchmarks/` | Recorded hardware measurements |
| `docs/kino/`, `docs/i2rt/` | Downloaded vendor references |
| `research/` | CAD, models, and research artifacts |

[Project notes](KINO_HACKATHON.md) preserve the original architecture research and open questions; they are not a list of completed integrations.

## Development

Start from current `main`, use a short personal branch such as `o/capture`, and keep changes focused. Coordinate directly when changing a shared interface. No assignment board or special branch-import workflow is required.

Run both suites from the repository root:

```sh
make check
```

This installs optional test dependencies and runs the Python camera/gimbal/MCP tests and Node simulator tests. It needs uv, Python 3.12+, ffmpeg/ffprobe, Node.js 22+, and make. Tests use local fixtures and simulated motion; physical hardware checks remain separate.
