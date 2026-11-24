# Kino Flow Base Studio

A browser-based camera-move rehearsal tool using official I2RT Flow Base geometry, extracted from the Linear Bot URDF. Kino's existing chat directs shots through a local bridge; the browser executes them and reports the result. This version has no physical robot connection and does not run a second chatbot.

## Run locally

Double-click `start-bridge.command`, or run from this directory:

```sh
node bridge/server.mjs
```

Open <http://127.0.0.1:8766> and leave it visible. Wait for **Kino bridge connected**. The launcher finds Node on PATH, with this Mac's bundled Node as a fallback. No dependency installation or build is needed. WebGL is required.

The hosted Site also has a **Connect Kino** button that attempts to reach the same local bridge. Browser local-network restrictions may prevent this; **Open local simulator** provides the same UI over a same-origin local connection. The hosted Site remains private and has no cloud command broker.

## Direct from Kino

The skill is installed on this Mac at `/Users/vinnie/Library/Application Support/Kino/skills/flowbase-simulator/SKILL.md`. In any Kino desktop chat, type `/flow` and select **/flowbase-simulator**. Settings → Skills → Local lists it as **Flowbase simulator** (`/kino:flowbase-simulator`). The editable source is `skills/flowbase-simulator/SKILL.md`; copy updates to the installed file and refresh Kino's skills catalog.

Kino can control every planar base degree of freedom (X, Y, yaw) through:

- Simultaneous translation and rotation, using body or world velocities.
- Relative displacement or absolute world poses, including multiple full turns.
- Instant pose placement, arbitrary timed paths, and repeated mixed sequences.
- Orbit, dolly, and slide presets, with optional subject-facing rotation.
- Status, completion feedback, interruption, and Stop.

Free simulation is the default in the helper and browser. Stage boundaries, subject clearance, and preview speed, acceleration, travel, radius, and turn restrictions are off. `run --constrained` opts into the original preset limits. This does not provide physical robot control, vertical motion, a gimbal, or object manipulation.

```sh
python3 bridge/kino_sim.py capabilities
python3 bridge/kino_sim.py drive --vx 1 --vy 0.5 --omega 90 --duration 4 --frame body --wait
python3 bridge/kino_sim.py move --absolute --x 8 --y -6 --yaw 90 --duration 5 --wait
python3 bridge/kino_sim.py rotate --degrees 720 --duration 4 --wait
python3 bridge/kino_sim.py pose --x -2.5 --y 0 --yaw 0 --wait
python3 bridge/kino_sim.py motion --file /absolute/path.json --wait
python3 bridge/kino_sim.py stop
```

CLI yaw/omega use degrees/degrees per second; raw JSON uses radians/radians per second. All translation is in meters. General motions start from the current pose. Presets start at a calculated marker. `motion` accepts `drive`, `move`, `pose`, `path`, and flat `sequence` schemas; see the skill for examples. Paths use absolute world waypoints with increasing times and unwrapped headings. Smooth interpolation stops at each waypoint; linear interpolation connects them directly. Requests are limited to 128 KB and 1024 waypoints or expanded sequence commands for predictable processing. Numeric values must be finite; long commands can be polled after the helper's 55-second wait returns.

The API binds to `127.0.0.1:8766`. A per-process credential is stored with restricted permissions in ignored `.runtime/bridge.json`. The helper reads it automatically. One browser owns execution. Jobs use idempotent IDs; retries retain their original start pose. Completion verifies elapsed time, position, and full unwrapped rotation. Manual takeover, Stop, disconnection, or hiding the tab cancels execution. `--replace` stops an active job before submitting its replacement.

Keep the bridge running and the preview visible. Jobs are in memory and never replay after restart. Relaunch `start-bridge.command` and reload/reconnect the preview after restarting. The server has no physical robot driver.

## Controls

- W/S: forward/back; A/D: strafe left/right; Q/E: rotate left/right, in the robot body frame.
- Hold the on-screen keys for touch/mouse driving. Release stops the preview.
- Space/Stop: cancel movement. Manual input cancels a running shot. Window blur releases manual keys; automatic shots continue while the simulator is visible, so you can type in Kino. Hiding the simulator tab cancels the shot.
- Orbit, push-in, and slide: edit a shot, then Run shot. Presets begin at their preview start marker; general Kino motions continue from the current pose. Free simulation is on by default; turn it off to restore the original preview limits.
- Drag the timeline to inspect a frame. Changing shot parameters resets the preview.
- Camera height and lens change the illustrative camera rig. The optical axis is horizontal and follows base yaw; no gimbal is modeled.
- Export shot downloads JSON with world-frame poses, timestamps, body velocities, camera assumptions, model revision, and validation results. It is explicitly marked `simulation_only` and is not a hardware execution authorization.

