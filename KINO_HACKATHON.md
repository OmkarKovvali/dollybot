# Kino Flow Base Hackathon

Kino is the director: its assistant chooses shots, reviews recorded takes, and decides how to revise them. A local executor translates Kino's decisions into velocity or position commands for an I2RT Flow Base. Creative decisions should remain in Kino.

## Browser simulation

The [Flow Base Studio](flowbase-sim/README.md) provides a 3D kinematic preview with official I2RT geometry, WASD/QE controls, orbit/push-in/slide paths, a simulated camera view, and JSON shot export. Run the static server described there to rehearse without hardware. Full official model downloads and provenance are in `research/flowbase/`; the simulator also includes a downloadable base-only URDF/STL package. This is a motion and framing preview, not a contact-physics model.

## Local API and SDK references

The public references below were downloaded on November 22, 2026 (America/Los_Angeles). These are documentation and source snapshots. No official installable Kino client SDK was located in the public documentation or package searches; the published OpenAPI specification is the available REST client-generation input.

| Reference | Local file | Purpose |
| --- | --- | --- |
| Kino OpenAPI 3.1 specification | [openapi.json](docs/kino/api/openapi.json) | Exact REST operations and request/response schemas |
| Complete Kino REST reference | [llms-full.txt](docs/kino/api/llms-full.txt) | Authentication, imports, polling, limits, and errors |
| Kino API index | [llms.txt](docs/kino/api/llms.txt) | Official reference links |
| Desktop and remote MCP | [mcp.txt](docs/kino/guides/mcp.txt) | Connection setup and supported workflow descriptions |
| Custom panels | [custom-panels.txt](docs/kino/guides/custom-panels.txt) | Experimental in-Kino UI capabilities |
| Prompting and skills | [prompting.txt](docs/kino/guides/prompting.txt) | Reusable agent instructions |
| Chat modes | [chat.txt](docs/kino/guides/chat.txt) | Kino Agent and integrated agent options |
| Kino changelog | [changelog.txt](docs/kino/changelog.txt) | Includes outside-agent prompt/reply support for Kino chats |
| Flow Base guide | [flow-base-README.md](docs/i2rt/flow-base-README.md) | Robot commands, coordinates, odometry, and hardware behavior |
| Flow Base Python client | [flow_base_client.py](docs/i2rt/flow_base_client.py) | Official client source excerpt; not a standalone installed SDK |
| Source manifest | [sources.json](docs/sources.json) | Source URLs, UTC retrieval times, byte counts, and SHA-256 hashes |

The 23 Kino guide pages are in `docs/kino/guides/`, with original HTML and extracted readable text. The original I2RT repository is [i2rt-robotics/i2rt](https://github.com/i2rt-robotics/i2rt); the saved client imports other modules and needs the full I2RT environment to run.

## Verified capabilities and open questions

- The public REST schema contains only `POST /api/v1/bins/{bin_id}/assets/import` and `GET /api/v1/imports/{import_id}`. It does not describe robot control, project editing, or chat endpoints.
- Kino's desktop MCP endpoint is `http://127.0.0.1:45680/mcp`. The app must be open. Discover actual tool names and input schemas from the running server rather than guessing them.
- Kino's November changelog states that outside agents can send prompts to Kino chats and read replies. The exact tools, structured-output behavior, and availability in the installed build still need verification.
- Public docs do not establish that Kino Agent can register an arbitrary custom robot tool, or that a custom panel can directly call a local robot service. Verify those extension points before depending on them.
- Custom panels are experimental. They can read project context, show media/takes, and edit projects; they are a candidate for displaying Kino's shot decisions and take history.
- The REST import preview documents four new imports per organization per rolling hour, a 2 GiB file limit, and transfers that may start within one hour. Verify local desktop ingest for the live demo.
- The saved Flow Base client exposes velocity commands and odometry reads, with local/global command frames. It does not expose a base-position target method. Use an existing position controller if supplied, or build trajectory following over velocity commands.
- FlowBaseClient repeatedly sends its last command from a background thread. The executor needs its own move deadline and stop behavior; an assistant pause alone will not stop that heartbeat. Wheel odometry drifts, so repeatability needs measurement.

## Suggested parallel work

These are proposed work areas, not already-running agents or completed implementations. Agree on the shot request and execution-result contract before implementing both ends. Keep downloaded references intact and place project code outside `docs/`.

| Area | Suggested ownership | First deliverable |
| --- | --- | --- |
| Kino integration | `kino_bridge/` | Discover the available tools and prove Kino's own chat can produce a shot request that reaches a mock executor. A relay transports decisions; Kino makes them. |
| Flow Base execution | `dolly_executor/` | Build a simulated executor for an agreed shot contract, then map it to the actual robot interface, bounded trajectories, telemetry, and stop behavior. |
| Kino panel and take workflow | `kino_panel/` | Prototype an in-Kino view of the requested shot, Kino's reason, execution status, and resulting take. Verify panel communication capabilities. |

Suggested shared contract fields: request ID, shot ID, plan version, decision reason, coordinate frame, path or target poses, duration, and orientation. Execution results should associate the request with its status, actual trajectory, recording path, and timing. This contract is project design, not an official Kino API schema.

## First demo milestone

Give Kino a brief or rough cut. Kino requests a shot, the dolly records it, and the footage returns to Kino. Kino evaluates the result and either keeps it or changes the next shot. Start with one simple move and one revision so the causal chain from Kino's decision to robot action is visible.
