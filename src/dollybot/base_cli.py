import argparse
import asyncio
import json
import signal
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dollybot.controllers.flow_base import BaseVelocity, FlowBaseController
from dollybot.drivers.base import BaseDriver, BaseMove


async def run(args):
    controller = FlowBaseController(args.url, args.device_id)
    if args.command == 'status':
        return asdict(await controller.read_identity())
    request = None if args.command == 'stop' else BaseMove(BaseVelocity(args.forward_m_s, args.left_m_s, args.yaw_rad_s), args.seconds)
    driver = BaseDriver(controller)
    interrupted = False
    stop_tasks = set()
    loop = asyncio.get_running_loop()

    def interrupt():
        nonlocal interrupted
        interrupted = True
        if controller.connected:
            task = asyncio.create_task(driver.stop())
            stop_tasks.add(task)

    report = {'operation_id': uuid4().hex, 'started_at': datetime.now(timezone.utc).isoformat(),
              'device_id': args.device_id, 'operation': args.command,
              'request': asdict(request) if request else None, 'status': 'running'}
    folder = args.output.expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (report['operation_id'] + '.json')

    def save():
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(path)

    save()
    for name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(name, interrupt)
    try:
        await controller.connect()
        if interrupted:
            raise RuntimeError('Interrupted before execution')
        if request is None:
            report['result'] = {'stop_frames_sent': await driver.stop(), 'physically_verified': False}
        else:
            report['result'] = asdict(await driver.move(request))
        report['status'] = 'cancelled' if interrupted or report['result'].get('outcome') == 'stopped' else 'completed'
        return report
    except BaseException as error:
        report.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        try:
            if stop_tasks:
                await asyncio.gather(*stop_tasks, return_exceptions=True)
            report['controller_state'] = asdict(controller.state())
            await driver.close()
        finally:
            save()
            for name in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(name)


def main():
    parser = argparse.ArgumentParser(description='Typed planar Flow Base control through the existing Pi controller')
    parser.add_argument('--url', required=True, help='Controller HTTP origin, normally through an SSH tunnel')
    parser.add_argument('--device-id', required=True, help='Expected CAN adapter ID reported by /disco')
    parser.add_argument('--output', type=Path, default=Path.home() / 'Movies/Dollybot/base-tests')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('stop')
    move = commands.add_parser('move')
    move.add_argument('--forward-m-s', type=float, default=0)
    move.add_argument('--left-m-s', type=float, default=0)
    move.add_argument('--yaw-rad-s', type=float, default=0)
    move.add_argument('--seconds', type=float, required=True)
    args = parser.parse_args()
    try:
        result = asyncio.run(run(args))
        print(json.dumps(result, indent=2))
        if result.get('status') == 'cancelled':
            parser.exit(130)
    except Exception as error:
        parser.exit(1, f'{type(error).__name__}: {error}\nMovement may have occurred; do not retry blindly.\n')
