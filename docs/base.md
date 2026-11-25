# Flow Base controller and driver

Dollybot talks to the existing controller on the robot's Pi. The Pi owns CAN and motor control; the Mac sends body-frame velocity commands over its `/velocity` WebSocket. This change does not install a replacement motor service or modify the Pi.

## Layers

- `controllers/flow_base.py`: immutable `BaseVelocity`, `BaseIdentity`, and `BaseState`; hardware identity/readiness lookup; one WebSocket connection; binary encoding; and an advisory local process lock keyed by hardware ID.
- `drivers/base.py`: `BaseMove` and `BaseMoveResult`; bounded movement, command refresh, interruption, and stop cleanup.
- `base_cli.py`: `status`, `move`, and `stop` commands, with JSON reports for physical operations.

Forward and left are meters/second in the robot's body frame. Positive yaw is counterclockwise, in radians/second. These are velocity requests, not measured travel distances or absolute poses. The wire packet is four little-endian float32 values: forward, left, yaw, lift. Dollybot always sends zero for lift.

The controller contract accepts ±0.5 m/s per translation axis and ±1.57 rad/s yaw. The driver deliberately has smaller commissioning limits: translation magnitude at most 0.1 m/s, yaw at most 0.2 rad/s, and duration at most two seconds. These are software test limits, not payload-dependent safety ratings.

## Connection

Use the known SSH route to the Pi and forward its IPv4 controller port. For direct Ethernet with a scoped IPv6 address, the tested tunnel form is:

```sh
ssh -6 -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes \
  -L '[::1]:18080:127.0.0.1:8080' \
  robot@PI_LINK_LOCAL_IPV6%MAC_ETHERNET_INTERFACE -N
```

Replace the host and interface with the current Pi and Mac Ethernet link. Keep the tunnel open. Enter the existing password at the SSH prompt, or use your approved SSH identity; never embed credentials in commands, configuration, or this repository. IPv6 SSH uses an IPv6 local listener here, so the controller URL is `http://[::1]:18080`.

Before the first movement of a session, check `base-control.service`, CAN error counters, recent motor-control errors, and other established connections to port 8080 through SSH. The `/disco` ready flag alone cannot establish motor-loop health. Never start another controller alongside the existing service. Resolve ownership with any other operator before moving; the Pi service itself does not enforce exclusive control.

## Commands

Use the expected CAN-adapter hardware ID from the confirmed robot. Reading `/disco` provides the advertised identity; compare it with the intended base before authorizing movement. All commands require that expected ID rather than silently accepting whatever device answers.

```sh
uv sync --frozen
uv run dollybot-base --url 'http://[::1]:18080' --device-id DEVICE_ID status
uv run dollybot-base --url 'http://[::1]:18080' --device-id DEVICE_ID move --forward-m-s 0.08 --seconds 1
uv run dollybot-base --url 'http://[::1]:18080' --device-id DEVICE_ID move --left-m-s 0.05 --seconds 1
uv run dollybot-base --url 'http://[::1]:18080' --device-id DEVICE_ID move --yaw-rad-s 0.1 --seconds 1
uv run dollybot-base --url 'http://[::1]:18080' --device-id DEVICE_ID stop
```

`status` is read-only and does not open the motion feed. `move` refreshes the velocity approximately every 50 ms and then sends six zero frames. `stop` sends zero frames through a new session; it cannot take over an already locked Dollybot session. Interrupt the owning CLI with Ctrl-C/SIGTERM, or call its driver's `stop()` from the controlling process.

Move/stop reports are saved under `~/Movies/Dollybot/base-tests/`. `--output` selects another directory. Each CLI invocation is a new operation, so do not blindly rerun a motion after an uncertain result. There is no automatic reconnect, replay, distance estimation, or pose feedback. A report left `running` after a crash is an unfinished operation, not authorization to repeat it.

## Python

```python
from dollybot.controllers.flow_base import BaseVelocity, FlowBaseController
from dollybot.drivers.base import BaseDriver, BaseMove

controller = FlowBaseController(base_url, expected_id=device_id)
driver = BaseDriver(controller)
await controller.connect()
try:
    result = await driver.move(BaseMove(BaseVelocity(forward_m_s=0.08), duration_s=1))
finally:
    await driver.close()
```

These classes share the same asyncio model as the OM8 controller. A shot executor can own both drivers and coordinate them with the Moblin capture workflow. This base-only change does not merge or modify the separate gimbal PR or expose new MCP tools.

## Stop and failure semantics

The existing Pi controller zeroes targets 250 ms after its last accepted command. This deadman belongs on the Pi, where losing the Mac/network does not remove the timeout. The actual stop still depends on the Pi loop and motor system functioning; physical braking distance is not measured here.

The Mac driver stops refreshing when its requested duration expires, sends zero frames during cleanup, and rejects a second operation while active or stopping. A command-refresh gap over 150 ms aborts further nonzero sends instead of resuming an interrupted stream. The send wait is bounded. Scheduling and network delays can affect actual timing; this is not hard real-time control.

The velocity feed provides no application acknowledgements or odometry. `command_completed`, `velocity_frames_sent`, `stop_frames_sent`, and `stop_sent` describe software/transport operations. They do not prove physical motion, physical stop, achieved displacement, or motor health. `physically_verified` remains false in automatically generated results. An exception can follow partial physical movement.

The process lock prevents cooperating Dollybot processes on this Mac from controlling the same hardware ID through different URL aliases. It cannot exclude other computers or unrelated clients. SSH is a connection/administration mechanism; the controller and driver never store or handle SSH passwords.

## Validation

`make check` runs base transport/driver tests, existing Moblin tests, and simulator tests. Base tests use a local HTTP/WebSocket fixture and cover identity mismatch, not-ready states, binary layout, refresh/stop ordering, interruption, disconnects, duplicate owners, and a stalled command stream. No Pi or physical robot is contacted by automated tests.

Live read-only validation on November 24, 2026 reached the confirmed Pi over Ethernet SSH and verified the expected hardware identity, `ready: true`, `lift: false`, an active service with zero restarts, no CAN error counters, and no other controller connection at inspection time. Fresh checks and supervision are required for physical trials. The typed driver's motion and combined base/gimbal/Moblin acceptance are recorded separately when performed.
