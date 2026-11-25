import asyncio
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dollybot.agent import ShotInput
from dollybot.controllers.om8 import OM8, VelocityCommand, speed_packet
from dollybot.controllers.vendor.duml import DUMLParser
from dollybot.rig import Rig, TakeRequest


class FakeTransport:
    def __init__(self):
        self.connected = False
        self.packets = []
        self.fail = False

    async def connect(self, receive):
        self.connected = True
        self.receive = receive

    async def write(self, packet):
        if self.fail:
            self.connected = False
            raise ConnectionError('lost link')
        self.packets.append(packet)

    async def close(self):
        self.connected = False


class FakeCamera:
    url = 'http://fixture'

    def __init__(self):
        self.recording = False
        self.commands = []
        self.fail_start = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def status(self):
        return {'recording': self.recording}

    def recordings(self):
        return []

    def set_recording(self, on):
        self.commands.append(on)
        self.recording = on
        if on and self.fail_start:
            raise TimeoutError('start outcome unknown')
        return {}

    def stop_recording(self):
        return self.set_recording(False)

    def wait_for_recording(self, previous):
        return {'name': 'new.mp4'}

    def download(self, name, destination=None):
        if destination is None:
            return {'sha256': 'fixture'}
        partial = destination.with_suffix('.partial')
        partial.write_bytes(b'fixture')
        return {'partial_path': str(partial), 'sha256': 'fixture'}


class GimbalTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = FakeTransport()
        self.controller = OM8(self.transport)
        await self.controller.connect()
        self.directory = tempfile.TemporaryDirectory()
        self.camera = FakeCamera()
        self.rig = Rig(self.controller, self.camera.url, Path(self.directory.name), lambda _: self.camera)

    async def asyncTearDown(self):
        await self.rig.close()
        self.directory.cleanup()

    async def wait_job(self, job):
        async with asyncio.timeout(5):
            while self.rig.get_job(job)['status'] == 'running':
                await asyncio.sleep(.01)
        return self.rig.get_job(job)

    def moving_packets(self):
        return [p for p in self.transport.packets if p != speed_packet()]

    async def test_bounded_move_and_stop(self):
        result = await self.controller.drive(VelocityCommand(10, 0, .1))
        self.assertEqual(result.outcome, 'command_completed')
        self.assertFalse(result.physically_verified)
        self.assertEqual(self.transport.packets[-3:], [speed_packet()] * 3)
        self.assertEqual(struct.unpack('<hhh', self.moving_packets()[0][11:17]), (100, 0, 0))

    async def test_stop_preempts_and_no_later_motion(self):
        job = self.rig.move_gimbal(VelocityCommand(10, 0, 2))
        await asyncio.sleep(.03)
        with self.assertRaises(RuntimeError):
            self.rig.move_gimbal(VelocityCommand(1, 0, 1))
        await self.rig.stop()
        count = len(self.moving_packets())
        result = await self.wait_job(job)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(len(self.moving_packets()), count)

    async def test_cancelled_controller_task_still_sends_stop(self):
        task = asyncio.create_task(self.controller.drive(VelocityCommand(0, 10, 2)))
        await asyncio.sleep(.03)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.transport.packets[-3:], [speed_packet()] * 3)
        self.assertFalse(self.controller.state().moving)

    async def test_link_loss_fails_without_replay(self):
        self.transport.fail = True
        job = self.rig.move_gimbal(VelocityCommand(10, 0, .1))
        result = await self.wait_job(job)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['gimbal_state']['stop_sent'])
        self.assertEqual(self.transport.packets, [])

    async def test_capture_coordinates_recording_and_clip(self):
        with patch('dollybot.capture.inspect_video', return_value={'duration_seconds': .6}):
            job = self.rig.capture_take(TakeRequest(VelocityCommand(10, 0, .1), .01, .01, True))
            result = await self.wait_job(job)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(self.camera.commands, [True, False])
        self.assertTrue(result['result']['byte_identical_repeat_download'])
        self.assertTrue(Path(result['result']['local_path']).is_file())
        self.assertEqual(result['result']['motion']['outcome'], 'command_completed')

    async def test_stop_during_lead_does_not_move(self):
        job = self.rig.capture_take(TakeRequest(VelocityCommand(10, 0, .1), 2, 0))
        async with asyncio.timeout(2):
            while not self.camera.recording:
                await asyncio.sleep(.01)
        await self.rig.stop()
        self.assertEqual((await self.wait_job(job))['status'], 'cancelled')
        self.assertEqual(self.camera.commands, [True, False])
        self.assertEqual(self.moving_packets(), [])

    async def test_start_failure_stops_camera_without_moving(self):
        self.camera.fail_start = True
        job = self.rig.capture_take(TakeRequest(VelocityCommand(10, 0, .1), 0, 0))
        self.assertEqual((await self.wait_job(job))['status'], 'failed')
        self.assertEqual(self.camera.commands, [True, False])
        self.assertEqual(self.moving_packets(), [])

    async def test_existing_recording_untouched(self):
        self.camera.recording = True
        job = self.rig.capture_take(TakeRequest(VelocityCommand(10, 0, .1), 0, 0))
        self.assertEqual((await self.wait_job(job))['status'], 'failed')
        self.assertEqual(self.camera.commands, [])
        self.assertEqual(self.moving_packets(), [])

    async def test_motion_failure_stops_camera(self):
        self.transport.fail = True
        job = self.rig.capture_take(TakeRequest(VelocityCommand(10, 0, .1), 0, 0))
        self.assertEqual((await self.wait_job(job))['status'], 'failed')
        self.assertEqual(self.camera.commands, [True, False])

    async def test_restart_does_not_claim_completion_or_replay(self):
        job = 'a' * 32
        folder = Path(self.directory.name) / 'jobs'
        folder.mkdir()
        (folder / (job + '.json')).write_text(json.dumps({'job_id': job, 'status': 'running'}))
        self.assertEqual(self.rig.get_job(job)['status'], 'unknown')
        self.assertEqual(self.moving_packets(), [])
        with self.assertRaises(ValueError):
            self.rig.get_job('../anything')

    async def test_validation_before_motion(self):
        for value in (float('nan'), float('inf'), True, '10', 21):
            with self.assertRaises(ValueError):
                VelocityCommand(value, 0, 1)
        with self.assertRaises(ValueError):
            VelocityCommand(1, 1, 1)
        with self.assertRaises(ValueError):
            VelocityCommand(1, 0, 3)
        with self.assertRaises(ValueError):
            TakeRequest(VelocityCommand(1, 0, 1), -1)
        with self.assertRaises(ValueError):
            ShotInput(goal='test', vendor_bytes='hello')

    async def test_same_request_never_replays(self):
        request_id = 'b' * 32
        command = VelocityCommand(10, 0, .1)
        job = self.rig.move_gimbal(command, request_id)
        self.assertEqual(self.rig.move_gimbal(command, request_id), job)
        await self.wait_job(job)
        count = len(self.transport.packets)
        self.assertEqual(self.rig.move_gimbal(command, request_id), job)
        self.assertEqual(len(self.transport.packets), count)
        with self.assertRaises(ValueError):
            self.rig.move_gimbal(VelocityCommand(5, 0, .1), request_id)

    async def test_new_move_rejected_while_stop_in_flight(self):
        task = asyncio.create_task(self.rig.stop())
        await asyncio.sleep(.01)
        with self.assertRaises(RuntimeError):
            self.rig.move_gimbal(VelocityCommand(10, 0, 1))
        with self.assertRaises(RuntimeError):
            await self.controller.drive(VelocityCommand(10, 0, 1))
        await task
        self.assertEqual(self.moving_packets(), [])

    async def test_malformed_short_packet_resynchronizes(self):
        parser = DUMLParser()
        packets = list(parser.feed(bytes.fromhex('55000400') + speed_packet(10)))
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].cmd, 12)
