import argparse
import asyncio
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from dollybot.client import request
from dollybot.service import Shot


class ShotInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    goal: str = Field(min_length=1, max_length=2000)
    seconds: float = Field(default=3, ge=.1, le=30)
    lead_s: float = Field(default=1, ge=0, le=10)
    tail_s: float = Field(default=3, ge=0, le=10)
    forward_m_s: float = 0
    left_m_s: float = 0
    yaw_rad_s: float = 0
    pan_deg_s: float = 0
    tilt_deg_s: float = 0
    motion_seconds: float = Field(default=1, gt=0, le=2)
    import_to_kino: bool = True


def make_server(url='ws://127.0.0.1:8767/api', request_fn=request):
    server = FastMCP('Dollybot')

    async def call(method, params=None):
        return await asyncio.to_thread(request_fn, method, params, url)

    @server.tool(description='Read connectivity and active job from the persistent Dollybot service. No hardware connection is created by this MCP client.')
    async def get_status() -> dict:
        return await call('get_status')

    @server.tool(description='Connect selected devices through the persistent service; does not move or record.')
    async def connect(devices: list[str]) -> dict:
        return await call('connect', {'devices': devices})

    @server.tool(description='Record one goal-directed take, optionally with bounded base/gimbal motion, download the original, and optionally import into Kino. Requires supervision for motion. Use a fresh 32-character lowercase hex request_id and retain it on retries. Poll get_job; never automatically replay failed or unknown takes.')
    async def capture_take(shot: ShotInput, request_id: str) -> dict:
        validated = Shot(**shot.model_dump())
        return await call('capture_take', {'request_id': request_id, 'shot': asdict(validated)})

    @server.tool(description='Read persistent take progress/result, local clip metadata, Kino media IDs, or error. A completed transport request is not physical verification.')
    async def get_job(job_id: str) -> dict:
        return await call('get_job', {'job_id': job_id})

    @server.tool(description='Interrupt the active take and stop both motion drivers. Recording cleanup runs in the service; poll the job until terminal.')
    async def stop() -> dict:
        return await call('stop')

    return server


def main():
    parser = argparse.ArgumentParser(description='Thin stdio MCP client of the running Dollybot service')
    parser.add_argument('--server', default='ws://127.0.0.1:8767/api')
    make_server(parser.parse_args().server).run(transport='stdio')
