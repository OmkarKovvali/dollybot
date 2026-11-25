# OM8 control

The typed `OM8` controller owns one Bluetooth transport. `GimbalDriver` exposes bounded timed motion and stop. `VelocityCommand` has pan/tilt in degrees per second and duration in seconds. The current qualified envelope is one axis at a time, at most 20 degrees/second and two seconds. Telemetry is experimental, not a calibrated pose or exact-angle contract.

Mount the iPhone securely, unfold/power the OM8, and confirm its joystick works. Keep the tracking module detached and Moblin gimbal tracking off when using manual control. The Mac controls the gimbal directly; Moblin records over Wi-Fi. No DockKit pairing or Xcode app is required for this path.

Use the shared [localhost console and Kino service](kino-integration.md). The UI, `dollybot-client`, `dollybot-rig`, and `dollybot-agent` share one running service instead of creating competing hardware sessions.

```sh
uv run --frozen --extra gimbal dollybot-console
uv run --frozen dollybot-client connect '{"devices":["gimbal","camera"]}'
```

The console has manual pan/tilt controls. For an agent-directed recording, submit capture_take with a goal and optional pan_deg_s or tilt_deg_s, then poll get_job. Retain the request ID on retries; explicit stop interrupts both base and gimbal and initiates recording cleanup. See the integration guide for the full contract.

The controller uses Bleak on macOS, a process lock, DUML speed packets, periodic command refresh, and repeated zero-speed stop packets. The reverse-engineered protocol source retains its license in `controllers/vendor/LICENSE`. BLE send completion is not a motor acknowledgement; stop_sent is not proof of physical stop. No absolute-angle, roll, combined-axis gimbal move, tracking, or acceleration profile is exposed.
