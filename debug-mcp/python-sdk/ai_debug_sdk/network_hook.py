"""
Network hook for Python - captures httpx and requests calls.
Following SPEC.md Section 4.6
"""

import time
import urllib.parse
from datetime import datetime
from typing import Optional, Any
from .collector import Collector

# We'll do runtime imports to avoid hard dependencies
_httpx_installed = False
_requests_installed = False

try:
    import httpx
    _httpx_installed = True
except ImportError:
    pass

try:
    import requests
    _requests_installed = True
except ImportError:
    pass


class NetworkHook:
    """Hook into Python HTTP libraries to capture network requests."""
    
    def __init__(self, collector: Collector):
        self._collector = collector
        self._original_httpx_request = None
        self._original_requests_request = None
        self._enabled = False
    
    def install(self):
        """Install network hooks for httpx and requests."""
        if _requests_installed:
            self._install_requests_hook()
        if _httpx_installed:
            self._install_httpx_hook()
        self._enabled = True
    
    def uninstall(self):
        """Remove network hooks."""
        if _requests_installed and self._original_requests_request:
            requests.api.request = self._original_requests_request  # type: ignore
        if _httpx_installed and self._original_httpx_request:
            httpx.Client.request = self._original_httpx_request  # type: ignore
        self._enabled = False
    
    def _install_requests_hook(self):
        """Hook into requests library."""
        original_request = requests.api.request
        
        def hooked_request(method, url, **kwargs):
            start_time = time.time()
            headers = kwargs.get("headers", {})
            body = kwargs.get("data") or kwargs.get("json")
            
            try:
                response = original_request(method, url, **kwargs)
            except Exception as e:
                self._record_error(url, method, 0, str(e), headers, body)
                raise
            
            response_time = int((time.time() - start_time) * 1000)
            self._record_response(response, method, response_time, headers, body)
            return response
        
        self._original_requests_request = original_request
        requests.api.request = hooked_request  # type: ignore
        
        # Also hook Session.request
        if hasattr(requests, "Session"):
            original_session_request = requests.Session.request
            def hooked_session_request(self, method, url, **kwargs):
                start_time = time.time()
                headers = kwargs.get("headers", {})
                body = kwargs.get("data") or kwargs.get("json")
                
                try:
                    response = original_session_request(self, method, url, **kwargs)
                except Exception as e:
                    self._record_error(url, method, 0, str(e), headers, body)
                    raise
                
                response_time = int((time.time() - start_time) * 1000)
                self._record_response(response, method, response_time, headers, body)
                return response
            
            requests.Session.request = hooked_session_request  # type: ignore
    
    def _install_httpx_hook(self):
        """Hook into httpx library."""
        original_request = httpx.Client.request
        
        async def hooked_request_async(self, method, url, **kwargs):
            start_time = time.time()
            headers = kwargs.get("headers", {})
            content = kwargs.get("content")
            
            try:
                response = await original_request(self, method, url, **kwargs)
            except Exception as e:
                self._record_error(str(url), method, 0, str(e), headers, content)
                raise
            
            response_time = int((time.time() - start_time) * 1000)
            self._record_httpx_response(response, method, response_time, headers, content)
            return response
        
        self._original_httpx_request = original_request
        httpx.Client.request = hooked_request_async  # type: ignore
    
    def _record_response(self, response, method: str, response_time: int, request_headers: dict, request_body: Any):
        """Record a requests response."""
        try:
            parsed_url = urllib.parse.urlparse(response.url)
            entry = {
                "type": "network",
                "runtime": "python",
                "id": response.url,
                "method": method.upper(),
                "url": response.url,
                "path": parsed_url.path,
                "domain": parsed_url.netloc,
                "status": response.status_code,
                "statusText": response.reason or "",
                "responseTime": response_time,
                "requestHeaders": dict(request_headers),
                "requestBody": request_body,
                "responseHeaders": dict(response.headers),
                "responseBody": self._try_get_json(response),
                "validated": False,
                "validationResult": {"符合预期": False},
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            self._collector.add_network(entry)
        except Exception:
            pass  # Don't let recording failures break the request
    
    def _record_httpx_response(self, response, method: str, response_time: int, request_headers: dict, request_body: Any):
        """Record an httpx response."""
        try:
            url_str = str(response.url)
            parsed_url = urllib.parse.urlparse(url_str)
            entry = {
                "type": "network",
                "runtime": "python",
                "id": url_str,
                "method": method.upper(),
                "url": url_str,
                "path": parsed_url.path,
                "domain": parsed_url.netloc,
                "status": response.status_code,
                "statusText": response.reason_phrase or "",
                "responseTime": response_time,
                "requestHeaders": dict(request_headers) if request_headers else {},
                "requestBody": request_body,
                "responseHeaders": dict(response.headers),
                "responseBody": self._try_get_json(response),
                "validated": False,
                "validationResult": {"符合预期": False},
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            self._collector.add_network(entry)
        except Exception:
            pass
    
    def _record_error(self, url: str, method: str, status: int, message: str, request_headers: dict, request_body: Any):
        """Record a failed network request."""
        try:
            parsed_url = urllib.parse.urlparse(url)
            entry = {
                "type": "network",
                "runtime": "python",
                "id": url,
                "method": method.upper(),
                "url": url,
                "path": parsed_url.path,
                "domain": parsed_url.netloc,
                "status": 0,
                "statusText": message,
                "responseTime": 0,
                "requestHeaders": dict(request_headers) if request_headers else {},
                "requestBody": request_body,
                "responseHeaders": {},
                "responseBody": None,
                "validated": False,
                "validationResult": {"符合预期": False},
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            self._collector.add_network(entry)
        except Exception:
            pass
    
    def _try_get_json(self, response) -> Optional[Any]:
        """Try to get JSON body from response."""
        try:
            return response.json()
        except Exception:
            try:
                return response.text
            except Exception:
                return None