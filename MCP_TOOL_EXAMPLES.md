/**
 * Example MCP Tool Definitions and Responses
 * This file shows how Claude should format tool calls and what responses look like
 */

// ============================================
// Tool Call Format (Claude sends)
// ============================================

// 1. CLICK
{
  "tool": "click",
  "params": {
    "selector": "button[data-testid=submit-btn]"
  }
}

// 2. INPUT
{
  "tool": "input",
  "params": {
    "selector": "input[data-testid=product-name]",
    "text": "Laptop Pro"
  }
}

// 3. NAVIGATE
{
  "tool": "navigate",
  "params": {
    "url_path": "/ai-demo"
  }
}

// 4. WAIT_FOR_ELEMENT
{
  "tool": "wait_for_element",
  "params": {
    "selector": ".success-message",
    "timeout_ms": 5000
  }
}

// 5. GET_PAGE_STATE
{
  "tool": "get_page_state",
  "params": {}
}

// 6. SCREENSHOT
{
  "tool": "screenshot",
  "params": {}
}

// ============================================
// Stream Response Format (Backend sends)
// ============================================

// Line 1: Initial screenshot
{"type": "screenshot", "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}

// Line 2: User task echoed
{"type": "task", "task": "Fill in product name as Laptop and submit the form"}

// Line 3: AI decides to click input field
{"type": "tool_call", "tool": "input", "params": {"selector": "input[data-testid=product-name]", "text": "Laptop"}, "sequence": 1}

// Line 4: Tool result
{"type": "tool_result", "tool": "input", "success": true, "message": "Typed 'Laptop' into input[data-testid=product-name]", "sequence": 1}

// Line 5: Screenshot after action
{"type": "screenshot", "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "sequence": 1}

// Line 6: Next tool call - click submit
{"type": "tool_call", "tool": "click", "params": {"selector": "button[data-testid=submit-btn]"}, "sequence": 2}

// Line 7: Tool result
{"type": "tool_result", "tool": "click", "success": true, "message": "Clicked button[data-testid=submit-btn]", "sequence": 2}

// Line 8: Screenshot after submit
{"type": "screenshot", "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "sequence": 2}

// Line 9: AI response text
{"type": "response", "content": "I have successfully filled in the product name as 'Laptop' and submitted the form. The page now shows a success message."}

// Line 10: Task complete
{"type": "done", "tool_calls": 2}

// ============================================
// Error Response Format
// ============================================

{"type": "error", "message": "Invalid selector: 'iframe src=evil.com' not in whitelist", "error": "security_validation_failed"}

// ============================================
// Example Page State Response
// ============================================

{
  "url": "http://localhost:3001/ai-demo",
  "title": "AI Assistant Demo",
  "visible_text": "Interactive Demo Form\nProduct Name\nEnter product name...\nDescription\nEnter product description...",
  "form_data": {
    "productName": "Laptop",
    "description": "High performance laptop",
    "category": "electronics",
    "price": "1299",
    "quantity": "5"
  }
}

// ============================================
// Common Tool Call Patterns
// ============================================

// Pattern 1: Fill a form
[
  {"tool": "input", "params": {"selector": "[data-testid=product-name]", "text": "Laptop"}},
  {"tool": "input", "params": {"selector": "[data-testid=description]", "text": "High-end laptop"}},
  {"tool": "input", "params": {"selector": "[data-testid=price]", "text": "1299"}},
  {"tool": "click", "params": {"selector": "[data-testid=submit-btn]"}},
  {"tool": "screenshot", "params": {}}
]

// Pattern 2: Wait and verify
[
  {"tool": "click", "params": {"selector": "button.delete"}},
  {"tool": "wait_for_element", "params": {"selector": ".confirmation-dialog", "timeout_ms": 3000}},
  {"tool": "click", "params": {"selector": "button.confirm"}},
  {"tool": "screenshot", "params": {}}
]

// Pattern 3: Dropdown selection
[
  {"tool": "click", "params": {"selector": "select[data-testid=category]"}},
  {"tool": "wait_for_element", "params": {"selector": "option[value=electronics]", "timeout_ms": 2000}},
  {"tool": "click", "params": {"selector": "option[value=electronics]"}},
  {"tool": "screenshot", "params": {}}
]

// Pattern 4: Multi-page flow
[
  {"tool": "navigate", "params": {"url_path": "/ai-demo"}},
  {"tool": "wait_for_element", "params": {"selector": "form", "timeout_ms": 5000}},
  {"tool": "get_page_state", "params": {}},
  {"tool": "screenshot", "params": {}}
]
