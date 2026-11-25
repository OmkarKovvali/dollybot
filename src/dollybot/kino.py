import json
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener


def call_tool(name: str, arguments: dict, url: str = 'http://127.0.0.1:45680/mcp') -> dict:
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': arguments}}
    request = Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'})
    with build_opener(ProxyHandler({})).open(request, timeout=120) as response:
        raw = response.read().decode()
    messages = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: ')] if raw.startswith('event:') or raw.startswith('data:') else [json.loads(raw)]
    message = next(m for m in messages if m.get('id') == 1)
    if 'error' in message:
        raise RuntimeError(f"Kino RPC error: {message['error']}")
    result = message['result']
    if result.get('isError'):
        raise RuntimeError(f"Kino tool failed: {result.get('content')}")
    if 'structuredContent' in result:
        return result['structuredContent']
    for item in result.get('content', []):
        if item.get('type') == 'text':
            try:
                return json.loads(item['text'])
            except json.JSONDecodeError:
                pass
    return result


def import_clip(path: str) -> dict:
    absolute = Path(path).resolve(strict=True)
    result = call_tool('addMediaToKino', {'sources': [{'type': 'localFile', 'absolutePath': str(absolute)}], 'binName': 'Dollybot takes'})
    if not result.get('media'):
        raise RuntimeError(f'Kino did not return imported media; inspect before retrying: {result}')
    return result
