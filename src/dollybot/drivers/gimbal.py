from dollybot.controllers.om8 import OM8, MotionResult, VelocityCommand


class GimbalDriver:
    def __init__(self, controller: OM8):
        self.controller = controller

    async def move(self, motion: VelocityCommand) -> MotionResult:
        return await self.controller.drive(motion)

    async def stop(self):
        return await self.controller.stop()
