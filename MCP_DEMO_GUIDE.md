# MCP Browser Control Demo - Quick Start Guide

## Overview

This demo shows Claude AI autonomously controlling a web browser through Model Context Protocol (MCP). Users describe tasks in plain English, and the AI automatically:
- Clicks buttons and links
- Fills form fields
- Takes screenshots
- Navigates pages

## Architecture

```
User Input → Frontend Chat Console → Backend /api/demo/ai-task
→ Claude LLM (with tool definitions) → Tool Calls → Playwright Browser
→ Screenshots + Page State → Real-time Operation Log
```

## Quick Start

### 1. Install Dependencies (Backend)

```bash
cd backend
source venv/bin/activate

# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium
```

### 2. Start Backend

```bash
cd backend
source venv/bin/activate
python run.py
```

Backend will start at `http://localhost:8000`
- Health check: `GET http://localhost:8000/health`
- Demo API: `POST http://localhost:8000/api/demo/ai-task`

### 3. Start Frontend

```bash
cd frontend
pnpm install  # if needed
pnpm dev
```

Frontend will start at `http://localhost:3001`

### 4. Open Demo Page

Navigate to: `http://localhost:3001/ai-demo`

## Using the Demo

### Left Panel: Interactive Form
- Contains test fields: Product Name, Description, Category, Price, Quantity
- Has buttons: Reset, Submit
- All elements have `data-testid` attributes for AI selector targeting

### Right Panel: AI Assistant Console

**Tabs:**
- **Operations** - Real-time log of tool calls and results
- **Screenshot** - Current page screenshot

**How to Use:**
1. Type a task: "Fill in product name with Laptop"
2. Click "Send" button
3. Watch AI execute:
   - Tool calls appear in log
   - Screenshots update after each action
   - Results show success/errors

### Demo Tasks to Try

```
1. "Click the reset button"
   → AI clicks [data-testid=reset-btn]

2. "Fill in product name as Laptop"
   → AI types "Laptop" into product name field

3. "Select Electronics from category"
   → AI clicks category dropdown and selects option

4. "Fill all fields with sample data and submit"
   → AI fills: name, description, category, price, quantity, then clicks submit

5. "Take a screenshot of the current form"
   → AI captures page state as image
```

## API Endpoints

### POST /api/demo/ai-task
Execute AI-controlled task and stream results.

**Request:**
```json
{
  "task": "Click the reset button",
  "session_id": "session_12345"  // optional, auto-generated if not provided
}
```

**Response:** NDJSON stream (1 JSON object per line)
```
{"type": "screenshot", "data": "data:image/png;base64,..."}
{"type": "task", "task": "Click the reset button"}
{"type": "tool_call", "tool": "click", "params": {"selector": "[data-testid=reset-btn]"}, "sequence": 1}
{"type": "tool_result", "tool": "click", "success": true, "message": "Clicked...", "sequence": 1}
{"type": "screenshot", "data": "data:image/png;base64,...", "sequence": 1}
{"type": "done", "tool_calls": 1}
```

### GET /api/demo/screenshot/{session_id}
Get current screenshot for a session.

**Response:**
```json
{
  "image": "data:image/png;base64,..."
}
```

### POST /api/demo/session/{session_id}/reset
Reset a browser session (clear page state).

**Response:**
```json
{
  "status": "ok",
  "message": "Session session_12345 reset"
}
```

### GET /api/demo/health
Health check for demo API.

**Response:**
```json
{
  "status": "ok",
  "service": "mcp-demo"
}
```

## MCP Tools Available

