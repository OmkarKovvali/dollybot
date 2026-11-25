import argparse
import asyncio
import json
import math
import time
import signal
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path
from uuid import uuid4

from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

from dollybot.adapters.moblin import Moblin
from dollybot.controllers.flow_base import BaseVelocity, FlowBaseController
from dollybot.controllers.om8 import BleTransport, OM8, VelocityCommand
from dollybot.drivers.base import BaseDriver, BaseHold
from dollybot.drivers.gimbal import GimbalDriver
from dollybot.media import inspect_video
from dollybot.service import Jobs, Shot, SlideShot


class Console:
    def __init__(self, base, gimbal, camera_url, output):
        self.base = base
        self.base_driver = BaseDriver(base)
        self.gimbal = gimbal
        self.gimbal_driver = GimbalDriver(gimbal)
        self.camera_url = camera_url
        self.camera = None
        self.camera_lock = asyncio.Lock()
        self.output = output
        self.previous = None
        self.motion = {}
        self.tasks = set()
        self.last_input = time.monotonic()
        self.held_action = None
        self.owner = None
        self.stopping = False
        self.camera_status = {}
        self.jobs = Jobs(self)
        self.connect_lock = asyncio.Lock()

    async def send(self, data):
        if self.owner:
            try:
                await self.owner.send(json.dumps(data))
            except Exception:
                pass

    def status(self):
        return {'base': asdict(self.base.state()), 'gimbal': asdict(self.gimbal.state()),
                'camera': self.camera_status, 'camera_connected': self.camera is not None and bool(self.camera.connected),
                'active_job': self.jobs.current if self.jobs.busy else None,
                'connecting': self.connect_lock.locked()}

    async def state(self):
        await self.send({'state': self.status()})

    async def stop(self):
        self.jobs.cancel.set()
        return await self.stop_motion()

    async def stop_motion(self):
        self.held_action = None
        self.stopping = True
        try:
            calls = {}
            if self.base.connected:
                calls['base'] = self.base_driver.stop()
            if self.gimbal.state().connected:
                calls['gimbal'] = self.gimbal_driver.stop()
            results = await asyncio.gather(*calls.values(), return_exceptions=True)
            report = {name: {'command_completed': False, 'error': 'not connected'} for name in ('base', 'gimbal')}
            for name, result in zip(calls, results):
                report[name] = {'command_completed': not isinstance(result, BaseException), 'physically_verified': False}
                if isinstance(result, BaseException):
                    report[name]['error'] = f'{type(result).__name__}: {result}'
                    await self.send({'error': f'Stop could not be confirmed: {result}'})
            return report
        finally:
            self.stopping = False

    async def camera_action(self, action, url=None):
        loop = asyncio.get_running_loop()
        async with self.camera_lock:
            def execute():
                if action == 'camera_connect':
                    if self.previous is not None:
                        raise RuntimeError('Stop and collect the current recording first')
                    if self.camera:
                        self.camera.close()
                    self.camera = None
                    camera = Moblin(url or self.camera_url)
                    try:
                        camera.connect()
                        status = camera.status()
                    except BaseException:
                        camera.close()
                        raise
                    self.camera = camera
                    self.camera_url = camera.url
                    self.camera_status = status
                    return {'message': 'Camera connected'}
                if not self.camera:
                    raise RuntimeError('Connect Moblin first')
                if action == 'record_start':
                    if self.previous is not None or self.camera.status()['recording'] is not False:
                        raise RuntimeError('Recording is already active or unknown')
                    self.previous = {r['name'] for r in self.camera.recordings()}
                    result = self.camera.set_recording(True)
                    self.camera_status = self.camera.status()
                    asyncio.run_coroutine_threadsafe(self.state(), loop).result()
                    return {'message': 'Recording on phone', 'timing': result}
                if action == 'record_stop':
                    start = time.monotonic()
                    result = self.camera.stop_recording()
                    self.camera_status = self.camera.status()
                    asyncio.run_coroutine_threadsafe(self.state(), loop).result()
                    if self.previous is None:
                        return {'message': 'Recording stopped; no console-owned clip to collect', 'timing': result}
                    recording = self.camera.wait_for_recording(self.previous)
                    folder = self.output / uuid4().hex
                    folder.mkdir(parents=True)
                    destination = folder / 'original.mp4'
                    transfer = self.camera.download(recording['name'], destination)
                    partial = Path(transfer['partial_path'])
                    video = inspect_video(partial)
                    partial.replace(destination)
                    report = {'path': str(destination), 'video': video, 'transfer': transfer,
                              'stop': result, 'stop_to_clip_ms': round((time.monotonic() - start) * 1000, 1)}
                    (folder / 'report.json').write_text(json.dumps(report, indent=2))
                    self.previous = None
                    return {'message': 'Original clip saved on Mac', 'clip': report}
                raise ValueError('Unknown camera command')
            result = await asyncio.to_thread(execute)
            await self.send(result)
            return result

    async def command(self, data):
        action = data.get('action')
        try:
            if self.jobs.busy or self.connect_lock.locked():
                raise RuntimeError('Agent take active; press Stop all motion to interrupt it')
            if action == 'base_connect':
                async with self.connect_lock:
                    await self.base.connect()
            elif action == 'gimbal_connect':
                if self.gimbal.state().connected:
                    raise RuntimeError('Gimbal is already connected')
                async with self.connect_lock:
                    await self.gimbal.connect()
            elif action in ('camera_connect', 'record_start', 'record_stop'):
                await self.camera_action(action, data.get('url'))
            elif action in ('base_move', 'gimbal_move'):
                if self.stopping or time.monotonic() - self.last_input > .25:
                    raise RuntimeError('Release controls and try again')
                stamp = data.get('time', 0)
                if not isinstance(stamp, (int, float)) or not math.isfinite(stamp) or abs(time.time() * 1000 - stamp) > 250:
                    raise RuntimeError('Stale motion request rejected')
                if action in self.motion:
                    raise RuntimeError('Release the active motion control first')
                self.motion[action] = asyncio.current_task()
                try:
                    if action == 'base_move':
                        velocity = BaseVelocity(data.get('forward', 0), data.get('left', 0), data.get('yaw', 0))
                        self.held_action = action
                        result = await self.base_driver.move(BaseHold(velocity),
                            keep_running=lambda: self.held_action == 'base_move' and time.monotonic() - self.last_input <= .25)
                    else:
                        result = await self.gimbal_driver.move(VelocityCommand(data.get('pan', 0), data.get('tilt', 0), 2))
                    await self.send({'motion_done': action, 'result': asdict(result)})
                finally:
                    self.motion.pop(action, None)
            else:
                raise ValueError('Unknown command')
        except Exception as error:
            await self.send({'error': f'{type(error).__name__}: {error}'})
        finally:
            await self.state()

    async def watchdog(self):
        while True:
            await asyncio.sleep(.05)
            if self.motion and time.monotonic() - self.last_input > .25 and not self.stopping:
                await self.stop_motion()
                await self.send({'error': 'Browser input timed out; motion stopped. Release controls.'})

    async def session(self, ws):
        if self.owner:
            await ws.close(1008, 'Another control screen owns the rig')
            return
        self.owner = ws
        self.last_input = time.monotonic()
        watchdog = asyncio.create_task(self.watchdog())
        await self.state()
        try:
            async for raw in ws:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError('Expected command object')
                if data.get('action') == 'heartbeat':
                    stamp = data.get('time', 0)
                    if isinstance(stamp, (int, float)) and math.isfinite(stamp) and abs(time.time() * 1000 - stamp) <= 250:
                        self.last_input = time.monotonic()
                        self.held_action = data.get('holding')
                elif data.get('action') == 'manual_stop':
                    if self.motion:
                        await self.stop_motion()
                elif data.get('action') == 'stop':
                    await self.stop()
                    await self.state()
                else:
                    if len(self.tasks) >= 8:
                        await self.send({'error': 'Too many pending commands'})
                        continue
                    task = asyncio.create_task(self.command(data))
                    self.tasks.add(task)
                    task.add_done_callback(self.tasks.discard)
        finally:
            watchdog.cancel()
            if self.motion:
                await self.stop_motion()
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            if self.previous is not None:
                try:
                    await self.camera_action('record_stop')
                except Exception:
                    pass
            self.owner = None

    async def api(self, ws):
        async for raw in ws:
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError('Expected request object')
                method = data['method']
                params = data.get('params', {})
                if method == 'get_status':
                    result = self.status()
                elif method == 'get_job':
                    result = self.jobs.get(params['job_id'])
                elif method == 'plan_preset':
                    result = SlideShot(**params).plan()
                elif method == 'capture_preset':
                    result = self.jobs.submit(params['request_id'], SlideShot(**params['shot']))
                    await self.state()
                elif method == 'capture_take':
                    result = self.jobs.submit(params['request_id'], Shot(**params['shot']))
                    await self.state()
                elif method == 'stop':
                    stops = await self.stop()
                    result = {'status': 'stop_requested', 'devices': stops, 'active_job': self.status()['active_job']}
                elif method == 'connect':
                    async with self.connect_lock:
                        if self.jobs.busy or self.motion or self.camera_lock.locked():
                            raise RuntimeError('Rig busy')
                        devices = params.get('devices', ['camera'])
                        if not isinstance(devices, list) or not set(devices) <= {'base', 'gimbal', 'camera'}:
                            raise ValueError('devices must contain base, gimbal, or camera')
                        if 'base' in devices and not self.base.connected:
                            await self.base.connect()
                        if 'gimbal' in devices and not self.gimbal.state().connected:
                            await self.gimbal.connect()
                        if 'camera' in devices:
                            await self.camera_action('camera_connect')
                    result = self.status()
                    await self.state()
                else:
                    raise ValueError('Unknown service method')
                await ws.send(json.dumps({'result': result}))
            except Exception as error:
                await ws.send(json.dumps({'error': f'{type(error).__name__}: {error}'}))

    async def route(self, ws):
        if ws.request.path == '/api':
            await self.api(ws)
        else:
            await self.session(ws)


