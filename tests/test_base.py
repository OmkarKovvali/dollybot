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
from dollybot.drivers.base import BaseDriver, BaseHold, BaseMove, BaseSlide


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

    async def test_continuous_hold_passes_two_seconds_and_stops_on_lease_loss(self):
        await self.controller.connect()
        held = True
        task = asyncio.create_task(self.driver.move(BaseHold(BaseVelocity(.08)), keep_running=lambda: held))
        await asyncio.sleep(2.2)
        self.assertFalse(task.done())
        held = False
        result = await asyncio.wait_for(task, 1)
        self.assertEqual(result.outcome, 'stopped')
        values = [struct.unpack('<4f', p) for _, p in self.frames]
        self.assertTrue(all(v[0] > 0 for v in values[:-6]))
        self.assertEqual(values[-6:], [(0, 0, 0, 0)] * 6)
        with self.assertRaises(ValueError):
            await self.driver.move(BaseHold(BaseVelocity(.08)))

    def test_slide_profile_distance_direction_and_limits(self):
        for direction, axis, sign in [('right', 1, -1), ('left', 1, 1), ('forward', 0, 1), ('backward', 0, -1)]:
            for distance in (1.8288, .1):
                slide = BaseSlide(direction, distance)
                dt = slide.duration_s / 10000
                integral = 0
                last_speed = 0
                for i in range(10000):
                    v = slide.velocity_at((i + .5) * dt)
                    values = (v.forward_m_s, v.left_m_s)
                    speed = values[axis] * sign
                    self.assertGreaterEqual(speed, 0)
                    self.assertLessEqual(speed, .5)
                    self.assertEqual(values[1-axis], 0)
                    self.assertEqual(v.yaw_rad_s, 0)
                    self.assertLessEqual(abs(speed - last_speed), .25 * dt + 1e-9)
                    last_speed = speed
                    integral += speed * dt
                self.assertAlmostEqual(integral, distance, places=6)
                self.assertEqual(slide.velocity_at(0), BaseVelocity())
                self.assertEqual(slide.velocity_at(slide.duration_s), BaseVelocity())
        self.assertAlmostEqual(BaseSlide('right').duration_s, 5.6576)
        for args in [('up',), ('right', True), ('right', float('nan')), ('right', 7), ('right', 1, .6), ('right', 1, .001)]:
            with self.assertRaises(ValueError):
                BaseSlide(*args)

    async def test_slide_stop_prevents_later_motion(self):
        await self.controller.connect()
        task = asyncio.create_task(self.driver.move(BaseSlide('right')))
        await asyncio.sleep(.18)
        await self.driver.stop()
        result = await task
        self.assertEqual(result.outcome, 'stopped')
        values = [struct.unpack('<4f', p) for _, p in self.frames]
        self.assertTrue(any(v[1] < 0 for v in values))
        last_nonzero = max(i for i, v in enumerate(values) if v != (0, 0, 0, 0))
        self.assertTrue(all(v == (0, 0, 0, 0) for v in values[last_nonzero+1:]))
        self.assertGreaterEqual(len(values) - last_nonzero - 1, 6)

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
