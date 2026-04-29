"""
AI Debug SDK - Python runtime monitoring for console and network.
Following SPEC.md Section 4.6

Usage:
    import ai_debug_sdk  # Enables global monitoring on import

    # Or manually control
    ai_debug_sdk.disable()
    # ... your code ...
    ai_debug_sdk.enable()
"""

from .collector import Collector
from .console_hook import ConsoleHook
from .network_hook import NetworkHook

__version__ = "0.1.0"

_collector = Collector()
_console_hook = ConsoleHook(_collector)
_network_hook = NetworkHook(_collector)

# Auto-enable on import
_network_hook.install()
_console_hook.install()


def enable():
    """Enable global console and network monitoring."""
    _console_hook.install()
    _network_hook.install()


def disable():
    """Disable global monitoring."""
    _console_hook.uninstall()
    _network_hook.uninstall()


def get_console_entries(since: int | None = None) -> list[dict]:
    """Get console log entries, optionally filtered by timestamp.
    
    Args:
        since: Unix timestamp in milliseconds. If provided, only returns
               entries newer than this timestamp.
    
    Returns:
        List of console entry dictionaries.
    """
    return _collector.get_console(since=since)


def get_network_entries(since: int | None = None) -> list[dict]:
    """Get network request entries, optionally filtered by timestamp.
    
    Args:
        since: Unix timestamp in milliseconds. If provided, only returns
               entries newer than this timestamp.
    
    Returns:
        List of network entry dictionaries.
    """
    return _collector.get_network(since=since)


def clear():
    """Clear all collected console and network entries."""
    _collector.clear()


def start_server(port: int = 9310):
    """Start the HTTP API server for MCP server integration.
    
    Args:
        port: Port number to listen on (default: 9310).
    """
    _collector.start(port=port)


def stop_server():
    """Stop the HTTP API server."""
    _collector.stop()