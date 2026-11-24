# Dollybot

## Kino Hackathon project

The complete project snapshot is included here: [project notes](KINO_HACKATHON.md), [Flow Base simulator and Kino bridge](flowbase-sim/README.md), API reference snapshots in `docs/`, and Flow Base / Unitree camera-rig CAD research in `research/`.

Start the simulator with `cd flowbase-sim && node bridge/server.mjs`, then open <http://127.0.0.1:8766>. The bridge runs on the same computer as Kino. The local Kino skill includes machine-specific paths; adjust those paths when setting up another machine. No physical robot is connected by this simulator.

Runtime credentials, caches, logs, and simulator QA screenshots are excluded. Embedded tokens in three downloaded HTML reference pages were redacted; their original provenance hashes still describe the original downloads.

## Start a build session

Pick a human coordinator for the session. Two people can split recorder and playback, with one also coordinating. A third can own the demo or integration tests. Agree on one demo action and commit a small shared interface or example before assigning dependent work. For example, both recorder and playback can build against the same sample camera-command log.

1. **Coordinator:** Fetch main and check the [board](coordination/board.json), merged work, and open PRs for the proposed behavior. Reuse an existing card for the same outcome. Put each new assignment in a board-only PR and merge it before agents begin. Only the coordinator merges. Board changes go through the same queue, one at a time.
2. **Each teammate:** Clone the repo, fetch main, and start the exact assigned branch. For another agent on the same laptop, give it a separate worktree. Run the agent from its assigned directory.
3. **Each agent:** Implement one card, run its acceptance check, and open one PR. If a shared file or interface needs changing, ask its owner. The coordinator can split off a prerequisite or revise the board before work resumes.
4. **Coordinator:** Review the handoff, update the branch against current main, verify the reviewed commit and run the combined demo. Merge one PR at a time. Mark its card done in a board-only PR before assigning follow-up work. Keep finished cards searchable.

### Assign work

Add entries to the board's `tasks` array. This example is illustrative; the initial board is empty.

```json
{
  "id": "record-command",
  "state": "active",
  "owner": "alex",
  "branch": "alex/record-command",
  "outcome": "Append one timestamped camera command to the session log",
  "paths": ["src/recorder", "tests/test_recorder.py"],
  "check": "python3 -m unittest discover -s tests -p test_recorder.py"
}
```

Give playback its own behavior, source directory, and tests. Paths are literal files or directory trees. Include any new tests and fixtures in the assignment. Keep shared schemas, dependency manifests and lockfiles under one owner when they need edits. To hand over a stalled task, have the previous owner push their last commit and stop. Update the owner on the existing card and have the successor resume the same branch at that commit. Mark abandoned work `cancelled`.

### Start an assigned agent

```sh
git clone https://github.com/OmkarKovvali/dollybot.git
cd dollybot
git fetch origin
git switch -c alex/record-command origin/main
```

Replace the example branch with yours. For a second agent in an existing clone, use `git worktree add -b NAME ../dollybot-second origin/main`. For a handover, fetch and check out the existing remote branch.

Paste this into each agent session:

> Read AGENTS.md. My owner name is ___ and my assigned branch is ___. Read the card from origin/main. Tell me the outcome, owned paths and acceptance check. Check for an existing implementation, then implement the card and prepare a PR. Ask the coordinator if the scope needs to change.

### Hand off and merge

After committing, run the card's check and the scope check from your feature branch:

```sh
git fetch origin
git show origin/main:coordination/check.py > "$(git rev-parse --git-path dollybot-scope.py)"
python3 "$(git rev-parse --git-path dollybot-scope.py)" origin/main HEAD "$(git branch --show-current)"
git rev-parse HEAD
```

Put the card ID, user-visible outcome, commit SHA, exact check command and result in the PR. List any hardware checks still pending. The coordinator compares the outcome with current main and other PRs, reruns the acceptance check on the reviewed SHA, then tests it together with current main. Repeat verification after any new commit.

### What the scope check enforces

The GitHub Actions job **Task scope** rejects reused card IDs or branch names, overlapping active paths (including parent/child directories), unassigned feature branches, edits outside owned paths, and PRs that mix board edits with implementation. Renames count as touching both paths. Humans review behavioral overlap because two implementations in different directories can both pass this check. For GitHub-enforced merges, configure main to require pull requests, the up-to-date **Task scope** check, and restricted bypass permissions.

Workflow adapted from section 6 of [Sin Liang Lee’s HackMIT write-up](https://www.sinlianglee.com/writing/hackathon-workflow).
