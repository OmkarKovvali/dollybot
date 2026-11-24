# Working on Dollybot

Read README.md and fetch origin/main before editing. Start new work from current main on a short personal branch (Omkar uses `o/`). Use a separate worktree for concurrent agents and coordinate changes to shared interfaces directly.

Keep commits focused, with short lowercase messages. Run `make check` before pushing code changes. Only merge or push to main when the user asks. No assignment board is required.

Keep downloaded references under docs/kino, docs/i2rt, and research intact. Put runtime Python code under src/dollybot and simulator code under flowbase-sim. Never commit runtime credentials or captured clips.

Distinguish simulation, automated tests, and physical hardware verification. Simulator commands are not hardware motion commands. Do not report a physical action as successful based solely on an API acknowledgement.