def handler(port):
    origin = f'http://127.0.0.1:{port}'
    async def process(connection, request):
        if request.headers.get('Host') != f'127.0.0.1:{port}':
            return connection.respond(HTTPStatus.FORBIDDEN, 'Local access only')
        if request.path == '/api':
            if request.headers.get('Origin') is not None:
                return connection.respond(HTTPStatus.FORBIDDEN, 'Agent endpoint does not accept browser origins')
            return None
        if request.path == '/control':
            if request.headers.get('Origin') != origin:
                return connection.respond(HTTPStatus.FORBIDDEN, 'Invalid origin')
            return None
        name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}.get(request.path)
        if not name:
            return connection.respond(HTTPStatus.NOT_FOUND, 'Not found')
        content = (Path(__file__).parent / 'web' / name).read_bytes()
        mime = {'html': 'text/html', 'js': 'text/javascript', 'css': 'text/css'}[name.split('.')[-1]]
        return Response(200, 'OK', Headers({'Content-Type': mime, 'Content-Length': str(len(content)),
                         'Cache-Control': 'no-store', 'Content-Security-Policy': "default-src 'self'; connect-src 'self'; frame-ancestors 'none'"}), content)
    return process


async def run(args):
    console = Console(FlowBaseController(args.base_url, args.device_id), OM8(BleTransport(args.gimbal_address)),
                      args.camera_url, args.output.expanduser())
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown.set)
    try:
        async with serve(console.route, '127.0.0.1', args.port, process_request=handler(args.port), max_size=4096):
            print(f'Dollybot console: http://127.0.0.1:{args.port}', flush=True)
            await shutdown.wait()
            await console.jobs.close()
    finally:
        await console.jobs.close()
        await console.stop()
        await console.base_driver.close()
        await console.gimbal.close()
        if console.camera:
            await asyncio.to_thread(console.camera.close)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--base-url', default='http://192.168.2.104:8080')
    parser.add_argument('--device-id', default='0019001633354B0432333837')
    parser.add_argument('--gimbal-address', default='372488CB-D007-3262-1E09-B248B8C63EE9')
    parser.add_argument('--camera-url', default='http://192.168.2.230')
    parser.add_argument('--output', type=Path, default=Path.home() / 'Movies/Dollybot/console')
    try:
        asyncio.run(run(parser.parse_args()))
    except KeyboardInterrupt:
        pass
