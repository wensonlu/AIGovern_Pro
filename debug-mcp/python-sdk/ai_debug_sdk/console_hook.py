"""
Console hook for Python - captures print() and logging output.
Following SPEC.md Section 4.6
"""

import sys
import logging
import io
from datetime import datetime
from contextlib import contextmanager
from typing import Callable
from .collector import Collector


class ConsoleHook:
    """Hook into Python's print and logging to capture console output."""
    
    def __init__(self, collector: Collector):
        self._collector = collector
        self._original_excepthook = None
        self._original_write = None
        self._original_flush = None
        
    def install(self):
        """Install console hooks (redirect print, capture logging)."""
        # Capture stdout write
        self._original_write = sys.stdout.write
        self._original_flush = sys.stdout.flush
        
        def hooked_write(text):
            self._capture_text(text, "stdout")
            return self._original_write(text)
        
        sys.stdout.write = hooked_write  # type: ignore
        
        # Also hook stderr
        self._original_stderr_write = sys.stderr.write
        self._original_stderr_flush = sys.stderr.flush
        
        def hooked_stderr_write(text):
            self._capture_text(text, "stderr")
            return self._original_stderr_write(text)
        
        sys.stderr.write = hooked_stderr_write  # type: ignore
        
        # Capture logging
        self._logging_handler = _LoggingHandler(self._collector)
        self._logging_handler.setLevel(logging.DEBUG)
        
        # Add handler to root logger and common loggers
        for logger_name in ["", "root", "urllib3", "httpx", "requests"]:
            log = logging.getLogger(logger_name)
            log.addHandler(self._logging_handler)
            log.setLevel(logging.DEBUG)
        
        # Hook into sys.excepthook to catch unhandled exceptions
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._hooked_excepthook
    
    def uninstall(self):
        """Remove console hooks."""
        if self._original_write:
            sys.stdout.write = self._original_write  # type: ignore
        if hasattr(self, "_original_stderr_write"):
            sys.stderr.write = self._original_stderr_write  # type: ignore
        
        if hasattr(self, "_logging_handler"):
            for logger_name in ["", "root", "urllib3", "httpx", "requests"]:
                log = logging.getLogger(logger_name)
                if self._logging_handler in log.handlers:
                    log.removeHandler(self._logging_handler)
        
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
    
    def _capture_text(self, text: str, stream: str):
        """Capture text written to stdout/stderr."""
        if not text or text in ("\n", "\r\n"):
            return
        
        entry = {
            "type": "console",
            "runtime": "python",
            "level": "log" if stream == "stdout" else "error",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "messages": [text.rstrip()],
            "source": f"python:{stream}",
            "context": {},
        }
        self._collector.add_console(entry)
    
    def _hooked_excepthook(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        import traceback
        
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        entry = {
            "type": "console",
            "runtime": "python",
            "level": "error",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "messages": [str(exc_value)],
            "stack": tb_str,
            "source": "python:exception",
            "context": {},
        }
        self._collector.add_console(entry)
        
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)


class _LoggingHandler(logging.Handler):
    """Custom logging handler that forwards records to the collector."""
    
    def __init__(self, collector: Collector):
        super().__init__()
        self._collector = collector
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the collector."""
        entry = {
            "type": "console",
            "runtime": "python",
            "level": record.levelname.lower(),
            "timestamp": int(record.created * 1000),
            "messages": [record.getMessage()],
            "source": f"python:logging:{record.name}",
            "context": {
                "logger": record.name,
                "level": record.levelname,
            },
        }
        
        if record.exc_info:
            entry["stack"] = self.formatException(record.exc_info)
        
        self._collector.add_console(entry)
    
    def formatException(self, exc_info) -> str:
        """Format exception info into a string."""
        import traceback
        return "".join(traceback.format_exception(*exc_info))