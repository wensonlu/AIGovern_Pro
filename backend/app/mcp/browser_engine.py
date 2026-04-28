"""Playwright-based browser automation engine for MCP"""

import base64
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    # Provide meaningful error if playwright not installed
    raise ImportError("playwright required: pip install playwright")


@dataclass
class ToolResult:
    """Result of a browser tool execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


class BrowserEngine:
    """Playwright-based browser engine for page automation"""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}

    async def initialize(self) -> None:
        """Start browser"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def shutdown(self) -> None:
        """Close browser and cleanup"""
        # Close all pages
        for page in self._pages.values():
            try:
                await page.close()
            except Exception:
                pass

        # Close all contexts
        for context in self._contexts.values():
            try:
                await context.close()
            except Exception:
                pass

        # Close browser
        if self._browser:
            await self._browser.close()

        # Close playwright
        if self._playwright:
            await self._playwright.stop()

        self._playwright = None
        self._browser = None
        self._contexts = {}
        self._pages = {}

    async def get_or_create_page(self, session_id: str, url: str = "http://localhost:3001/ai-demo") -> Page:
        """Get existing page or create new one"""
        if session_id in self._pages:
            return self._pages[session_id]

        # Create new context and page
        context = await self._browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")

        self._contexts[session_id] = context
        self._pages[session_id] = page
        return page

    async def close_session(self, session_id: str) -> None:
        """Close page and context for session"""
        if session_id in self._pages:
            try:
                await self._pages[session_id].close()
            except Exception:
                pass
            del self._pages[session_id]

        if session_id in self._contexts:
            try:
                await self._contexts[session_id].close()
            except Exception:
                pass
            del self._contexts[session_id]

    async def click(self, session_id: str, selector: str) -> ToolResult:
        """Click an element"""
        try:
            page = await self.get_or_create_page(session_id)
            await page.click(selector, timeout=5000)
            return ToolResult(success=True, message=f"Clicked {selector}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to click {selector}", error=str(e))

    async def input_text(self, session_id: str, selector: str, text: str) -> ToolResult:
        """Type text into input field"""
        try:
            page = await self.get_or_create_page(session_id)
            await page.fill(selector, text, timeout=5000)
            return ToolResult(success=True, message=f"Typed '{text}' into {selector}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to type into {selector}", error=str(e))

    async def navigate(self, session_id: str, url_path: str) -> ToolResult:
        """Navigate to URL path (restricted to localhost)"""
        try:
            page = await self.get_or_create_page(session_id)
            # Only allow demo page routes
            if not url_path.startswith("/"):
                url_path = "/" + url_path
            full_url = f"http://localhost:3001{url_path}"
            await page.goto(full_url, wait_until="networkidle", timeout=10000)
            return ToolResult(success=True, message=f"Navigated to {url_path}", data={"url": full_url})
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to navigate", error=str(e))

    async def wait_for_element(self, session_id: str, selector: str, timeout_ms: int = 5000) -> ToolResult:
        """Wait for element to appear"""
        try:
            page = await self.get_or_create_page(session_id)
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return ToolResult(success=True, message=f"Element {selector} is visible")
        except Exception as e:
            return ToolResult(success=False, message=f"Element {selector} not found within {timeout_ms}ms", error=str(e))

    async def get_page_state(self, session_id: str) -> ToolResult:
        """Get current page state (URL, title, visible text)"""
        try:
            page = await self.get_or_create_page(session_id)
            url = page.url
            title = await page.title()

            # Get visible text (simplified)
            visible_text = await page.evaluate(
                """() => {
                    const elem = document.body;
                    return elem ? elem.innerText.slice(0, 5000) : '';
                }"""
            )

            # Get form data
            form_data = await page.evaluate(
                """() => {
                    const data = {};
                    document.querySelectorAll('input, select, textarea').forEach(el => {
                        if (el.name) {
                            if (el.type === 'checkbox') {
                                data[el.name] = el.checked;
                            } else if (el.type === 'radio') {
                                if (el.checked) data[el.name] = el.value;
                            } else {
                                data[el.name] = el.value;
                            }
                        }
                    });
                    return data;
                }"""
            )

            return ToolResult(
                success=True,
                message="Page state retrieved",
                data={
                    "url": url,
                    "title": title,
                    "visible_text": visible_text[:1000],  # Limit text
                    "form_data": form_data,
                }
            )
        except Exception as e:
            return ToolResult(success=False, message="Failed to get page state", error=str(e))

    async def screenshot(self, session_id: str) -> ToolResult:
        """Take screenshot and return as base64"""
        try:
            page = await self.get_or_create_page(session_id)
            screenshot_bytes = await page.screenshot()
            base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
            return ToolResult(
                success=True,
                message="Screenshot captured",
                data={"image": f"data:image/png;base64,{base64_image}"}
            )
        except Exception as e:
            return ToolResult(success=False, message="Failed to capture screenshot", error=str(e))


# Global browser engine instance
browser_engine = BrowserEngine()
