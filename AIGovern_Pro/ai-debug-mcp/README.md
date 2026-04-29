# AI Debug MCP

> Production-grade debugging tools for AI Agents — browser DevTools Protocol + Python Runtime console/network monitoring via MCP.

[![npm version](https://img.shields.io/badge/npm-v0.1.0-blue)](https://www.npmjs.com/package/ai-debug-mcp)
[![Node.js >= 20](https://img.shields.io/badge/node-%3E%3D%2020-brightgreen)](https://nodejs.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

**AI Debug MCP** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives AI coding agents (Claude Code, Cursor, etc.) the ability to introspect running applications:

- **Browser Runtime** — captures `console.log/warn/error/info/debug` and HTTP network traffic via Playwright's Chrome DevTools Protocol (CDP) integration
- **Python Runtime** — monitors `print()`, `logging`, `httpx` and `requests` calls inside Python scripts via a lightweight SDK

The AI Agent calls one of 8 structured tools, gets back typed JSON, and can validate/assert on the results — enabling self-healing, auto-debugging, and regression detection loops.

## Features

- **8 MCP Tools** for structured debugging and validation
- **Browser** and **Python** runtime support in one server
- **Playwright CDP** for full browser DevTools access
- **Python SDK** with one-line `import ai_debug_sdk` integration
- **HTTP API** bridge — MCP server polls Python runtime over HTTP (port 9310)
- **Structured JSON output** — all results are machine-readable for AI agents
- **Time-range filtering** on all snapshot tools

---

## Quick Start

### Installation

```bash
npm install ai-debug-mcp
```

### Configure as MCP Server

Add to your MCP client config (Claode, Cursor, etc.):

```json
{
  "mcpServers": {
    "ai-debug": {
      "command": "node",
      "args": ["/path/to/node_modules/ai-debug-mcp/dist/index.js"]
    }
  }
}
```

### Browser Runtime — Quick Demo

```typescript
import { chromium } from "ai-debug-mcp";

const browser = await chromium.launch();
const page = await browser.newPage();

// Enable console & network capture on the page...
// Then query via MCP tools (see Tools section below)
```

### Python Runtime — One-Line Integration

```python
import ai_debug_sdk  # Enables global monitoring on import

import requests

response = requests.get("https://api.example.com/users")
print("Status:", response.status_code)

# AI Agent queries monitoring data via MCP tools
# Python SDK exposes HTTP endpoints at http://127.0.0.1:9310
```

---

## 8 MCP Tools

### 1. `debug_console_snapshot`

Capture browser or Python console logs.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "timeRange": {
    "since": 1745884800000,
    "until": 1745888400000
  },
  "level": "log" | "error" | "warn" | "info" | "debug"
}
```

**Output:**

```json
{
  "entries": [
    {
      "type": "console",
      "runtime": "browser",
      "level": "log",
      "timestamp": 1745884800000,
      "messages": ["User clicked button"],
      "source": "https://example.com/app.js:42",
      "context": { "url": "https://example.com/" }
    }
  ],
  "total": 1,
  "timeRange": { "since": 1745884800000, "until": 1745888400000 }
}
```

---

### 2. `debug_network_snapshot`

Capture HTTP network requests and responses.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "timeRange": { "since": 1745884800000 },
  "urlPattern": "/api/v1/*",
  "status": 200
}
```

**Output:**

```json
{
  "entries": [
    {
      "type": "network",
      "runtime": "browser",
      "id": "https://api.example.com/api/v1/users",
      "method": "GET",
      "url": "https://api.example.com/api/v1/users",
      "path": "/api/v1/users",
      "domain": "api.example.com",
      "status": 200,
      "statusText": "OK",
      "responseTime": 145,
      "requestHeaders": { "Authorization": "Bearer ***" },
      "responseHeaders": { "content-type": "application/json" },
      "responseBody": { "users": [...] },
      "validated": false,
      "validationResult": { "符合预期": false },
      "timestamp": 1745884800000
    }
  ],
  "total": 1,
  "timeRange": { "since": 1745884800000, "until": 1745884801000 }
}
```

---

### 3. `debug_error_summary`

Get a consolidated error and network-failure report.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "timeRange": { "since": 1745884800000 }
}
```

**Output:**

```json
{
  "summary": {
    "type": "error_summary",
    "runtime": "browser",
    "errorCount": 2,
    "errors": [
      {
        "message": "TypeError: Cannot read property 'x' of undefined",
        "stack": "at app.js:42\nat onClick (app.js:10)",
        "count": 3,
        "firstSeen": 1745884800000,
        "lastSeen": 1745884810000
      }
    ],
    "networkFailCount": 1,
    "networkFails": [
      { "url": "https://api.example.com/users", "status": 500, "message": "Internal Server Error" }
    ]
  },
  "hasErrors": true,
  "hasNetworkFails": true
}
```

---

### 4. `debug_validate_response`

Validate that a network response contains expected JSON fields.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "expectedFields": ["token", "userId", "expiresAt"],
  "responseId": "https://api.example.com/auth"
}
```

**Output:**

```json
{
  "responseId": "https://api.example.com/auth",
  "validated": false,
  "expectedFields": ["token", "userId", "expiresAt"],
  "presentFields": ["token", "userId"],
  "missingFields": ["expiresAt"],
  "extraFields": ["refreshToken"],
  "detail": "Missing required fields: expiresAt. Unexpected extra fields: refreshToken."
}
```

---

### 5. `debug_check_errors`

Check whether specific error patterns appear in the console.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "expectedErrors": ["TypeError", "Cannot read", "undefined is not an object"]
}
```

**Output:**

```json
{
  "matched": true,
  "matchedErrors": ["TypeError"],
  "unmatchedErrors": ["Cannot read", "undefined is not an object"],
  "foundErrors": [
    {
      "message": "TypeError: Cannot read property 'x' of undefined",
      "stack": "at app.js:42",
      "count": 2,
      "firstSeen": 1745884800000,
      "lastSeen": 1745884810000
    }
  ]
}
```

---

### 6. `debug_assert_network`

Assert that a specific URL returned an expected HTTP status code.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "url": "https://api.example.com/users",
  "expectedStatus": 200
}
```

**Output:**

```json
{
  "url": "https://api.example.com/users",
  "expectedStatus": 200,
  "actualStatus": 200,
  "matched": true,
  "detail": "Assertion passed: URL https://api.example.com/users returned 200."
}
```

---

### 7. `debug_collect_all`

Capture a full snapshot of console logs, network requests, and errors in one call.

**Input:**

```json
{
  "runtime": "browser" | "python",
  "timeRange": { "since": 1745884800000 }
}
```

**Output:**

```json
{
  "console": [...],
  "network": [...],
  "errorSummary": { "type": "error_summary", ... },
  "stats": {
    "consoleTotal": 12,
    "networkTotal": 5,
    "errorCount": 1,
    "networkFailCount": 0
  }
}
```

---

## Browser DevTools Integration (Playwright)

### Setup

```bash
npm install ai-debug-mcp playwright
npx playwright install chromium
```

### Usage

```typescript
import { chromium } from "playwright";
import { BrowserRuntime } from "ai-debug-mcp/runtimes/browser-runtime";

const runtime = new BrowserRuntime();
await runtime.launch();

// Create a page and navigate
const page = await runtime.attach("https://example.com");

// Interact with the page (triggers console/network events)
await page.click("#submit-btn");
await page.waitForResponse("**/api/**");

// Query captured data via MCP tools
const consoleEntries = runtime.getConsoleEntries();
const networkEntries = runtime.getNetworkEntries();
```

### CDP Access

`BrowserRuntime` uses Playwright's CDP session to intercept:
- `Page.consoleAPICalled` — all `console.log/warn/error/info/debug` events
- `Network.requestWillBeSent` — outbound HTTP requests
- `Network.responseReceived` — HTTP responses with headers + body

---

## Python Runtime Integration

### Installation

```bash
pip install ai-debug-sdk
# or
pip install -e python-sdk/
```

### One-Line Import (Recommended)

```python
import ai_debug_sdk  # Auto-starts monitoring on import

import requests
import logging

logging.basicConfig(level=logging.INFO)

response = requests.get("https://api.example.com/users")
print(f"Got {len(response.json())} users")
```

### Manual Control

```python
from ai_debug_sdk import enable, disable, get_console_entries, get_network_entries

# Disable during startup
disable()

# ... your app initialization code ...

# Re-enable for the test phase
enable()

# ... run your test ...

# Collect results
console_logs = get_console_entries()
network_logs = get_network_entries()
```

### HTTP API Server (for MCP Server Integration)

```python
import ai_debug_sdk

# Start HTTP server on port 9310 (MCP server polls this)
ai_debug_sdk.start_server(port=9310)

# Your script runs normally...
# MCP server calls http://127.0.0.1:9310/console and /network
```

**HTTP Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/console` | GET | Returns console entries. Optional `?since=<timestamp>` filter |
| `/network` | GET | Returns network entries. Optional `?since=<timestamp>` filter |
| `/health` | GET | Health check |

**Example:**

```bash
curl "http://127.0.0.1:9310/console?since=1745884800000"
curl "http://127.0.0.1:9310/network?since=1745884800000"
```

### Supported HTTP Libraries

- `requests` — automatic request/response capture
- `httpx` — automatic request/response capture

### Python Version

Requires **Python 3.10+**.

---

## AI Agent Integration

### Claude Code

```json
{
  "mcpServers": {
    "ai-debug": {
      "command": "node",
      "args": ["/full/path/to/ai-debug-mcp/dist/index.js"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/home/user/.cache/playwright"
      }
    }
  }
}
```

### Cursor

Add to Cursor settings → MCP Servers:

```json
{
  "mcpServers": {
    "ai-debug": {
      "command": "node",
      "args": ["/full/path/to/ai-debug-mcp/dist/index.js"]
    }
  }
}
```

### OpenAI Agents SDK

```python
from openai import OpenAI

client = OpenAI()

# Your agent code...
# ai_debug_sdk captures all console/network activity

# Agent can call MCP tools:
# - debug_console_snapshot
# - debug_network_snapshot
# - debug_validate_response
# etc.
```

---

## Architecture

```
┌─────────────────┐      MCP stdio       ┌────────────────────────┐
│  AI Agent       │ ◄──────────────────► │  ai-debug-mcp Server    │
│  (Claude Code,  │                      │  (Node.js / TypeScript) │
│   Cursor, etc.)  │                      └──────────┬─────────────┘
└─────────────────┘                                     │
                                           ┌────────────┴────────────┐
                              CDP (WebSocket) │                         │ HTTP GET
                               ┌────────────▼────────────┐  ┌────────▼────────┐
                               │  Browser (Chromium via  │  │  Python Runtime  │
                               │   Playwright)           │  │  (ai_debug_sdk)  │
                               │  - console events       │  │  - print/logging │
                               │  - network events       │  │  - httpx/requests│
                               └─────────────────────────┘  └─────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | TypeScript 5.x |
| Runtime | Node.js 20+ |
| MCP Protocol | @modelcontextprotocol/sdk (StdioServerTransport) |
| Browser Automation | Playwright 1.x (CDP) |
| Python SDK | Python 3.10+, httpx, requests |
| Python HTTP | Built-in `http.server` (port 9310) |
| Testing | Vitest |
| Type checking | TypeScript (strict mode) |

---

## Development

```bash
# Install dependencies
cd ai-debug-mcp
npm install

# Type check
npm run build

# Run tests
npm test

# Watch mode
npm run dev
```

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
