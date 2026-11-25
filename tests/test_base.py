import asyncio
import json
import math
import struct
import time
import unittest
from http import HTTPStatus
from unittest.mock import patch

from websockets.asyncio.server import serve

from dollybot.controllers.flow_base import BaseVelocity, FlowBaseController
from dollybot.drivers.base import BaseDriver, BaseMove


class BaseTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.identity = {'type': 'i2rtbase', 'id': 'test-base', 'ready': True, 'meta': {'lift': False}}
        self.frames = []
        self.peers = []
        self.reject = False

        async def process(connection, request):
            if request.path == '/disco':
                return connection.respond(HTTPStatus.OK, json.dumps(self.identity))
            if request.path != '/velocity':
                return connection.respond(HTTPStatus.NOT_FOUND, 'not found')

        async def handler(ws):
            self.peers.append(ws)
            async for packet in ws:
                self.frames.append((time.monotonic(), packet))
                if self.reject:
                    await ws.close(code=1008, reason='controller rejection')
                    return

        self.server = await serve(handler, '127.0.0.1', 0, process_request=process)
        port = self.server.sockets[0].getsockname()[1]
        self.controller = FlowBaseController(f'http://127.0.0.1:{port}', 'test-base')
        self.driver = BaseDriver(self.controller)

    async def asyncTearDown(self):
        await self.driver.close()
        self.server.close()
        await self.server.wait_closed()

    async def test_read_only_identity_does_not_open_motion_feed(self):
        identity = await self.controller.read_identity()
        self.assertTrue(identity.reported_ready)
        self.assertFalse(identity.lift_available)
        self.assertEqual(self.peers, [])
        self.assertEqual(self.frames, [])

    async def test_identity_and_readiness_checked_before_connect(self):
        self.identity['id'] = 'other-base'
        with self.assertRaisesRegex(RuntimeError, 'identity'):
            await self.controller.connect()
        self.identity['id'] = 'test-base'
        self.identity['ready'] = False
        with self.assertRaisesRegex(RuntimeError, 'not ready'):
            await self.controller.connect()
        self.assertEqual(self.peers, [])

    async def test_typed_wire_payload_leaves_lift_zero(self):
        payload = BaseVelocity(.08, -.04, .1).encode()
        self.assertEqual(len(payload), 16)
        forward, left, yaw, lift = struct.unpack('<4f', payload)
        self.assertAlmostEqual(forward, .08)
        self.assertAlmostEqual(left, -.04)
        self.assertAlmostEqual(yaw, .1)
        self.assertEqual(lift, 0)

    async def test_bounded_move_sends_refreshes_then_six_stops(self):
        await self.controller.connect()
        result = await self.driver.move(BaseMove(BaseVelocity(.08), .2))
        await asyncio.sleep(.01)
        values = [struct.unpack('<4f', p) for _, p in self.frames]
        self.assertGreaterEqual(result.velocity_frames_sent, 3)
        self.assertEqual(values[-6:], [(0, 0, 0, 0)] * 6)
        self.assertFalse(result.physically_verified)
        self.assertEqual(result.outcome, 'command_completed')
        self.assertEqual(result.stop_frames_sent, 6)

    async def test_explicit_stop_preempts_without_later_nonzero(self):
        await self.controller.connect()
        task = asyncio.create_task(self.driver.move(BaseMove(BaseVelocity(.08), 2)))
        await asyncio.sleep(.06)
        with self.assertRaises(RuntimeError):
            await self.driver.move(BaseMove(BaseVelocity(.01), .1))
        await self.driver.stop()
        result = await task
        self.assertEqual(result.outcome, 'stopped')
        values = [struct.unpack('<4f', p) for _, p in self.frames]
        first_zero = values.index((0, 0, 0, 0))
        self.assertTrue(all(v == (0, 0, 0, 0) for v in values[first_zero:]))

    async def test_task_cancellation_still_stops(self):
        await self.controller.connect()
        task = asyncio.create_task(self.driver.move(BaseMove(BaseVelocity(.08), 2)))
        await asyncio.sleep(.06)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual([p for _, p in self.frames][-6:], [bytes(16)] * 6)

    async def test_disconnect_does_not_reconnect_or_replay(self):
        await self.controller.connect()
        self.reject = True
        with self.assertRaises(Exception):
            await self.driver.move(BaseMove(BaseVelocity(.08), 1))
        self.assertEqual(len(self.peers), 1)
        self.assertFalse(self.controller.connected)

    async def test_lock_is_by_hardware_id_not_url(self):
        await self.controller.connect()
        second = FlowBaseController(self.controller.url.replace('127.0.0.1', 'localhost'), 'test-base')
        try:
            with self.assertRaises(BlockingIOError):
                await second.connect()
        finally:
            await second.close()
        self.assertTrue(self.controller.connected)

    async def test_readiness_rechecked_at_move(self):
        await self.controller.connect()
        self.identity['ready'] = False
        with self.assertRaisesRegex(RuntimeError, 'not ready'):
            await self.driver.move(BaseMove(BaseVelocity(.08), .1))
        self.assertEqual(self.frames, [])

    async def test_event_loop_stall_does_not_resume_motion(self):
        await self.controller.connect()
        original = self.controller.send_velocity
        sent = 0

        async def slow_once(velocity):
            nonlocal sent
            await original(velocity)
            if velocity != BaseVelocity():
                sent += 1
                if sent == 1:
                    await asyncio.sleep(.2)

        with patch.object(self.controller, 'send_velocity', slow_once):
            with self.assertRaisesRegex(TimeoutError, 'stalled'):
                await self.driver.move(BaseMove(BaseVelocity(.08), 1))
        self.assertEqual(sent, 1)
        self.assertEqual([p for _, p in self.frames][-6:], [bytes(16)] * 6)

    async def test_close_interrupts_active_move_before_disconnect(self):
        await self.controller.connect()
        task = asyncio.create_task(self.driver.move(BaseMove(BaseVelocity(.08), 2)))
        await asyncio.sleep(.06)
        await self.driver.close()
        self.assertEqual((await task).outcome, 'stopped')
        self.assertFalse(self.controller.connected)
        self.assertEqual([p for _, p in self.frames][-6:], [bytes(16)] * 6)

    async def test_validation_rejects_bad_and_excessive_commands(self):
        for value in (True, '1', math.nan, math.inf, .6):
            with self.assertRaises(ValueError):
                BaseVelocity(value)
        for duration in (True, '1', math.nan, math.inf, 0, 2.1):
            with self.assertRaises(ValueError):
                BaseMove(BaseVelocity(), duration)
        with self.assertRaises(ValueError):
            BaseMove(BaseVelocity(.1, .1), 1)
        with self.assertRaises(ValueError):
            BaseMove(BaseVelocity(yaw_rad_s=.3), 1)
        with self.assertRaises(ValueError):
            FlowBaseController('http://example/velocity', 'test-base')
