---
name: flowbase-simulator
description: Freely drive and direct the simulated Flow Base from Kino chat. Use for any planar movement, rotation, teleport, timed path, sequence, camera-shot rehearsal, status, or stop in the browser simulator.
---

# Flow Base simulation control

Use the local helper through Kino's shell tool. This skill controls the browser simulation only; the physical base is not connected. Choose and execute the movement the user asks for without requiring preset shots or an extra confirmation. Free simulation is the default: no stage boundary, subject-clearance check, or preview speed, acceleration, distance, or turn limit is enforced. Keep Stop, manual takeover, connection ownership, and disconnect cancellation working.

The base has three planar degrees of freedom: X, Y, and yaw. It can translate in any direction while rotating. It cannot physically fly, tilt, move the camera mast, or manipulate objects; do not claim those capabilities. Teleport is a simulator setup operation.

## Start with current state

```sh
python3 __DOLLYBOT_SIM_HELPER__ capabilities
python3 __DOLLYBOT_SIM_HELPER__ status
```

If unavailable, direct the user to `__DOLLYBOT_SIM_LAUNCHER__`. If no viewer is ready, open `http://127.0.0.1:8766` and wait for “Kino bridge connected.” Keep the simulator visible during execution. Kino can have keyboard focus.

For the examples below, append the listed arguments to:
`python3 __DOLLYBOT_SIM_HELPER__`

## General movement (starts at the current pose)

- `drive --vx 1 --vy 0.5 --omega 90 --duration 4 --frame body --wait`: translate and spin together. Velocities are m/s; **CLI omega is degrees/s**. Body +X is forward and +Y is left. In `--frame world`, X/Y velocity stays aligned to the room while yaw changes.
- `move --x 2 --y -1 --yaw 450 --duration 6 --frame body --wait`: displacement relative to the current pose. Body axes are captured at the start of the move. **CLI yaw is degrees**, including full turns. Omitted axes stay unchanged.
- `move --absolute --x 8 --y -6 --yaw 90 --duration 5 --wait`: go to a world pose, including outside the original stage. Omitted axes hold their current values. Use `--easing linear` for constant interpolation or the default smooth easing.
- `rotate --degrees -720 --duration 4 --wait`: two clockwise turns in place. Positive turns are counterclockwise viewed from above.
- `pose --x -2.5 --y 0 --yaw 0 --wait`: instantly place/reset the simulated base.
- `stop`: request cancellation; check status to confirm it stopped.

Add `--reason 'Short description'` to label the movement in the browser. Use `--replace` when a new user instruction should interrupt an active command. Otherwise, wait for the current job or stop it first. A timed drive can be long-running; the user can interrupt it at any point.

## Arbitrary paths and sequences

Use `motion --json 'JSON' --wait` or `motion --file /absolute/path.json --wait`. **JSON yaw and omega use radians**; position is meters and time is seconds. Every command accepts these schemas:

```json
{"kind":"drive","vx":1,"vy":0.2,"omega":1.57,"duration":4,"frame":"body"}
{"kind":"move","x":2,"y":-1,"yaw":6.283185307179586,"relative":true,"frame":"world","duration":6,"easing":"smooth"}
{"kind":"pose","x":-2.5,"y":0,"yaw":0}
{"kind":"path","easing":"linear","waypoints":[{"t":2,"x":0,"y":0,"yaw":0},{"t":5,"x":6,"y":3,"yaw":3.141592653589793}]}
{"kind":"sequence","repeat":2,"commands":[{"kind":"move","x":1,"duration":2,"frame":"body"},{"kind":"move","yaw":1.5707963267948966,"duration":1}]}
```

Path waypoints are absolute world poses. Time is measured from the start of that path; the current pose is the implicit point at t=0. Waypoint times must increase. Yaw is unwrapped: 0 → 4π means two full turns, not zero rotation. Smooth easing stops at each waypoint; linear interpolation changes direction at waypoints. Dense linear samples can describe circles, figure-eights, spirals, or another user-specified curve.

Sequence commands execute in order, each starting where the previous ended; `repeat` repeats the entire sequence. Use a flat sequence. Requests support up to 1024 waypoints or expanded sequence commands and 128 KB of JSON. All numbers must be finite and fit numerical precision; durations must be positive except instantaneous `pose`. These are transport/computation bounds, not robot-motion limits. Split larger plans into successive jobs.

## Preset camera shots

Presets remain available, without the old motion limits by default:

- `run --kind orbit --radius 5 --sweep 720 --duration 12 --wait`
- `run --kind dolly --radius 2.5 --distance -4 --duration 3 --wait`
- `run --kind slide --distance 8 --duration 4 --fixed-heading --wait`

Presets begin at their calculated start marker, unlike general movement commands. Use a path or move if continuity from the current pose matters. Subject-facing rotation is the preset default; `--fixed-heading` holds its initial heading. Add `--constrained` only when the user requests the original bounded rehearsal mode; do not silently slow or reshape a requested free movement.

## Execution and results

Each new movement gets a fresh request ID automatically; specify `--request-id UNIQUE-UUID` when stable retries are needed. Retrying an uncertain submission uses the same ID and identical parameters. First inspect `status --job JOB-ID`. A completed/cancelled/failed ID never replays.

`--wait` waits at most 55 seconds, then reports the same pending job ID. Check that ID for longer movements; do not resubmit. Report completion only when status is `completed` with the browser-confirmed endpoint. For failures or cancellation, report `status_reason`. Do not automatically resume a cancelled or disconnected command.

This is ideal kinematic visualization. Free simulation can pass through the subject or scenery and use physically impossible speeds. Do not present it as contact-physics validation, physical robot execution, or a recorded video.
