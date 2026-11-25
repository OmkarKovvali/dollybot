import argparse
import asyncio
import json
import signal
from pathlib import Path

from dollybot.controllers.om8 import BleTransport, OM8, VelocityCommand
from dollybot.rig import Rig, TakeRequest


async def run(args):
    rig = Rig(OM8(BleTransport(args.gimbal_address)), args.url, args.output)
    loop = asyncio.get_running_loop()
    stop_tasks = set()
    interrupted = False

    def stop():
        nonlocal interrupted
        interrupted = True
        task = asyncio.create_task(rig.stop())
        stop_tasks.add(task)
        task.add_done_callback(stop_tasks.discard)

    for name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(name, stop)
    try:
        await rig.controller.connect()
        if interrupted:
            raise RuntimeError('Interrupted before execution')
        if args.command == 'status':
            print(json.dumps(rig.get_status(), indent=2))
            return
        motion = VelocityCommand(args.pan_deg_s, args.tilt_deg_s, args.seconds)
        job = rig.capture_take(TakeRequest(motion, args.lead_s, args.tail_s, args.verify_copy)) if args.command == 'take' else rig.move_gimbal(motion)
        print(json.dumps({'job_id': job}), flush=True)
        while rig.get_job(job)['status'] == 'running':
            await asyncio.sleep(0.1)
        result = rig.get_job(job)
        print(json.dumps(result, indent=2))
        if result['status'] != 'completed':
            raise RuntimeError(f"Job {result['status']}: {result.get('error', '')}")
    finally:
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        await rig.close()
        for name in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(name)


def main():
    parser = argparse.ArgumentParser(description='Bounded OM8 movement and coordinated Moblin capture')
    parser.add_argument('--gimbal-address', required=True)
    parser.add_argument('--url', default='', help='Moblin web remote; required for take')
    parser.add_argument('--output', type=Path, default=Path.home() / 'Movies/Dollybot/takes')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    for name in ('move', 'take'):
        command = commands.add_parser(name)
        command.add_argument('--pan-deg-s', type=float, default=0)
        command.add_argument('--tilt-deg-s', type=float, default=0)
        command.add_argument('--seconds', type=float, required=True)
        if name == 'take':
            command.add_argument('--lead-s', type=float, default=1)
            command.add_argument('--tail-s', type=float, default=3)
            command.add_argument('--verify-copy', action='store_true')
    args = parser.parse_args()
    if args.command == 'take' and not args.url:
        parser.error('--url is required for take')
    try:
        asyncio.run(run(args))
    except Exception as error:
        parser.exit(1, f'{type(error).__name__}: {error}\n')
