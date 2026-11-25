import asyncio
import json
import math
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

from dollybot.capture import capture
from dollybot.controllers.flow_base import BaseVelocity
from dollybot.controllers.om8 import VelocityCommand
from dollybot.drivers.base import BaseMove
from dollybot.kino import import_clip


@dataclass(frozen=True)
class Shot:
    goal: str
    seconds: float = 3
    lead_s: float = 1
    tail_s: float = 3
    forward_m_s: float = 0
    left_m_s: float = 0
    yaw_rad_s: float = 0
    pan_deg_s: float = 0
    tilt_deg_s: float = 0
    motion_seconds: float = 1
    import_to_kino: bool = True

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip() or len(self.goal) > 2000:
            raise ValueError('An explicit shot goal is required (1–2000 characters)')
        for key, lower, upper in [('seconds', .1, 30), ('lead_s', 0, 10), ('tail_s', 0, 10), ('motion_seconds', .01, 2)]:
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lower <= value <= upper:
                raise ValueError(f'{key} must be finite and between {lower} and {upper}')
        if not isinstance(self.import_to_kino, bool):
            raise ValueError('import_to_kino must be boolean')
        self.base_move()
        self.gimbal_move()
        if self.has_motion and self.motion_seconds > self.seconds:
            raise ValueError('Motion must fit inside the main recording interval')

    @property
    def has_base(self):
        return bool(self.forward_m_s or self.left_m_s or self.yaw_rad_s)

    @property
    def has_gimbal(self):
        return bool(self.pan_deg_s or self.tilt_deg_s)

    @property
    def has_motion(self):
        return self.has_base or self.has_gimbal

    def base_move(self):
        return BaseMove(BaseVelocity(self.forward_m_s, self.left_m_s, self.yaw_rad_s), self.motion_seconds)

    def gimbal_move(self):
        return VelocityCommand(self.pan_deg_s, self.tilt_deg_s, self.motion_seconds)


class Jobs:
    def __init__(self, console, capture_fn=capture, import_fn=import_clip):
        self.console = console
        self.folder = console.output / 'jobs'
        self.capture_fn = capture_fn
        self.import_fn = import_fn
        self.task = None
        self.current = None
        self.cancel = threading.Event()

    @property
    def busy(self):
        return self.task is not None and not self.task.done()

    @staticmethod
    def validate_id(value):
        if not isinstance(value, str) or len(value) != 32 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('request_id must be 32 lowercase hexadecimal characters; retain it for retries')

    def save(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / (self.current['job_id'] + '.json')
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.current, indent=2) + '\n')
        temp.replace(path)

    def get(self, job_id):
        self.validate_id(job_id)
        result = json.loads((self.folder / (job_id + '.json')).read_text())
        if result['status'] == 'running' and not (self.busy and self.current['job_id'] == job_id):
            result.update(status='unknown', error='Service interrupted; no automatic replay')
        return result

    def submit(self, request_id, shot):
        self.validate_id(request_id)
        path = self.folder / (request_id + '.json')
        if path.exists():
            job = self.get(request_id)
            if job['request'] != asdict(shot):
                raise ValueError('Request ID already belongs to a different shot')
            return {'job_id': request_id, 'status': job['status']}
        c = self.console
        if self.busy or c.motion or c.stopping or c.camera_lock.locked() or c.previous is not None or c.connect_lock.locked():
            raise RuntimeError('Rig busy: connection setup, manual operation, or agent take in progress; inspect status and wait')
        if c.camera is None:
            raise RuntimeError('Connect the camera first')
        if shot.has_base and not c.base.connected:
            raise RuntimeError('Connect the base first')
        if shot.has_gimbal and not c.gimbal.state().connected:
            raise RuntimeError('Connect the gimbal first')
        self.cancel.clear()
        self.current = {'job_id': request_id, 'request': asdict(shot), 'status': 'running', 'phase': 'admitted'}
        self.save()
        self.task = asyncio.create_task(self.execute(shot))
        return {'job_id': request_id, 'status': 'running'}

    def wait(self, seconds):
        if self.cancel.wait(seconds):
            raise InterruptedError('Take stopped; cleanup attempted')

    async def motion(self, shot):
        if self.cancel.is_set():
            raise InterruptedError('Stopped before motion')
        results = []
        try:
            async with asyncio.TaskGroup() as group:
                if shot.has_base:
                    results.append(group.create_task(self.console.base_driver.move(shot.base_move())))
                if shot.has_gimbal:
                    results.append(group.create_task(self.console.gimbal_driver.move(shot.gimbal_move())))
        finally:
            if shot.has_motion:
                await self.console.stop_motion()
        return [asdict(task.result()) for task in results]

    async def execute(self, shot):
        c = self.console
        loop = asyncio.get_running_loop()
        try:
            async with c.camera_lock:
                def during():
                    self.wait(shot.lead_s)
                    result = asyncio.run_coroutine_threadsafe(self.motion(shot), loop).result()
                    self.wait(max(0, shot.seconds - (shot.motion_seconds if shot.has_motion else 0)))
                    return result

                def recording_state(on):
                    c.camera_status = {'recording': on}
                    asyncio.run_coroutine_threadsafe(c.state(), loop).result()

                def record():
                    if self.cancel.is_set():
                        raise InterruptedError('Stopped before recording')
                    return self.capture_fn(c.camera, shot.lead_s + shot.seconds, c.output, False,
                                           shot.tail_s, during, self.wait, recording_state)

                self.current['phase'] = 'preparing_camera'
                self.save()
                await asyncio.to_thread(c.camera.request, {'setGimbalTracking': {'on': False}})
                self.current['phase'] = 'capture'
                self.save()
                try:
                    result = await asyncio.to_thread(record)
                finally:
                    try:
                        c.camera_status = await asyncio.to_thread(c.camera.status)
                    except Exception:
                        c.camera_status = {'recording': None}
                self.current['result'] = result
                self.save()
            if self.cancel.is_set():
                raise InterruptedError('Stopped after capture; clip retained')
            if shot.import_to_kino:
                self.current['phase'] = 'kino_import'
                self.save()
                self.current['kino'] = await asyncio.to_thread(self.import_fn, result['local_path'])
            self.current.update(status='cancelled' if self.cancel.is_set() else 'completed', phase='done')
        except asyncio.CancelledError:
            self.cancel.set()
            self.current.update(status='unknown', error='Service interrupted; inspect phone and saved files before any retry')
            raise
        except Exception as error:
            self.current.update(status='cancelled' if self.cancel.is_set() else 'failed', error=f'{type(error).__name__}: {error}')
        finally:
            self.save()
            await c.send({'job': self.current})
            await c.state()

    async def close(self):
        if self.busy:
            self.cancel.set()
            await self.console.stop_motion()
            await self.task
