---
name: dollybot
description: Executes stationary takes and directional sliding shot presets on physical Dollybot through the persistent local rig service, imports clips into Kino, reviews them against an explicit goal, and proposes bounded retakes.
disable-model-invocation: true
---

# Dollybot cinematography

Use the running Dollybot service. It owns the Wi-Fi base, Bluetooth OM8, and Moblin camera. Never open hardware connections, restart the service, use the simulator for physical work, or send raw Bluetooth/motor commands. The web controls and this client share the same drivers and admission checks.

## Tools

If Dollybot MCP tools are available, use them. Otherwise use the shell command below; it calls the exact same service, not a separate controller:

```sh
__DOLLYBOT_CLIENT__ get_status
__DOLLYBOT_CLIENT__ connect '{"devices":["camera"]}'
```

For a take, generate one fresh UUID without hyphens (32 lowercase hexadecimal characters). Keep that request ID unchanged when retrying a lost response. Different parameters require a new ID; never replay a failed or unknown physical take automatically.

```sh
__DOLLYBOT_CLIENT__ capture_take '{"request_id":"REPLACE_WITH_NEW_32_HEX_ID","shot":{"goal":"Check framing and exposure for a stationary medium shot","seconds":3,"lead_s":1,"tail_s":3,"import_to_kino":true}}'
__DOLLYBOT_CLIENT__ get_job '{"job_id":"SAME_ID"}'
__DOLLYBOT_CLIENT__ stop
```

Poll get_job until completed, failed, cancelled, or unknown. Client exit and MCP disconnect do not cancel a submitted job. Stop is explicit and works from the UI or CLI. Do not submit extra captures while a job runs. A failed import can leave a successful local clip in result.local_path: use that clip, never recapture just to fix an import.

## Sliding shot preset

Map "sliding shot", "slide", or "left to right" to the `slide` preset. Direction is required: `left`, `right`, `forward`, or `backward`, relative to the base's forward heading, not the camera or screen. "Left to right" means `right`. If missing or ambiguous, ask which direction; never pick one silently. Invoking `/dollybot` alone does not authorize motion.

Defaults are six feet and 0.5 m/s top speed. Accept the user's distance and speed when specified; the service validates a maximum of 20 feet, 0.5 m/s, and 30 seconds of motion. Acceleration and deceleration are 0.25 m/s²; a default six-foot slide takes about 5.66 seconds, with two seconds of recording lead and three seconds of tail. Travel is estimated from timed velocity commands, not measured position. State that limitation; do not promise exact displacement.

Preview without motion:

```sh
__DOLLYBOT_CLIENT__ plan_preset '{"preset":"slide","direction":"right","distance_ft":6,"speed_m_s":0.5}'
```

After establishing the user's requested direction and current supervised clear path, connect camera and base through the service. Gimbal connection is not required for this preset. Use the user's creative goal when given; otherwise use the goal below. Execute one take, retaining its request ID:

```sh
__DOLLYBOT_CLIENT__ capture_preset '{"request_id":"REPLACE_WITH_NEW_32_HEX_ID","shot":{"preset":"slide","direction":"right","distance_ft":6,"speed_m_s":0.5,"goal":"Capture a smooth lateral slide and review framing"}}'
__DOLLYBOT_CLIENT__ get_job '{"job_id":"SAME_ID"}'
```

Replace the example direction with the requested direction. With MCP, call `plan_preset(shot=...)` then `capture_preset(shot=..., request_id=...)`. Poll the same job to completion, import, and review as below. The localhost console displays the active job and recording state; its Stop all motion control cancels the job. Never substitute a series of manual pulses or raw velocity commands.

Slides preserve Moblin's existing tracking setting and send no gimbal movement commands during normal execution. They do not establish DockKit pairing or guarantee subject tracking. Do not claim tracking works without physical confirmation. There is no orbit or automatic return to the starting position.

## Shot workflow

1. Establish the film's explicit goal, intended subject, framing, and acceptance criteria. Address the human in chat with concrete staging instructions before recording (where to stand, when to act, what line to say).
2. Read status. Connect only the necessary devices. A stationary recording needs only camera. Never stop an existing human recording just to start a job.
3. Before physical motion, establish current supervision, clear travel space, secure phone mounting, and accessible stop. Software limits are not collision avoidance. If these facts are missing, ask the human and continue with planning rather than motion.
4. Use a stationary test if camera capture has not yet been verified for this setup. Use lead and tail padding; acknowledgements and the UI timer are not sensor exposure timestamps. Compare the returned duration_check and decoded video metadata with the requested coverage.
5. For custom `capture_take` only (not `capture_preset`), motion fields are forward_m_s, left_m_s, yaw_rad_s, pan_deg_s, tilt_deg_s, motion_seconds. Base is body-relative (left positive, counterclockwise yaw positive), up to 0.1 m/s translation magnitude and 0.2 rad/s yaw. Gimbal accepts pan OR tilt, up to 20 degrees/second. Motion lasts at most 2 seconds and must fit inside seconds. Set absent motion fields to zero. These timed velocities do not guarantee a particular displacement or angle.
6. For custom `capture_take`, the service disables Moblin gimbal tracking; the slide preset preserves it. The service records, executes bounded motion, stops, downloads, validates, and imports into Kino's Dollybot takes bin. A completed job returns Kino media IDs; indexing/analysis may still be running. Use Kino's media inspection tools to review actual images/audio. Do not mistake import success for visual acceptance.
7. State accept/reject with evidence against the goal. Keep notes with job ID, media ID, quality findings, and the next proposed change. Use Kino project/chat notes as the shared record. Propose a retake with one concrete change; execute only within the user's shot/motion authorization. Avoid unlimited capture loops.
8. Assemble accepted clips in the selected Kino project. No selected project means ask the user where to edit; capture/import can still be verified independently.

## Ownership and recovery

The UI can remain open during agent takes. Its manual movement and recording controls are rejected while a take runs; Stop all motion interrupts the take and initiates recording cleanup. Closing the UI only stops its manual actions; it does not cancel an agent job.

Never interpret stop_sent or command_completed as physical verification. On uncertain motion, stop and ask the human to inspect. Persisted unfinished jobs become unknown after restart and cannot be replayed by reusing their ID. Resolve the outcome before a new take.
