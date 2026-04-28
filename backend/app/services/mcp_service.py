"""MCP service orchestration - routes tool calls and manages sessions"""

from typing import Dict, Any, AsyncIterator, Optional
from app.mcp.browser_engine import browser_engine, ToolResult
from app.mcp.page_state import page_state_manager
from app.mcp.security import SecurityValidator
import json


class MCPService:
    """Orchestrate MCP tool execution and session management"""

    # Track operation counts per minute for rate limiting
    _operation_counts: Dict[str, int] = {}

    async def initialize(self) -> None:
        """Initialize MCP service"""
        await browser_engine.initialize()
        await page_state_manager.initialize()

    async def shutdown(self) -> None:
        """Shutdown MCP service"""
        await browser_engine.shutdown()
        await page_state_manager.shutdown()

    async def execute_tool(
        self,
        session_id: str,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """Execute a single MCP tool with security validation"""

        # Validate tool exists
        if tool_name not in self.AVAILABLE_TOOLS:
            return ToolResult(
                success=False,
                message=f"Tool '{tool_name}' not found",
                error="invalid_tool"
            )

        # Execute tool
        if tool_name == "click":
            selector = kwargs.get("selector")
            is_valid, error = SecurityValidator.validate_selector(selector)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid selector: {error}")
            return await browser_engine.click(session_id, selector)

        elif tool_name == "input":
            selector = kwargs.get("selector")
            text = kwargs.get("text")
            is_valid, error = SecurityValidator.validate_selector(selector)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid selector: {error}")
            is_valid, error = SecurityValidator.validate_text_input(text)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid text: {error}")
            return await browser_engine.input_text(session_id, selector, text)

        elif tool_name == "navigate":
            url_path = kwargs.get("url_path", "/ai-demo")
            is_valid, error = SecurityValidator.validate_url_path(url_path)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid URL: {error}")
            return await browser_engine.navigate(session_id, url_path)

        elif tool_name == "wait_for_element":
            selector = kwargs.get("selector")
            timeout_ms = kwargs.get("timeout_ms", 5000)
            is_valid, error = SecurityValidator.validate_selector(selector)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid selector: {error}")
            is_valid, error = SecurityValidator.validate_timeout(timeout_ms)
            if not is_valid:
                return ToolResult(success=False, message=f"Invalid timeout: {error}")
            return await browser_engine.wait_for_element(session_id, selector, timeout_ms)

        elif tool_name == "get_page_state":
            return await browser_engine.get_page_state(session_id)

        elif tool_name == "screenshot":
            result = await browser_engine.screenshot(session_id)
            if result.success and result.data:
                # Save screenshot to state
                page_state_manager.update_state(session_id, last_screenshot=result.data.get("image"))
            return result

        else:
            return ToolResult(success=False, message="Tool not implemented")

    async def stream_ai_task(
        self,
        session_id: str,
        task: str,
        llm_client: Any,
        db: Any = None,
    ) -> AsyncIterator[dict]:
        """Stream AI task execution with tool calls (DOM-based, no screenshots)"""
        import re

        # Create or get session
        state = page_state_manager.get_session(session_id)
        if not state:
            state = page_state_manager.create_session(session_id)

        # Emit user task
        yield {
            "type": "task",
            "task": task,
        }

        # Build system prompt with available tools
        system_prompt = self._build_system_prompt()
        full_prompt = f"{system_prompt}\n\nUser Task: {task}"

        try:
            # Get LLM response
            response_text = await llm_client.generate_text(full_prompt, max_tokens=2048)

            # Parse tool calls from response (JSON format)
            tool_calls = []

            # Try to extract JSON objects from the response
            # Handle nested structures by finding matching braces
            i = 0
            while i < len(response_text):
                # Look for opening brace of a JSON object
                idx = response_text.find('{', i)
                if idx == -1:
                    break

                # Try to find the matching closing brace
                brace_count = 0
                end_idx = idx
                for j in range(idx, len(response_text)):
                    if response_text[j] == '{':
                        brace_count += 1
                    elif response_text[j] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = j + 1
                            break

                # Try to parse as JSON
                try:
                    potential_json = response_text[idx:end_idx]
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict) and "tool" in parsed:
                        tool_calls.append(parsed)
                    i = end_idx
                except (json.JSONDecodeError, ValueError):
                    i = idx + 1

            # Execute tool calls
            tool_calls_count = 0
            for tool_call in tool_calls:
                tool_calls_count += 1
                tool_name = tool_call.get("tool")
                tool_params = tool_call.get("params", {})

                # Emit tool call
                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "params": tool_params,
                    "sequence": tool_calls_count,
                }

                # Execute tool
                result = await self.execute_tool(session_id, tool_name, **tool_params)

                # Emit tool result
                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "success": result.success,
                    "message": result.message,
                    "error": result.error,
                    "data": result.data,
                    "sequence": tool_calls_count,
                }

            # Emit LLM response
            yield {
                "type": "response",
                "content": response_text,
            }

            # Emit done
            yield {
                "type": "done",
                "tool_calls": tool_calls_count,
            }

        except Exception as e:
            yield {
                "type": "error",
                "message": f"Task execution failed: {str(e)}",
                "error": str(e),
            }

    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools"""
        return """You are an AI assistant that controls a web browser to complete user tasks.

