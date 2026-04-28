"""Security validation for MCP browser automation"""

import re
from typing import List


class SecurityValidator:
    """Validate MCP tool inputs for security"""

    # Whitelist of allowed CSS selector patterns
    ALLOWED_SELECTOR_PATTERNS = [
        r"^button[\.\[\]#\w\-=:\s\"']*$",           # button selectors
        r"^input[\.\[\]#\w\-=:\s\"']*$",            # input selectors
        r"^select[\.\[\]#\w\-=:\s\"']*$",           # select selectors
        r"^\[data-testid=['\"]?[\w\-]+['\"]?\]$",   # data-testid
        r"^form[\.\[\]#\w\-=:\s\"']*$",             # form selectors
        r"^\.\w[\w\-]*$",                            # class selectors
        r"^#\w[\w\-]*$",                             # id selectors
        r"^a[\.\[\]#\w\-=:\s\"']*$",                # anchor selectors
        r"^div[\.\[\]#\w\-=:\s\"']*$",              # div selectors
        r"^span[\.\[\]#\w\-=:\s\"']*$",             # span selectors
    ]

    # Allowed URL paths (relative)
    ALLOWED_URL_PATHS = [
        r"^/ai-demo$",
        r"^/ai-demo/.*",
    ]

    # Rate limiting: max operations per minute
    MAX_OPERATIONS_PER_MINUTE = 60

    @classmethod
    def validate_selector(cls, selector: str) -> tuple[bool, str]:
        """Validate CSS selector against whitelist"""
        if not selector or len(selector) > 200:
            return False, "Selector too long or empty"

        # Check for dangerous patterns first
        dangerous_patterns = [
            r"script", r"iframe", r"onclick", r"onerror", r"onload",
            r"alert", r"eval", r"javascript:", r"data:", r"vbscript:",
            r"<", r">", r"&", r"onclick", r"onerror", r"onload",
        ]
        selector_lower = selector.lower()
        for pattern in dangerous_patterns:
            if pattern in selector_lower:
                return False, f"Dangerous pattern detected: {pattern}"

        # Remove quotes for validation
        clean_selector = selector.replace('"', "'")

        for pattern in cls.ALLOWED_SELECTOR_PATTERNS:
            if re.match(pattern, clean_selector):
                return True, ""

        # If no pattern matched, only allow specific safe patterns
        # Must start with . # or [ or known tags
        if re.match(r"^[\w\-\.\[\]#=\":' \*\+~>]+$", clean_selector):
            # Additional check: no more than 3 levels deep
            if clean_selector.count('>') <= 2:
                return True, ""

        return False, f"Selector '{selector}' not in whitelist"

    @classmethod
    def validate_url_path(cls, url_path: str) -> tuple[bool, str]:
        """Validate URL path is allowed"""
        if not url_path:
            return False, "URL path cannot be empty"

        # Normalize path
        if not url_path.startswith("/"):
            url_path = "/" + url_path

        for pattern in cls.ALLOWED_URL_PATHS:
            if re.match(pattern, url_path):
                return True, ""

        return False, f"URL path '{url_path}' not allowed"

    @classmethod
    def validate_text_input(cls, text: str, max_length: int = 1000) -> tuple[bool, str]:
        """Validate text input"""
        if not isinstance(text, str):
            return False, "Input must be string"

        if len(text) > max_length:
            return False, f"Input too long (max {max_length} chars)"

        return True, ""

    @classmethod
    def validate_timeout(cls, timeout_ms: int) -> tuple[bool, str]:
        """Validate timeout value"""
        if not isinstance(timeout_ms, int):
            return False, "Timeout must be integer"

        if timeout_ms < 100 or timeout_ms > 30000:
            return False, "Timeout must be between 100-30000 ms"

        return True, ""
