import asyncio
import fcntl
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from websockets.asyncio.client import connect


@dataclass(frozen=True)
class BaseVelocity:
    forward_m_s: float = 0
    left_m_s: float = 0
    yaw_rad_s: float = 0

    def __post_init__(self) -> None:
        for value, limit in zip((self.forward_m_s, self.left_m_s, self.yaw_rad_s), (.5, .5, 1.57)):
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or abs(value) > limit:
                raise ValueError('Velocity must be finite: forward/left ±0.5 m/s, yaw ±1.57 rad/s')

    def encode(self) -> bytes:
        return struct.pack('<4f', self.forward_m_s, self.left_m_s, self.yaw_rad_s, 0)


@dataclass(frozen=True)
class BaseIdentity:
    device_id: str
    reported_ready: bool
    lift_available: bool


@dataclass(frozen=True)
class BaseState:
    identity: BaseIdentity | None
    connected: bool
    last_command: BaseVelocity | None
    stop_sent: bool


class FlowBaseController:
    def __init__(self, url: str, expected_id: str):
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError('Supply an http(s) controller origin without a path, query, or credentials')
        if not isinstance(expected_id, str) or not expected_id:
            raise ValueError('Expected hardware identity is required')
        self.url = f'{parsed.scheme}://{parsed.netloc}'
        self.ws_url = f'{"wss" if parsed.scheme == "https" else "ws"}://{parsed.netloc}/velocity'
        self.expected_id = expected_id
        self._ws = None
        self._lock_file = None
        self._wire = asyncio.Lock()
        self._identity = None
        self._last_command = None
        self._stop_sent = False

    def _read_identity(self) -> BaseIdentity:
        opener = build_opener(ProxyHandler({}))
        with opener.open(self.url + '/disco', timeout=3) as response:
            data = json.load(response)
        if data.get('type') != 'i2rtbase' or data.get('id') != self.expected_id:
            raise RuntimeError('Unexpected base controller identity')
        ready = data.get('ready')
        lift = data.get('meta', {}).get('lift')
        if not isinstance(ready, bool) or not isinstance(lift, bool):
            raise RuntimeError('Controller readiness/capability response is malformed')
        return BaseIdentity(self.expected_id, ready, lift)

    async def read_identity(self) -> BaseIdentity:
        identity = await asyncio.to_thread(self._read_identity)
        self._identity = identity
        return identity

    @property
    def connected(self) -> bool:
        from websockets.protocol import State
        return self._ws is not None and self._ws.state is State.OPEN

    async def connect(self) -> None:
        if self._ws is not None or self._lock_file is not None:
            raise RuntimeError('Controller already has a session')
        identity = await self.read_identity()
        if not identity.reported_ready:
            raise RuntimeError('Base controller reports not ready')
        folder = Path.home() / '.cache/dollybot/locks'
        folder.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(('flow-base:' + self.expected_id).encode()).hexdigest()
        self._lock_file = (folder / key).open('a')
        try:
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._ws = await connect(self.ws_url, proxy=None, open_timeout=3, close_timeout=1, ping_interval=None, max_size=4096)
        except BaseException:
            await self.close()
            raise

    def state(self) -> BaseState:
        return BaseState(self._identity, self.connected, self._last_command, self._stop_sent)

    async def send_velocity(self, velocity: BaseVelocity) -> None:
        if not isinstance(velocity, BaseVelocity):
            raise TypeError('Expected BaseVelocity')
        async with self._wire:
            if not self.connected:
                raise ConnectionError('Base feed disconnected; physical outcome is unknown')
            self._stop_sent = False
            async with asyncio.timeout(.15):
                await self._ws.send(velocity.encode())
            self._last_command = velocity
            self._stop_sent = velocity == BaseVelocity()

    async def close(self) -> None:
        try:
            if self._ws is not None:
                await self._ws.close()
        finally:
            self._ws = None
            if self._lock_file is not None:
                self._lock_file.close()
                self._lock_file = None
