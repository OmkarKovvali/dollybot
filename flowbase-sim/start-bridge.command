#!/bin/zsh
set -e
cd -- "${0:A:h}"
if command -v node >/dev/null 2>&1; then
  exec node bridge/server.mjs
fi
exec "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" bridge/server.mjs
