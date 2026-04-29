"""
Data collector and HTTP API server for Python SDK.
Following SPEC.md Section 4.6

Provides HTTP endpoints for MCP server to query collected data.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from datetime import datetime


class Collector:
    """Shared data collector for console and network entries."""
    
    def __init__(self, port: int = 9310):
        self._port = port
        self._console: list[dict] = []
        self._network: list[dict] = []
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
    
    def add_console(self, entry: dict):
        """Add a console entry."""
        self._console.append(entry)
    
    def add_network(self, entry: dict):
        """Add a network entry."""
        self._network.append(entry)
    
    def get_console(self, since: Optional[int] = None) -> list[dict]:
        """Get console entries, optionally filtered by timestamp."""
        if since is None:
            return list(self._console)
        return [e for e in self._console if e.get("timestamp", 0) > since]
    
    def get_network(self, since: Optional[int] = None) -> list[dict]:
        """Get network entries, optionally filtered by timestamp."""
        if since is None:
            return list(self._network)
        return [e for e in self._network if e.get("timestamp", 0) > since]
    
    def clear(self):
        """Clear all collected entries."""
        self._console.clear()
        self._network.clear()
    
    def start(self, port: Optional[int] = None):
        """Start the HTTP API server."""
        if port is not None:
            self._port = port
        
        if self._server is not None:
            return  # Already running
        
        handler = _create_handler(self)
        self._server = HTTPServer(("127.0.0.1", self._port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the HTTP API server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None


def _create_handler(collector: Collector):
    """Create HTTP request handler bound to collector instance."""
    
    class _RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            """Handle GET requests."""
            parsed = None
            try:
                parsed = urllib.parse.urlparse(self.path)
            except Exception:
                self._send_error(400, "Invalid URL")
                return
            
            path = parsed.path
            query = urllib.parse.parse_qs(parsed.query)
            since = int(query["since"][0]) if "since" in query else None
            
            if path == "/console":
                entries = collector.get_console(since=since)
                self._send_json(entries)
            elif path == "/network":
                entries = collector.get_network(since=since)
                self._send_json(entries)
            elif path == "/health":
                self._send_json({"status": "ok", "timestamp": int(datetime.now().timestamp() * 1000)})
            else:
                self._send_error(404, f"Unknown endpoint: {path}")
        
        def _send_json(self, data):
            """Send JSON response."""
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        
        def _send_error(self, code: int, message: str):
            """Send error response."""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": message}).encode("utf-8"))
        
        def log_message(self, format, *args):
            """Suppress default logging."""
            pass
    
    return _RequestHandler


# Import needed for URL parsing
import urllib.parse