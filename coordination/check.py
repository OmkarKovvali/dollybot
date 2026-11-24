import json
import os
import subprocess
import sys
from pathlib import PurePosixPath


def git(*args):
    return subprocess.check_output(["git", *args])


def board(revision):
    return json.loads(git("show", f"{revision}:coordination/board.json"))["tasks"]


def covers(root, path):
    return path == root or path.startswith(root + "/")


def validate(tasks):
    ids, branches, owners = set(), set(), {}
    for task in tasks:
        for key in ("id", "owner", "branch", "outcome", "check"):
            if not isinstance(task[key], str) or not task[key].strip():
                raise ValueError(f"missing {key}: {task}")
        if task["id"] in ids or task["branch"] in branches:
            raise ValueError(f"reuse of ID or branch: {task['id']}")
        ids.add(task["id"])
        branches.add(task["branch"])
        if task["state"] not in ("active", "done", "cancelled"):
            raise ValueError(f"unknown state: {task['state']}")
        paths = task["paths"]
        if not isinstance(paths, list) or not paths:
            raise ValueError("paths must be a nonempty list")
        for path in paths:
            p = PurePosixPath(path)
            if str(p) != path or p.is_absolute() or ".." in p.parts or not p.parts:
                raise ValueError(f"expected literal repository path: {path!r}")
            if task["state"] == "active":
                for root, owner in owners.items():
                    if covers(root, path) or covers(path, root):
                        raise ValueError(f"{path} overlaps {root} owned by {owner}")
                owners[path] = task["id"]


def main(base, head, branch):
    paths = {
        os.fsdecode(p) for p in
        git("diff", "--no-renames", "--name-only", "-z", f"{base}...{head}").split(b"\0") if p
    }
    ledger = "coordination/board.json"
    validate(board(base))
    if paths == {ledger}:
        validate(board(head))
        return
    if ledger in paths:
        raise ValueError("submit board changes separately from implementation")
    matches = [t for t in board(base) if t["state"] == "active" and t["branch"] == branch]
    if len(matches) != 1:
        raise ValueError(f"no active assignment on the base branch for {branch!r}")
    outside = sorted(p for p in paths if not any(covers(r, p) for r in matches[0]["paths"]))
    if outside:
        raise ValueError(f"outside {matches[0]['id']}: {outside}")


if __name__ == "__main__":
    main(*sys.argv[1:])
