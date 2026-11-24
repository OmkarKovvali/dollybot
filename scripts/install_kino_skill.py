import argparse
from pathlib import Path
import shlex


def main():
    parser = argparse.ArgumentParser(description="Install the Kino simulator skill for this checkout")
    parser.add_argument("--destination", type=Path, default=Path.home() / "Library/Application Support/Kino/skills/flowbase-simulator")
    parser.add_argument("--force", action="store_true", help="Replace an existing skill")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    simulator = root / "flowbase-sim"
    source = simulator / "skills/flowbase-simulator/SKILL.md"
    content = source.read_text().replace(
        "__DOLLYBOT_SIM_HELPER__", shlex.quote(str(simulator / "bridge/kino_sim.py"))
    ).replace(
        "__DOLLYBOT_SIM_LAUNCHER__", shlex.quote(str(simulator / "start-bridge.command"))
    )
    target = args.destination.expanduser() / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("w" if args.force else "x") as output:
            output.write(content)
    except FileExistsError:
        parser.error(f"{target} already exists; use --force to replace it")
    print(f"Installed {target}")
    print("Refresh Kino's local skills and select flowbase-simulator.")


if __name__ == "__main__":
    main()
