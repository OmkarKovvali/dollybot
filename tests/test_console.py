import asyncio
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from dollybot.console import Console
from dollybot.controllers.flow_base import BaseState
from dollybot.controllers.om8 import GimbalState


class ConsoleTests(unittest.IsolatedAsyncioTestCase):
    def make_console(self):
        base = Mock(connected=True)
        base.state.return_value = BaseState(None, True, None, False)
        gimbal = Mock()
        gimbal.state.return_value = GimbalState(True, False, None, None, False)
        console = Console(base, gimbal, 'http://phone', Path('/tmp/unused'))
        console.base_driver = Mock(stop=AsyncMock(), move=AsyncMock())
        console.gimbal_driver = Mock(stop=AsyncMock(), move=AsyncMock())
        console.send = AsyncMock()
        return console

    async def test_watchdog_stops_both_devices(self):
        console = self.make_console()
        console.motion['base_move'] = True
        console.last_input = time.monotonic() - 1
        task = asyncio.create_task(console.watchdog())
        await asyncio.sleep(.08)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        console.base_driver.stop.assert_awaited()
        console.gimbal_driver.stop.assert_awaited()

    async def test_stale_motion_does_not_execute(self):
        console = self.make_console()
        await console.command({'action': 'base_move', 'time': 0, 'forward': .08})
        console.base_driver.move.assert_not_awaited()

    async def test_stop_failure_does_not_skip_other_device(self):
        console = self.make_console()
        console.base_driver.stop.side_effect = ConnectionError('offline')
        await console.stop()
        console.gimbal_driver.stop.assert_awaited_once()
        self.assertFalse(console.stopping)
        self.assertTrue(any('error' in call.args[0] for call in console.send.call_args_list))

    async def test_motion_limits_checked_before_execution(self):
        console = self.make_console()
        await console.command({'action': 'base_move', 'time': time.time()*1000, 'forward': 1})
        console.base_driver.move.assert_not_awaited()
        self.assertEqual(console.motion, {})
