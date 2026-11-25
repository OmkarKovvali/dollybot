import argparse
from pathlib import Path
import shlex
import shutil


def main():
    parser = argparse.ArgumentParser(description='Install the physical Dollybot skill into Kino')
    parser.add_argument('--destination', type=Path, default=Path.home() / 'Library/Application Support/Kino/skills/dollybot')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    uv = shutil.which('uv')
    if not uv:
        parser.error('Install uv first')
    command = f'{shlex.quote(uv)} run --frozen --project {shlex.quote(str(root))} dollybot-client'
    content = (root / 'skills/dollybot/SKILL.md').read_text().replace('__DOLLYBOT_CLIENT__', command)
    target = args.destination.expanduser() / 'SKILL.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w' if args.force else 'x') as output:
        output.write(content)
    print(target)


if __name__ == '__main__':
    main()
