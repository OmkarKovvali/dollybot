import asyncio
import math
import time
from dataclasses import dataclass
from typing import Literal

from dollybot.controllers.flow_base import BaseVelocity, FlowBaseController


@dataclass(frozen=True)
class BaseMove:
    velocity: BaseVelocity
    duration_s: float

    def __post_init__(self) -> None:
        if not isinstance(self.velocity, BaseVelocity):
            raise TypeError('Expected BaseVelocity')
        if isinstance(self.duration_s, bool) or not isinstance(self.duration_s, (int, float)) or not math.isfinite(self.duration_s) or not 0 < self.duration_s <= 2:
            raise ValueError('Commissioning move duration must be in (0, 2] seconds')
        if math.hypot(self.velocity.forward_m_s, self.velocity.left_m_s) > .1 or abs(self.velocity.yaw_rad_s) > .2:
            raise ValueError('Commissioning limits: translation magnitude 0.1 m/s, yaw 0.2 rad/s')


@dataclass(frozen=True)
class BaseMoveResult:
    requested: BaseMove
    outcome: Literal['command_completed', 'stopped']
    elapsed_s: float
    velocity_frames_sent: int
    stop_frames_sent: int
    physically_verified: bool = False


class BaseDriver:
    def __init__(self, controller: FlowBaseController):
        self.controller = controller
        self._active = False
        self._stopping = 0
        self._stop = asyncio.Event()
        self._commands = asyncio.Lock()
        self._idle = asyncio.Event()
        self._idle.set()
        self._closing = False

    async def _send_stop(self) -> int:
        for _ in range(6):
            async with self._commands:
                await self.controller.send_velocity(BaseVelocity())
            await asyncio.sleep(.05)
        return 6

    async def stop(self) -> int:
        self._stopping += 1
        self._stop.set()
        try:
            return await self._send_stop()
        finally:
            self._stopping -= 1

    async def move(self, request: BaseMove) -> BaseMoveResult:
        if not isinstance(request, BaseMove):
            raise TypeError('Expected BaseMove')
        if self._active or self._stopping or self._closing:
            raise RuntimeError('Base is busy, stopping, or closing')
        self._active = True
        self._idle.clear()
        self._stop.clear()
        started = None
        sent = 0
        stop_frames = 0
        try:
            identity = await self.controller.read_identity()
            if not identity.reported_ready:
                raise RuntimeError('Base controller reports not ready')
            if not self.controller.connected:
                raise ConnectionError('Connect the base feed before moving')
            started = time.monotonic()
            previous_send = started
            while time.monotonic() - started < request.duration_s:
                async with self._commands:
                    if self._stop.is_set():
                        break
                    now = time.monotonic()
                    if now - previous_send > .15:
                        raise TimeoutError('Command refresh stalled; refusing to resume movement')
                    await self.controller.send_velocity(request.velocity)
                    sent += 1
                    previous_send = now
                remaining = request.duration_s - (time.monotonic() - started)
                if remaining > 0:
                    try:
                        await asyncio.wait_for(self._stop.wait(), min(.05, remaining))
                    except TimeoutError:
                        pass
        finally:
            try:
                if started is not None:
                    stop_frames = await self._send_stop()
            finally:
                self._active = False
                self._idle.set()
        return BaseMoveResult(request, 'stopped' if self._stop.is_set() else 'command_completed',
                              time.monotonic() - started, sent, stop_frames)

    async def close(self) -> None:
        self._closing = True
        try:
            if self._active:
                try:
                    await self.stop()
                finally:
                    await self._idle.wait()
        finally:
            await self.controller.close()
