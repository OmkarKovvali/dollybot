import argparse
import anyio
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, ConfigDict, Field

from dollybot.controllers.om8 import BleTransport, OM8, VelocityCommand
from dollybot.rig import Rig, TakeRequest


class MotionInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    pan_deg_s: float = Field(default=0, ge=-20, le=20)
    tilt_deg_s: float = Field(default=0, ge=-20, le=20)
    duration_s: float = Field(gt=0, le=2)

    def command(self):
        return VelocityCommand(**self.model_dump())


def make_server(address: str, camera_url: str, output: Path, rig_factory=None):
    @asynccontextmanager
    async def lifespan(_):
        rig = rig_factory() if rig_factory else Rig(OM8(BleTransport(address)), camera_url, output)
        try:
            await rig.controller.connect()
            yield rig
        finally:
            with anyio.CancelScope(shield=True):
                await rig.close()

    server = FastMCP('Dollybot', lifespan=lifespan)

    def rig(ctx):
        return ctx.request_context.lifespan_context

    @server.tool(description='Read gimbal connectivity and the active job; telemetry is not a verified pose.')
    async def get_status(ctx: Context) -> dict:
        return rig(ctx).get_status()

    @server.tool(description='Run one bounded timed pan or tilt. Use a fresh 32-character lowercase hex request_id, retaining it for retries. Returns a job ID; does not record video. No exact angle positioning.')
    async def move_gimbal(motion: MotionInput, request_id: str, ctx: Context) -> dict:
        return {'job_id': rig(ctx).move_gimbal(motion.command(), request_id)}

    @server.tool(description='Start Moblin recording, lead in, move, stop movement, record tail, and download the original clip. Use a fresh 32-character lowercase hex request_id, retaining it for retries. Poll the job; no automatic retakes.')
    async def capture_take(motion: MotionInput, request_id: str, ctx: Context, lead_s: float = 1, tail_s: float = 3, verify_copy: bool = False) -> dict:
        request = TakeRequest(motion.command(), lead_s, tail_s, verify_copy)
        return {'job_id': rig(ctx).capture_take(request, request_id)}

    @server.tool(description='Read a job result, including clip path and capture validation. Never resubmit an uncertain physical command automatically.')
    async def get_job(job_id: str, ctx: Context) -> dict:
        return rig(ctx).get_job(job_id)

    @server.tool(description='Interrupt the active job and send gimbal stop commands. Recording cleanup is asynchronous; poll the job. A sent stop is not proof of physical stop.')
    async def stop(ctx: Context) -> dict:
        return await rig(ctx).stop()

    return server


def main():
    parser = argparse.ArgumentParser(description='Dollybot stdio MCP server; one process owns the rig')
    parser.add_argument('--gimbal-address', required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, default=Path.home() / 'Movies/Dollybot/takes')
    args = parser.parse_args()
    make_server(args.gimbal_address, args.url, args.output).run(transport='stdio')