The page has pre-defined interactive elements identified by data-testid attributes:
- reset-btn: Reset button
- product-name: Product name input field
- description: Product description text area
- category: Category dropdown select
- price: Price input field
- quantity: Quantity input field
- submit-btn: Submit form button

Available tools (format JSON and return in your response):
1. {"tool": "click", "params": {"selector": "[data-testid='ELEMENT_ID']"}}
   - Use data-testid selectors to click buttons and interactive elements

2. {"tool": "input", "params": {"selector": "[data-testid='ELEMENT_ID']", "text": "TEXT"}}
   - Fill text into input fields using data-testid

3. {"tool": "navigate", "params": {"url_path": "/path"}}

4. {"tool": "wait_for_element", "params": {"selector": "[data-testid='ELEMENT_ID']"}}
   - Wait for elements to be ready

5. {"tool": "get_page_state", "params": {}}
   - Get current DOM state with all interactive elements and their values
   - Returns: elements array with testid, tag, type, value, disabled status, etc.

Instructions:
- Always start by calling get_page_state to see current element states
- Use data-testid attributes for selectors (e.g., [data-testid='product-name'])
- Do NOT take screenshots - use get_page_state to verify element state
- Think step by step about how to complete the task
- Format each tool call as a JSON object on its own line
- Report results after each action

Example:
Plan: Get page state, then fill in product name and click submit
{"tool": "get_page_state", "params": {}}
Result: [Check element status - product-name is empty, submit-btn is enabled]
{"tool": "input", "params": {"selector": "[data-testid='product-name']", "text": "Laptop"}}
Result: Product name filled successfully
{"tool": "click", "params": {"selector": "[data-testid='submit-btn']"}}
Result: Form submitted successfully
"""

    AVAILABLE_TOOLS = [
        "click",
        "input",
        "navigate",
        "wait_for_element",
        "get_page_state",
        "screenshot",
    ]

    TOOL_DEFINITIONS = [
        {
            "name": "click",
            "description": "Click an element on the page",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to click"
                    }
                },
                "required": ["selector"]
            }
        },
        {
            "name": "input",
            "description": "Type text into an input field",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the input field"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    }
                },
                "required": ["selector", "text"]
            }
        },
        {
            "name": "navigate",
            "description": "Navigate to a page URL path",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url_path": {
                        "type": "string",
                        "description": "URL path (e.g. /ai-demo)"
                    }
                },
                "required": ["url_path"]
            }
        },
        {
            "name": "wait_for_element",
            "description": "Wait for an element to appear on the page",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element"
                    },
                    "timeout_ms": {
                        "type": "integer",
                        "description": "Timeout in milliseconds (default 5000)"
                    }
                },
                "required": ["selector"]
            }
        },
        {
            "name": "get_page_state",
            "description": "Get current page state including URL, title, and visible content",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "screenshot",
            "description": "Take a screenshot of the current page",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
    ]


# Global MCP service instance
mcp_service = MCPService()
