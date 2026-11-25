import asyncio
import json
import math
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from dollybot.adapters.moblin import Moblin
from dollybot.capture import capture
from dollybot.controllers.om8 import OM8, VelocityCommand
from dollybot.drivers.gimbal import GimbalDriver


class StopRequested(Exception):
    pass


@dataclass(frozen=True)
class TakeRequest:
    motion: VelocityCommand
    lead_s: float = 1
    tail_s: float = 3
    verify_copy: bool = False

    def __post_init__(self):
        for value in (self.lead_s, self.tail_s):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 10:
                raise ValueError('Lead and tail must be finite numbers between 0 and 10 seconds')
        if self.lead_s + self.motion.duration_s < 0.1:
            raise ValueError('Recording interval must be at least 0.1 seconds')
        if not isinstance(self.verify_copy, bool):
            raise ValueError('verify_copy must be boolean')


class Rig:
    def __init__(self, controller: OM8, camera_url: str, output: Path, camera_factory=Moblin):
        self.controller = controller
        self.driver = GimbalDriver(controller)
        self.camera_url = camera_url
        self.output = output.expanduser().resolve()
        self.camera_factory = camera_factory
        self._task = None
        self._job = None
        self._cancel = threading.Event()
        self._closing = False
        self._stopping = 0

    def _save(self):
        folder = self.output / 'jobs'
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (self._job['job_id'] + '.json')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self._job, indent=2) + '\n')
        temporary.replace(path)

    def _admit(self, kind, request, request_id):
        if request_id is not None:
            self._validate_id(request_id)
            path = self.output / 'jobs' / (request_id + '.json')
            if path.exists():
                previous = self.get_job(request_id)
                if previous['kind'] != kind or previous['request'] != asdict(request):
                    raise ValueError('Request ID already belongs to a different operation')
                return request_id, False
        if self._stopping:
            raise RuntimeError('Rig is stopping')
        if self._closing:
            raise RuntimeError('Rig is closing')
        if self._task is not None and not self._task.done():
            raise RuntimeError('Rig is busy; poll the active job or stop it')
        if not self.controller.state().connected:
            raise ConnectionError('Connect the gimbal before submitting work')
        self._cancel.clear()
        self._job = {'job_id': request_id or uuid4().hex, 'kind': kind, 'request': asdict(request), 'status': 'running'}
        self._save()
        return self._job['job_id'], True

    def move_gimbal(self, motion: VelocityCommand, request_id: str | None = None) -> str:
        job_id, created = self._admit('move', motion, request_id)
        if not created:
            return job_id
        self._task = asyncio.create_task(self._run(motion, None))
        return job_id

    def capture_take(self, request: TakeRequest, request_id: str | None = None) -> str:
        job_id, created = self._admit('take', request, request_id)
        if not created:
            return job_id
        self._task = asyncio.create_task(self._run(request.motion, request))
        return job_id

    def _wait(self, seconds):
        if self._cancel.wait(seconds):
            raise StopRequested('Stop requested; cleanup attempted')

    async def _move(self, motion):
        if self._cancel.is_set():
            raise StopRequested('Stopped before motion')
        result = await self.driver.move(motion)
        if result.outcome == 'stopped':
            raise StopRequested('Motion interrupted')
        return asdict(result)

    async def _run(self, motion, take):
        try:
            if take is None:
                result = await self._move(motion)
            else:
                loop = asyncio.get_running_loop()

                def during_recording():
                    self._wait(take.lead_s)
                    return asyncio.run_coroutine_threadsafe(self._move(motion), loop).result()

                def record():
                    with self.camera_factory(self.camera_url) as camera:
                        return capture(camera, take.lead_s + motion.duration_s, self.output,
                                       take.verify_copy, take.tail_s, during_recording, self._wait)

                result = await asyncio.to_thread(record)
            self._job['result'] = result
            self._job['status'] = 'cancelled' if self._cancel.is_set() else 'completed'
        except asyncio.CancelledError:
            self._cancel.set()
            self._job.update(status='unknown', error='Execution interrupted; physical outcome unknown')
            raise
        except StopRequested as error:
            self._job.update(status='cancelled', error=str(error))
        except Exception as error:
            self._job.update(status='failed', error=f'{type(error).__name__}: {error}')
        finally:
            self._job['gimbal_state'] = asdict(self.controller.state())
            self._save()

    @staticmethod
    def _validate_id(job_id: str):
        if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
            raise ValueError('Job/request ID must be 32 lowercase hexadecimal characters')

    def get_job(self, job_id: str):
        self._validate_id(job_id)
        if self._job is not None and job_id == self._job['job_id']:
            return json.loads(json.dumps(self._job))
        result = json.loads((self.output / 'jobs' / (job_id + '.json')).read_text())
        if result['status'] == 'running':
            result['status'] = 'unknown'
            result['error'] = 'Previous process ended without a terminal result; no automatic replay'
        return result

    def get_status(self):
        return {'gimbal': asdict(self.controller.state()),
                'active_job': self._job['job_id'] if self._task and not self._task.done() else None}

    async def stop(self):
        self._stopping += 1
        try:
            return await self._stop_job()
        finally:
            self._stopping -= 1

    async def _stop_job(self):
        self._cancel.set()
        try:
            state = asdict(await self.driver.stop())
        except Exception as error:
            return {'stop_sent': False, 'error': str(error), 'job': self.get_status()['active_job']}
        return {'stop_sent': state['stop_sent'], 'gimbal': state,
                'job': self.get_status()['active_job'], 'recording_cleanup': 'poll job for completion'}

    async def close(self):
        self._closing = True
        try:
            if self._task and not self._task.done():
                await self.stop()
                await self._task
        finally:
            await self.controller.close()
