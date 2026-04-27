#!/bin/bash
mkdir -p /tmp/aigovern_logs
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20.11.1 >/dev/null 2>&1 || nvm use 20 >/dev/null 2>&1 || true
export PATH="$HOME/.nvm/versions/node/v20.11.1/bin:$PATH"
cd /Users/wclu/AIGovern_Pro/frontend
exec pnpm dev
