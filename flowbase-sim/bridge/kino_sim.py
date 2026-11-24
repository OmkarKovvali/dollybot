#!/usr/bin/env python3
"""Small shell-facing client for Kino's existing agent. No robot drivers or external dependencies."""
import argparse
import json
import math
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import uuid

CONFIG = Path(__file__).resolve().parent.parent / '.runtime' / 'bridge.json'

def request(route, payload=None):
    try:
        config = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        raise RuntimeError('The simulator bridge is not running. Start flowbase-sim/start-bridge.command, then open http://127.0.0.1:8766.')
    # Configuration cannot redirect a shot request away from the intended local simulator.
    if config.get('url') != 'http://127.0.0.1:8766':
        raise RuntimeError('Unexpected simulator address')
    headers = {'Authorization': 'Bearer ' + config['token'], 'Content-Type': 'application/json'}
    req = urllib.request.Request(config['url'] + route, headers=headers, data=None if payload is None else json.dumps(payload).encode())
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try: message = json.load(error).get('error', str(error.code))
        except (ValueError, OSError): message = str(error.code)
        raise RuntimeError(message)
    except urllib.error.URLError:
        raise RuntimeError('The local simulator bridge is unavailable. Restart start-bridge.command.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    status = commands.add_parser('status'); status.add_argument('--job')
    commands.add_parser('capabilities')
    commands.add_parser('stop')
    run = commands.add_parser('run', help='Orbit, dolly, or slide; free simulation by default')
    run.add_argument('--kind', choices=['orbit','dolly','slide'], required=True)
    run.add_argument('--radius', type=float, default=2.5)
    run.add_argument('--sweep', type=float, default=90, help='Degrees, including multiple turns')
    run.add_argument('--distance', type=float, default=1.2)
    run.add_argument('--duration', type=float, default=16)
    run.add_argument('--fixed-heading', action='store_true')
    run.add_argument('--constrained', action='store_true', help='Opt in to the original preview limits')
    drive = commands.add_parser('drive', help='Simultaneous translation and rotation from current pose')
    for key in ['vx','vy','omega']: drive.add_argument('--'+key, type=float, default=0)
    drive.add_argument('--frame', choices=['body','world'], default='body')
    drive.add_argument('--duration', type=float, required=True)
    move = commands.add_parser('move', help='Relative or absolute planar pose interpolation')
    for key in ['x','y','yaw']: move.add_argument('--'+key, type=float)
    move.add_argument('--absolute', action='store_true')
    move.add_argument('--frame', choices=['body','world'], default='world')
    move.add_argument('--easing', choices=['smooth','linear'], default='smooth')
    move.add_argument('--duration', type=float, required=True)
    rotate = commands.add_parser('rotate', help='Rotate in place; signed degrees preserve full turns')
    rotate.add_argument('--degrees', type=float, required=True)
    rotate.add_argument('--duration', type=float, required=True)
    pose = commands.add_parser('pose', help='Instantly place the simulated base at a world pose')
    for key in ['x','y','yaw']: pose.add_argument('--'+key, type=float, required=True)
    motion = commands.add_parser('motion', help='Arbitrary JSON motion, timed path, or mixed sequence; angles in radians')
    source = motion.add_mutually_exclusive_group(required=True)
    source.add_argument('--json'); source.add_argument('--file', type=Path)
    for command in [run,drive,move,rotate,pose,motion]:
        command.add_argument('--reason', default='Movement requested in Kino')
        command.add_argument('--request-id', default=None)
        command.add_argument('--wait', action='store_true')
        command.add_argument('--replace', action='store_true', help='Stop an active job before this new movement')
    args = parser.parse_args()
    if args.command == 'status':
        if args.job and not all(c.isalnum() or c in '_-' for c in args.job): raise RuntimeError('Invalid job ID')
        result = request('/api/jobs/' + args.job if args.job else '/api/state')
    elif args.command == 'capabilities': result = request('/api/capabilities')
    elif args.command == 'stop': result = request('/api/stop', {})
    else:
        payload = {'request_id':args.request_id or str(uuid.uuid4()), 'reason':args.reason}
        if args.command == 'run':
            route = '/api/shots'
            payload['shot'] = {'kind':args.kind,'radius':args.radius,'sweepDeg':args.sweep,'distance':args.distance,'duration':args.duration,'faceSubject':not args.fixed_heading,'unconstrained':not args.constrained}
        else:
            route = '/api/motions'
            if args.command == 'drive':
                spec = {'kind':'drive','vx':args.vx,'vy':args.vy,'omega':math.radians(args.omega),'frame':args.frame,'duration':args.duration}
            elif args.command == 'move':
                spec = {'kind':'move','relative':not args.absolute,'frame':args.frame,'easing':args.easing,'duration':args.duration}
                for k in ['x','y','yaw']:
                    value = getattr(args,k)
                    if value is not None: spec[k] = math.radians(value) if k=='yaw' else value
            elif args.command == 'rotate':
                spec = {'kind':'move','yaw':math.radians(args.degrees),'duration':args.duration}
            elif args.command == 'pose':
                spec = {'kind':'pose','x':args.x,'y':args.y,'yaw':math.radians(args.yaw)}
            else:
                try: spec = json.loads(args.json if args.json is not None else args.file.read_text())
                except (ValueError,OSError) as error: raise RuntimeError('Cannot read motion JSON: '+str(error))
            payload['motion'] = spec
        # A retry of the same request must never cancel its own in-flight job.
        if args.replace:
            current = request('/api/state')['active_job']
            if current and current['id'] != payload['request_id']:
                request('/api/stop', {})
                deadline = time.monotonic()+5
                while request('/api/state')['active_job']:
                    if time.monotonic()>deadline: raise RuntimeError('Stop is still pending; check status before replacing')
                    time.sleep(.2)
        result = request(route, payload)
        if args.wait:
            print(json.dumps({'accepted': True, 'job_id': result['id'], 'simulation_only': True}), flush=True)
            deadline = time.monotonic() + min(55, result['duration'] + 15)
            while result['status'] not in ['completed','cancelled','failed'] and time.monotonic() < deadline:
                time.sleep(.4); result = request('/api/jobs/' + result['id'])
            if result['status'] not in ['completed','cancelled','failed']:
                result['note'] = 'Still pending; check this job ID. Do not submit the movement again.'
    print(json.dumps(result, indent=2))
    return 1 if result.get('status') in ['failed','cancelled'] else 0

if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError, ValueError, KeyError) as error:
        print(json.dumps({'error':str(error),'simulation_only':True}), file=sys.stderr);sys.exit(1)