## Official model and sources

Source: [i2rt-robotics/i2rt, Linear Bot](https://github.com/i2rt-robotics/i2rt/tree/8c1b3ab6b6f31ae11e8b5f1e46c037d154199938/i2rt/robot_models/linearbot), pinned to commit `8c1b3ab6b6f31ae11e8b5f1e46c037d154199938`.

- `dist/assets/robot/flowbase.urdf` retains the base, root, and motor1–motor8 links and their original transforms. Lift and arm mount links are omitted.
- `dist/assets/robot/assets/` contains nine unchanged upstream STL meshes, in meters.
- `dist/assets/flowbase-visual-model.zip` is a downloadable base-only package with license and provenance.
- The full original URDF/MJCF, lift meshes, source snapshots, checksums, and a reference archive are preserved in `../research/flowbase/`.
- `dist/assets/robot/model-mapping.json` documents the original model and CAD-to-controller caster mapping.
- I2RT and Three.js are MIT licensed; license notices are shipped with their assets.

These are official CAD-derived meshes and articulated robot descriptions. No public editable STEP or Onshape assembly was found. I2RT's current public product Drive folder contains a Flow Base specification PDF; it is not substituted for a CAD assembly.

## Simulation fidelity

The simulation uses exact planar body-twist integration, I2RT's caster-rate equations, a 50 mm wheel radius and 20 mm trailing caster offset. Caster integration uses substeps no larger than 5 ms. The four pivots use the controller's ±0.2 m nominal coordinates. The original CAD transforms are retained for rendering.

Shot paths use quintic easing and sampled velocity/acceleration validation. Preview limits are 0.5 m/s, 0.8 rad/s, 0.5 m/s² and 1.2 rad/s². They are planning limits, not certified hardware limits. The subject and stage use conservative approximate clearance checks.

Free simulation bypasses the planning limits and approximate stage/subject clearance checks described above. The limits apply only when explicitly opting into constrained presets or manual preview mode.

This is kinematic previsualization. It does not model traction, wheel slip, motor dynamics, payload stability, braking distances, or contact physics. Manual release and Stop halt the simulated body immediately. The upstream MJCF has a fixed root and visual-only mesh geoms; it needs collision geometry, a free base, suitable actuators and validated inertias for a dynamics simulator. The camera mast is illustrative, not an official I2RT part.

I2RT also provides a Python/Viser preview in its full repository:

```sh
uv run examples/drive_flow_base_viser/drive_flow_base_viser.py --linearbot --sim
```

Keep `--sim` for that command: its non-simulation modes can connect to real hardware. The downloaded reference file is not a standalone installation of its dependencies.

## Validation

```sh
node --test tests/*.test.mjs
```

The automated tests cover both constrained previews and free simulation. They cover coordinate transforms, curved body integration, shot endpoints, speed and clearance rejection, manual takeover, stopping, caster integration, exported samples, idempotency, authenticated HTTP access, viewer ownership, endpoint confirmation, and disconnect/reconnect races. Browser checks cover model loading, shot playback, manual takeover, parameter validation, camera settings, source information, and responsive layouts. A real Kino chat submitted and completed a 60° orbit at 2 m over 16 s through the bridge. A plain follow-up, “Now give me a gentle push-in toward the subject,” caused Kino to choose and complete a 0.8 m dolly over 10 s; both results were confirmed by the live browser.

## Integration boundaries

`window.kinoSim` offers browser-local `getState()`, `executeShot(params)`, `stop()` and `exportShot()`. `dist/bridge-client.mjs` connects it to the authenticated local HTTP service. The service supports `GET /api/state`, `POST /api/shots`, `GET /api/jobs/:id`, and `POST /api/stop`. The Python helper is the intended interface for Kino's shell-capable agent. This does not register an arbitrary tool in every Kino model or bypass Kino's approvals.

General control uses `POST /api/motions` and `GET /api/capabilities`. `window.kinoSim.executeMotion(motion, startPose)` executes those jobs. The Python helper and installed Kino skill use these APIs.

Hardware execution still belongs in a separate local service with a watchdog and control ownership. The private Site can be used standalone without the local bridge.
