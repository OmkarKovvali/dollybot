import argparse
import json
from urllib.parse import urlsplit
from websockets.sync.client import connect


def request(method: str, params: dict | None = None, url: str = 'ws://127.0.0.1:8767/api') -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != 'ws' or parsed.hostname != '127.0.0.1' or parsed.path != '/api':
        raise ValueError('Use the local Dollybot ws://127.0.0.1:PORT/api endpoint')
    with connect(url, proxy=None, open_timeout=3, close_timeout=1, ping_interval=None) as ws:
        ws.send(json.dumps({'method': method, 'params': params or {}}))
        result = json.loads(ws.recv(timeout=30))
    if 'error' in result:
        raise RuntimeError(result['error'])
    return result['result']


def main():
    parser = argparse.ArgumentParser(description='Client of the running Dollybot service; never opens hardware connections')
    parser.add_argument('--server', default='ws://127.0.0.1:8767/api')
    parser.add_argument('method', choices=['get_status', 'connect', 'capture_take', 'get_job', 'stop'])
    parser.add_argument('params', nargs='?', default='{}', help='JSON parameters; retain request_id for retries')
    args = parser.parse_args()
    try:
        print(json.dumps(request(args.method, json.loads(args.params), args.server), indent=2))
    except Exception as error:
        parser.exit(1, f'{type(error).__name__}: {error}\n')


if __name__ == '__main__':
    main()
