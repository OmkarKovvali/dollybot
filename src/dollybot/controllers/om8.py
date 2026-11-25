import asyncio
import fcntl
import hashlib
import math
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .vendor.duml import DUMLParser
from .vendor.gimbal import _crc16

WRITE = '0000fff5-0000-1000-8000-00805f9b34fb'
NOTIFY = '0000fff4-0000-1000-8000-00805f9b34fb'


@dataclass(frozen=True)
class VelocityCommand:
    pan_deg_s: float
    tilt_deg_s: float
    duration_s: float

    def __post_init__(self):
        for value in (self.pan_deg_s, self.tilt_deg_s, self.duration_s):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Motion values must be finite numbers')
        if max(abs(self.pan_deg_s), abs(self.tilt_deg_s)) > 20:
            raise ValueError('Commissioning limit: maximum 20 degrees/second per axis')
        if not 0 < self.duration_s <= 2:
            raise ValueError('Commissioning limit: duration must be in (0, 2] seconds')
        if self.pan_deg_s and self.tilt_deg_s:
            raise ValueError('Combined-axis motion is not qualified; select pan or tilt')


@dataclass(frozen=True)
class GimbalState:
    connected: bool
    moving: bool
    reported_angles_deg: tuple[float, float, float] | None
    telemetry_age_s: float | None
    stop_sent: bool


@dataclass(frozen=True)
class MotionResult:
    requested: VelocityCommand
    elapsed_s: float
    outcome: str
    stop_sent: bool
    physically_verified: bool = False


class Transport(Protocol):
    @property
    def connected(self) -> bool: ...
    async def connect(self, receive): ...
    async def write(self, packet: bytes): ...
    async def close(self): ...


def speed_packet(pan: float = 0, tilt: float = 0) -> bytes:
    body = bytes.fromhex('0204010000040c')
    body += struct.pack('<hhhBB', round(pan * 10), 0, round(tilt * 10), 0x80, 10 if pan or tilt else 0)
    return bytes.fromhex('551504a9') + body + _crc16(body, 0xdf0c).to_bytes(2, 'little')


class BleTransport:
    def __init__(self, address: str):
        self.address = address
        self.client = None
        self.lock_file = None

    @property
    def connected(self):
        return self.client is not None and self.client.is_connected

    async def connect(self, receive):
        from bleak import BleakClient, BleakScanner
        target = self.address
        folder = Path.home() / '.cache/dollybot/locks'
        folder.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(self.address.lower().encode()).hexdigest()
        self.lock_file = (folder / key).open('a')
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if sys.platform == 'darwin':
                from Foundation import NSUUID
                from bleak.backends.device import BLEDevice
                scanner = BleakScanner()
                manager = scanner._backend._manager
                await manager.wait_until_ready()
                identifier = NSUUID.alloc().initWithUUIDString_(self.address)
                if identifier is None:
                    raise ValueError('On macOS, supply the CoreBluetooth peripheral UUID')
                peripherals = manager.central_manager.retrievePeripheralsWithIdentifiers_([identifier])
                if peripherals:
                    target = BLEDevice(self.address, 'OM8', (peripherals[0], manager))
            self.client = BleakClient(target, timeout=15)
            await self.client.connect()
            await self.client.start_notify(NOTIFY, receive)
        except BaseException:
            await self.close()
            raise

    async def write(self, packet):
        if not self.connected:
            raise ConnectionError('OM8 is disconnected; motion outcome may be unknown')
        async with asyncio.timeout(2):
            for offset in range(0, len(packet), 20):
                await self.client.write_gatt_char(WRITE, packet[offset:offset + 20], response=False)

    async def close(self):
        try:
            if self.connected:
                await asyncio.wait_for(self.client.disconnect(), 5)
        finally:
            self.client = None
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None


class OM8:
    def __init__(self, transport: Transport):
        self.transport = transport
        self._wire = asyncio.Lock()
        self._active = False
        self._stopping = 0
        self._stop = asyncio.Event()
        self._stop_sent = False
        self._angles = None
        self._received_at = None
        self._parser = DUMLParser()

    async def connect(self):
        await self.transport.connect(self._receive)

    def _receive(self, _, data):
        for packet in self._parser.feed(bytes(data)):
            if packet.cmd_set == 4 and packet.cmd == 5 and len(packet.payload) >= 12:
                self._angles = tuple(value / 10 for value in struct.unpack('<hhh', packet.payload[:6]))
                self._received_at = time.monotonic()

    def state(self) -> GimbalState:
        age = None if self._received_at is None else time.monotonic() - self._received_at
        return GimbalState(self.transport.connected, self._active, self._angles, age, self._stop_sent)

    async def _send_stop(self):
        self._stop_sent = False
        for _ in range(3):
            async with self._wire:
                await self.transport.write(speed_packet())
            await asyncio.sleep(0.1)
        self._stop_sent = True

    async def stop(self) -> GimbalState:
        self._stopping += 1
        self._stop.set()
        try:
            await self._send_stop()
            return self.state()
        finally:
            self._stopping -= 1

    async def drive(self, command: VelocityCommand) -> MotionResult:
        if self._active or self._stopping:
            raise RuntimeError('Gimbal is busy')
        if not self.transport.connected:
            raise ConnectionError('Gimbal is disconnected')
        self._active = True
        self._stop.clear()
        self._stop_sent = False
        started = time.monotonic()
        try:
            while time.monotonic() - started < command.duration_s:
                async with self._wire:
                    if self._stop.is_set():
                        break
                    await self.transport.write(speed_packet(command.pan_deg_s, command.tilt_deg_s))
                remaining = command.duration_s - (time.monotonic() - started)
                if remaining > 0:
                    try:
                        await asyncio.wait_for(self._stop.wait(), min(0.2, remaining))
                    except TimeoutError:
                        pass
        finally:
            try:
                await self._send_stop()
            finally:
                self._active = False
        return MotionResult(command, time.monotonic() - started,
                            'stopped' if self._stop.is_set() else 'command_completed', self._stop_sent)

    async def close(self):
        try:
            if self.transport.connected:
                await self.stop()
        finally:
            await self.transport.close()
