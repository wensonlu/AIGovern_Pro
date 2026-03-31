#!/bin/bash
# 快捷启动Atomic for AIGovern_Pro

cd /Users/wclu/AIGovern_Pro
/Users/wclu/.bun/bin/bun run /Users/wclu/Atomic_Workspace/src/cli.ts chat -a claude "$@"
