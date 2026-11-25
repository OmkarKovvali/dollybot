import asyncio
import json
import tempfile
import time
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

from dollybot.agent import make_server
from dollybot.console import Console
from dollybot.controllers.flow_base import BaseState
from dollybot.controllers.om8 import GimbalState
from dollybot.service import Jobs, Shot, SlideShot


@dataclass
class Result:
    outcome: str = 'command_completed'


class ServiceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Mock(connected=True)
        base.state.return_value = BaseState(None, True, None, False)
        gimbal = Mock()
        gimbal.state.return_value = GimbalState(True, False, None, None, False)
        self.console = Console(base, gimbal, 'http://fixture', Path(self.tmp.name))
        self.console.camera = Mock()
        self.console.camera.status.return_value = {'recording': False}
        self.console.base_driver = Mock(move=AsyncMock(return_value=Result()), stop=AsyncMock())
        self.console.gimbal_driver = Mock(move=AsyncMock(return_value=Result()), stop=AsyncMock())
        self.console.send = AsyncMock()
        self.captures = 0
        self.imports = 0

        def capture(camera, seconds, output, verify, tail, action, wait, on_state):
            self.captures += 1
            on_state(True)
            action()
            on_state(False)
            wait(tail)
            return {'local_path': '/fixture.mp4', 'video': {'duration_seconds': seconds + tail}}

        def imported(path):
            self.imports += 1
            return {'media': [{'mediaId': 'fixture'}]}

        self.console.jobs = Jobs(self.console, capture, imported)

    async def asyncTearDown(self):
        await self.console.jobs.close()
        self.tmp.cleanup()

    def shot(self, **kwargs):
        return Shot(goal='fixture goal', seconds=.1, lead_s=0, tail_s=0, motion_seconds=.05, **kwargs)

    async def finish(self):
        await asyncio.wait_for(self.console.jobs.task, 3)

    async def test_capture_import_and_duplicate_request(self):
        shot = self.shot()
        self.console.jobs.submit('a'*32, shot)
        self.console.jobs.submit('a'*32, shot)
        await self.finish()
        self.console.jobs.submit('a'*32, shot)
        self.assertEqual((self.captures, self.imports), (1, 1))
        self.assertEqual(self.console.jobs.get('a'*32)['kino']['media'][0]['mediaId'], 'fixture')
        with self.assertRaises(ValueError):
            self.console.jobs.submit('a'*32, self.shot(pan_deg_s=1))

    async def test_ui_cannot_move_during_agent_take(self):
        self.console.jobs.submit('b'*32, self.shot())
        await self.console.command({'action': 'base_move', 'time': time.time()*1000, 'forward': .08})
        self.console.base_driver.move.assert_not_awaited()
        await self.finish()

    async def test_manual_recording_blocks_agent(self):
        self.console.previous = set()
        with self.assertRaises(RuntimeError):
            self.console.jobs.submit('b'*32, self.shot())
        self.assertEqual(self.captures, 0)

    async def test_stop_interrupts_lead_and_prevents_motion(self):
        self.console.jobs.submit('c'*32, Shot(goal='test stop', seconds=.1, lead_s=1, tail_s=0, motion_seconds=.05, forward_m_s=.05))
        await asyncio.sleep(.03)
        await self.console.stop()
        await self.finish()
        self.console.base_driver.move.assert_not_awaited()
        self.assertEqual(self.console.jobs.get('c'*32)['status'], 'cancelled')
        self.assertEqual(self.imports, 0)

    async def test_both_drivers_used_and_stopped(self):
        self.console.jobs.submit('d'*32, self.shot(forward_m_s=.05, pan_deg_s=5))
        await self.finish()
        self.console.base_driver.move.assert_awaited_once()
        self.console.gimbal_driver.move.assert_awaited_once()
        self.console.base_driver.stop.assert_awaited()
        self.console.gimbal_driver.stop.assert_awaited()

    async def test_import_failure_keeps_capture_and_never_recaptures(self):
        self.console.jobs.import_fn = Mock(side_effect=TimeoutError('import uncertain'))
        self.console.jobs.submit('e'*32, self.shot())
        await self.finish()
        job = self.console.jobs.get('e'*32)
        self.assertEqual(job['status'], 'failed')
        self.assertEqual(job['result']['local_path'], '/fixture.mp4')
        self.console.jobs.submit('e'*32, self.shot())
        self.assertEqual(self.captures, 1)

    async def test_restart_reports_unknown_and_does_not_replay(self):
        self.console.jobs.current = {'job_id': 'f'*32, 'request': self.shot().__dict__, 'status': 'running'}
        self.console.jobs.save()
        self.assertEqual(self.console.jobs.get('f'*32)['status'], 'unknown')
        self.console.jobs.submit('f'*32, self.shot())
        self.assertEqual(self.captures, 0)

    async def test_api_and_browser_disconnect_do_not_cancel_agent(self):
        async with serve(self.console.route, '127.0.0.1', 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f'ws://127.0.0.1:{port}/control', proxy=None):
                async with connect(f'ws://127.0.0.1:{port}/api', proxy=None) as api:
                    await api.send(json.dumps({'method': 'capture_take', 'params': {'request_id':'1'*32, 'shot':self.shot().__dict__}}))
                    self.assertIn('result', json.loads(await api.recv()))
            await self.finish()
            self.assertEqual(self.console.jobs.get('1'*32)['status'], 'completed')

    async def test_mcp_is_proxy_only_and_keeps_job_on_client_exit(self):
        from mcp.shared.memory import create_connected_server_and_client_session
        calls = []
        def request(method, params, url):
            calls.append(method)
            return {'job_id': '2'*32}
        server = make_server(request_fn=request)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool('capture_take', {'request_id': '2'*32, 'shot': {'goal':'proxy test'}})
            self.assertFalse(result.isError)
        self.assertEqual(calls, ['capture_take'])
        self.assertEqual({t.name for t in await server.list_tools()}, {'get_status','connect','capture_take','plan_preset','capture_preset','get_job','stop'})

    async def test_slide_preserves_tracking_and_does_not_command_gimbal(self):
        shot = SlideShot(direction='right', lead_s=0, tail_s=0)
        self.console.jobs.submit('3'*32, shot)
        self.console.jobs.submit('3'*32, shot)
        await self.finish()
        self.console.camera.request.assert_not_called()
        self.console.gimbal_driver.move.assert_not_awaited()
        self.console.gimbal_driver.stop.assert_not_awaited()
        move = self.console.base_driver.move.call_args.args[0]
        self.assertEqual(move.direction, 'right')
        self.assertAlmostEqual(move.distance_m, 1.8288)
        self.assertEqual(move.speed_m_s, .5)
        self.console.base_driver.stop.assert_awaited()
        job = self.console.jobs.get('3'*32)
        self.assertEqual(job['status'], 'completed')
        self.assertEqual(job['plan']['distance_control'], 'timed_velocity_estimate')
        self.assertEqual((self.captures, self.imports), (1, 1))
        with self.assertRaises(ValueError):
            self.console.jobs.submit('3'*32, SlideShot(direction='left'))

    async def test_manual_control_resumes_after_kino_take(self):
        self.console.jobs.submit('7'*32, SlideShot(direction='left', lead_s=0, tail_s=0))
        await self.finish()
        self.console.base_driver.move.reset_mock()
        self.console.last_input = time.monotonic()
        await self.console.command({'action': 'base_move', 'time': time.time()*1000, 'left': .08})
        self.console.base_driver.move.assert_awaited_once()
        self.assertEqual(self.console.base_driver.move.call_args.args[0].duration_s, 2)
        self.assertFalse(self.console.jobs.busy)
        await asyncio.sleep(0)
        states = [call.args[0]['state'] for call in self.console.send.call_args_list if 'state' in call.args[0]]
        self.assertIsNone(states[-1]['active_job'])

    async def test_preset_api_requires_direction_and_preview_has_no_side_effects(self):
        async with serve(self.console.route, '127.0.0.1', 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with connect(f'ws://127.0.0.1:{port}/api', proxy=None) as api:
                await api.send(json.dumps({'method': 'capture_preset', 'params': {'request_id': '4'*32, 'shot': {'preset': 'slide'}}}))
                self.assertIn('direction', json.loads(await api.recv())['error'])
                await api.send(json.dumps({'method': 'plan_preset', 'params': {'direction': 'backward'}}))
                plan = json.loads(await api.recv())['result']
                self.assertEqual(plan['direction'], 'backward')
                self.assertAlmostEqual(plan['motion_seconds'], 5.6576)
        self.assertEqual(self.captures, 0)
        self.console.base_driver.move.assert_not_awaited()

    async def test_slide_cancel_during_lead_never_moves(self):
        self.console.jobs.submit('5'*32, SlideShot(direction='left'))
        await asyncio.sleep(.03)
        await self.console.stop()
        await self.finish()
        self.console.base_driver.move.assert_not_awaited()
        self.assertEqual(self.console.jobs.get('5'*32)['status'], 'cancelled')

    async def test_mcp_preset_direction_required(self):
        from mcp.shared.memory import create_connected_server_and_client_session
        calls = []
        def request(method, params, url):
            calls.append((method, params))
            return {'status': 'running'}
        server = make_server(request_fn=request)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool('capture_preset', {'request_id': '6'*32, 'shot': {'preset': 'slide'}})
            self.assertTrue(result.isError)
            self.assertEqual(calls, [])
            result = await client.call_tool('capture_preset', {'request_id': '6'*32, 'shot': {'direction': 'forward'}})
            self.assertFalse(result.isError)
        self.assertEqual(calls[0][0], 'capture_preset')
        self.assertEqual(calls[0][1]['shot']['direction'], 'forward')

    def test_invalid_shots_rejected(self):
        for args in ({'forward_m_s': .2}, {'pan_deg_s': 5, 'tilt_deg_s': 5}, {'seconds': float('nan')}, {'seconds': True}, {'motion_seconds': 3}):
            with self.assertRaises(ValueError):
                Shot(goal='test', **args)
