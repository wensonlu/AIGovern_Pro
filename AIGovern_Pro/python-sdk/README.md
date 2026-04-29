# AI Debug SDK (Python)

> Python runtime monitoring for AI Agents — captures console output, logging, and HTTP traffic with zero-configuration import.

[![Python >= 3.10](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://www.python.org/)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/ai-debug-sdk/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

**AI Debug SDK** is a Python package that gives AI coding agents visibility into Python script execution:

- Captures `print()` calls and `logging` module output
- Intercepts `httpx` and `requests` HTTP requests/responses
- Exposes a local HTTP API (port 9310) for the MCP server to query collected data
- Requires **zero configuration** — just `import ai_debug_sdk`

Used together with the [ai-debug-mcp](https://github.com/your-org/ai-debug-mcp) Node.js server, AI agents can inspect Python script behavior through the same 8 MCP tools.

## Requirements

- **Python 3.10+**
- `httpx >= 0.27.0` (optional, for HTTP monitoring)
- `requests >= 2.32.0` (optional, for HTTP monitoring)

---

## Installation

### Via pip

```bash
pip install ai-debug-sdk
```

### Via pyproject.toml

```toml
[tool.poetry.dependencies]
python = "^3.10"
ai-debug-sdk = "^0.1.0"
```

### Editable install (development)

```bash
pip install -e python-sdk/
```

### Install with dev dependencies

```bash
pip install -e python-sdk/[dev]
```

---

## Quick Start

### One-Line Integration (Recommended)

```python
import ai_debug_sdk  # Auto-starts monitoring on import

import requests

response = requests.get("https://api.example.com/users")
print(f"Got {len(response.json())} users")

# ai_debug_sdk has captured:
# - the print() call
# - the HTTP request/response
# These are available via HTTP API at http://127.0.0.1:9310
```

### Start HTTP Server Manually

If you want the MCP server to be able to query data while your script runs:

```python
import ai_debug_sdk

# Start the HTTP API server (MCP server polls this)
ai_debug_sdk.start_server(port=9310)

# Your script runs...
import requests
requests.get("https://api.example.com/health")

# MCP server calls:
# GET http://127.0.0.1:9310/console
# GET http://127.0.0.1:9310/network
```

### Manual Enable/Disable

```python
from ai_debug_sdk import enable, disable, get_console_entries, clear

# Disable during initialization phase
disable()

# ... your app startup code ...

# Re-enable for the test phase
enable()

# ... run your test scenario ...

# Collect results
logs = get_console_entries(since=None)  # all entries
clear()  # reset for next run
```

---

## API Reference

### `ai_debug_sdk`

#### `enable()`

Enable global console and network monitoring.

```python
from ai_debug_sdk import enable
enable()
```

#### `disable()`

Disable global monitoring.

```python
from ai_debug_sdk import disable
disable()
```

#### `get_console_entries(since: int | None = None) -> list[dict]`

Get captured console log entries.

```python
from ai_debug_sdk import get_console_entries

# All entries
logs = get_console_entries()

# Only entries newer than timestamp (Unix ms)
recent = get_console_entries(since=1745884800000)
```

**Returns:** List of console entry dicts:

```python
{
    "type": "console",
    "runtime": "python",
    "level": "info",       # "info" | "warn" | "error" | "log" | "debug"
    "timestamp": 1745884800000,
    "messages": ["Health check passed"],
    "source": "script.py:42",
}
```

#### `get_network_entries(since: int | None = None) -> list[dict]`

Get captured HTTP request/response entries.

```python
from ai_debug_sdk import get_network_entries

# All entries
calls = get_network_entries()

# Only entries newer than timestamp (Unix ms)
recent = get_network_entries(since=1745884800000)
```

**Returns:** List of network entry dicts:

```python
{
    "type": "network",
    "runtime": "python",
    "id": "https://api.example.com/users",
    "method": "GET",
    "url": "https://api.example.com/users",
    "path": "/users",
    "domain": "api.example.com",
    "status": 200,
    "statusText": "OK",
    "responseTime": 87,          # milliseconds
    "requestHeaders": {...},
    "responseHeaders": {...},
    "responseBody": {"users": [...]},
    "validated": False,
    "validationResult": {"符合预期": False},
    "timestamp": 1745884800000,
}
```

#### `clear()`

Clear all collected entries.

```python
from ai_debug_sdk import clear
clear()
```

#### `start_server(port: int = 9310)`

Start the HTTP API server (for MCP server integration).

```python
from ai_debug_sdk import start_server
start_server(port=9310)  # Runs in a daemon thread
```

#### `stop_server()`

Stop the HTTP API server.

```python
from ai_debug_sdk import stop_server
stop_server()
```

---

## HTTP API

When `start_server()` is called, the SDK starts an HTTP server on `127.0.0.1:<port>` with the following endpoints:

### `GET /console`

Returns captured console entries.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | int | Unix timestamp in ms. Return only entries newer than this |

**Example:**

```bash
curl "http://127.0.0.1:9310/console?since=1745884800000"
```

**Response:**

```json
[
  {
    "type": "console",
    "runtime": "python",
    "level": "info",
    "timestamp": 1745884800000,
    "messages": ["Health check passed"],
    "source": "script.py:42"
  }
]
```

---

### `GET /network`

Returns captured HTTP network entries.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | int | Unix timestamp in ms. Return only entries newer than this |

**Example:**

```bash
curl "http://127.0.0.1:9310/network?since=1745884800000"
```

**Response:**

```json
[
  {
    "type": "network",
    "runtime": "python",
    "id": "https://api.example.com/users",
    "method": "GET",
    "url": "https://api.example.com/users",
    "path": "/users",
    "domain": "api.example.com",
    "status": 200,
    "statusText": "OK",
    "responseTime": 87,
    "requestHeaders": {"user-agent": "python-requests/..."},
    "responseHeaders": {"content-type": "application/json"},
    "responseBody": {"users": [...]},
    "validated": false,
    "validationResult": {"符合预期": false},
    "timestamp": 1745884800000
  }
]
```

---

### `GET /health`

Health check endpoint.

**Example:**

```bash
curl http://127.0.0.1:9310/health
```

**Response:**

```json
{
  "status": "ok",
  "timestamp": 1745884800000
}
```

---

## MCP Server Integration

The Python SDK is designed to work with the **ai-debug-mcp** Node.js MCP server. The integration architecture:

```
┌─────────────────┐      MCP stdio       ┌──────────────────────────┐
│  AI Agent       │ ◄──────────────────► │  ai-debug-mcp (Node.js)   │
│  (Claude Code)  │                      │  - routes MCP calls        │
└─────────────────┘                      │  - calls Python HTTP API   │
                                          └──────────┬───────────────┘
                                                     │ HTTP GET
                                          ┌──────────▼───────────────┐
                                          │  Python Script           │
                                          │  - import ai_debug_sdk   │
                                          │  - runs user code        │
                                          │  - HTTP API on :9310     │
                                          └──────────────────────────┘
```

**Setup:**

1. In your Python script, import ai_debug_sdk and start the server:

```python
import ai_debug_sdk

ai_debug_sdk.start_server(port=9310)

# Your script code...
import requests
response = requests.get("https://api.example.com/api/data")
```

2. Configure ai-debug-mcp to connect to the Python runtime. The MCP server's `python-runtime.ts` polls `http://127.0.0.1:9310` for data.

---

## Console Entry Format

Each `print()` call and `logging` message generates a `ConsoleEntry`:

```python
{
    "type": "console",           # always "console"
    "runtime": "python",         # always "python" for this SDK
    "level": "info",             # log | info | warn | error | debug
    "timestamp": 1745884800000,  # Unix ms
    "messages": ["Hello world"], # list of string arguments
    "source": "myscript.py:15",   # file:line of the print/log call
}
```

## Network Entry Format

Each HTTP request generates a `NetworkEntry`:

```python
{
    "type": "network",           # always "network"
    "runtime": "python",
    "id": "https://...",         # unique request ID (URL)
    "method": "GET",             # HTTP method
    "url": "https://...",
    "path": "/api/users",        # URL path
    "domain": "api.example.com",
    "status": 200,               # HTTP status code
    "statusText": "OK",
    "responseTime": 87,          # response duration in ms
    "requestHeaders": {...},
    "requestBody": None,         # request body (if any)
    "responseHeaders": {...},
    "responseBody": {...},       # parsed JSON response (if any)
    "validated": False,
    "validationResult": {"符合预期": False},
    "timestamp": 1745884800000,
}
```

---

## Supported HTTP Libraries

| Library | Support Level |
|---------|--------------|
| `requests` | ✅ Full capture |
| `httpx` | ✅ Full capture |

---

## Version Requirements

| Dependency | Minimum Version |
|------------|----------------|
| Python | 3.10+ |
| `requests` | 2.32.0 (optional) |
| `httpx` | 0.27.0 (optional) |

---

## LICENSE

MIT License

```
Copyright (c) 2026 AIGovern_Pro Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
