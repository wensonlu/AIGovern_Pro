#!/bin/bash
mkdir -p /tmp/aigovern_logs
cd /Users/wclu/AIGovern_Pro/backend
source venv/bin/activate
exec python run.py
