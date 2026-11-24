import argparse
import json
import signal
from pathlib import Path

from dollybot.adapters.moblin import Moblin
from dollybot.capture import capture


def main():
    parser = argparse.ArgumentParser(description="Dollybot camera control")
    parser.add_argument("--url", required=True, help="Moblin web remote address")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("stop")
    record = commands.add_parser("record")
    record.add_argument("--seconds", type=float, default=10)
    record.add_argument("--trials", type=int, choices=range(1, 6), default=1)
    record.add_argument("--output", type=Path, default=Path.home() / "Movies" / "Dollybot" / "moblin-tests")
    record.add_argument("--verify-copy", action="store_true", help="Re-download to a hash and verify unchanged bytes")
    record.add_argument("--tail-seconds", type=float, default=0, help="Keep recording after the main interval; 3 seconds is a conservative starting point")
    args = parser.parse_args()

    def interrupted(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        with Moblin(args.url) as camera:
            if args.command == "status":
                print(json.dumps(camera.status(), indent=2))
            elif args.command == "stop":
                print(json.dumps(camera.stop_recording(), indent=2))
            else:
                for _ in range(args.trials):
                    result = capture(camera, args.seconds, args.output, args.verify_copy, args.tail_seconds)
                    print(json.dumps(result, indent=2), flush=True)
    except KeyboardInterrupt:
        parser.exit(130, "Interrupted; recording stop was attempted for any take we started.\n")
    except Exception as error:
        parser.exit(1, f"{type(error).__name__}: {error}\nCheck the phone's recording state if a command timed out.\n")