| Tool | Purpose | Example |
|------|---------|---------|
| `click` | Click element | `{"tool": "click", "params": {"selector": "button.submit"}}` |
| `input` | Type text | `{"tool": "input", "params": {"selector": "input[name=name]", "text": "John"}}` |
| `navigate` | Go to page | `{"tool": "navigate", "params": {"url_path": "/ai-demo"}}` |
| `wait_for_element` | Wait for element | `{"tool": "wait_for_element", "params": {"selector": ".result", "timeout_ms": 5000}}` |
| `get_page_state` | Get page info | `{"tool": "get_page_state", "params": {}}` |
| `screenshot` | Capture screen | `{"tool": "screenshot", "params": {}}` |

## Security Features

- **Selector Whitelist**: Only CSS selectors matching safe patterns allowed
- **URL Restrictions**: Demo page only (`/ai-demo`)
- **Text Validation**: Max 1000 characters per input
- **Timeout Limits**: 100-30000ms per tool call
- **Session Timeout**: 30 minutes inactivity
- **Rate Limiting**: 60 operations/minute

## File Structure

```
backend/app/
├── mcp/                          # MCP module
│   ├── __init__.py
│   ├── page_state.py            # Session state manager
│   ├── browser_engine.py        # Playwright wrapper
│   ├── security.py              # Validation middleware
│   └── tools.py                 # Individual tool implementations
├── services/mcp_service.py      # Orchestration layer
└── api/demo.py                  # API routes

frontend/src/
├── pages/AIAssistantDemo.tsx    # Demo page
├── components/MCPConsole/       # AI console components
│   ├── MCPConsole.tsx           # Main chat interface
│   ├── OperationLog.tsx         # Operation timeline
│   └── ScreenshotViewer.tsx     # Screenshot display
└── services/mcp-demo-api.ts     # Frontend API client
```

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
# Kill if needed
kill -9 <PID>

# Verify Playwright is installed
python -c "import playwright; print('✓ Playwright installed')"

# Check Chromium binary
ls ~/.cache/ms-playwright/chromium-*/chrome-mac/
```

### Frontend can't connect to backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/app/main.py`
- Verify frontend proxy config in `frontend/vite.config.ts`

### No browser screenshots
- Verify Chromium installed: `playwright install chromium`
- Check browser logs: `cat /tmp/backend.log`
- Verify display settings if running headless

### AI not executing tools
- Check LLM API key configured: `echo $ANTHROPIC_AUTH_TOKEN`
- Check OpenRouter endpoint: `echo $ANTHROPIC_BASE_URL`
- Verify tool parsing in `/api/demo/ai-task` response

## Example Integration

```typescript
// Frontend: Call AI task endpoint
const response = await fetch('/api/demo/ai-task', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    task: 'Click the reset button',
    session_id: 'user-123'
  })
});

// Stream events as they arrive
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split('\n');

  for (const line of lines) {
    if (!line) continue;
    const event = JSON.parse(line);

    if (event.type === 'screenshot') {
      setScreenshot(event.data);
    }
    if (event.type === 'tool_call') {
      console.log(`Executing: ${event.tool}`);
    }
    if (event.type === 'error') {
      console.error(event.message);
    }
  }
}
```

## Performance Notes

- **First screenshot**: 2-5 seconds (Chromium startup)
- **Tool execution**: 500ms-1s per operation
- **Session memory**: ~50MB per active session (browser context)
- **Max concurrent sessions**: Limited by system RAM (recommend 3-5)

## Next Steps

1. **Production Deployment**: Update CORS whitelist, add authentication
2. **Multi-user**: Add session persistence (Redis), per-user quotas
3. **Advanced Tools**: Add keyboard input, mouse moves, file uploads
4. **Analytics**: Log all tool calls, success rates, user patterns
5. **Error Recovery**: Implement retry logic, fallback selectors

## Support

For issues or questions:
1. Check backend logs: `tail -f /tmp/backend.log`
2. Check browser logs: `ls ~/.cache/ms-playwright/chromium-*/logs/`
3. Enable debug mode: `DEBUG=* pnpm dev` (frontend)

---

**Last Updated**: 2026-04-28
**Status**: MVP Ready - All 6 tools working, tested with Claude
