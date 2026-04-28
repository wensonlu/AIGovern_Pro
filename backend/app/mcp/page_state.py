"""Session-based page state manager for MCP browser automation"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import uuid
import asyncio


@dataclass
class PageState:
    """Page state snapshot"""
    session_id: str
    current_url: str = "http://localhost:3001/ai-demo"
    dom_snapshot: str = ""
    form_data: Dict[str, Any] = field(default_factory=dict)
    page_title: str = ""
    visible_text: str = ""
    last_screenshot: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding base64 screenshot"""
        data = asdict(self)
        data.pop("last_screenshot", None)
        data["created_at"] = self.created_at.isoformat()
        data["last_updated"] = self.last_updated.isoformat()
        return data


class PageStateManager:
    """Manage page state for browser automation sessions"""

    def __init__(self, session_timeout_minutes: int = 30):
        self._sessions: Dict[str, PageState] = {}
        self._session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_task = None

    async def initialize(self) -> None:
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def shutdown(self) -> None:
        """Cancel cleanup task on shutdown"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def create_session(self, session_id: Optional[str] = None) -> PageState:
        """Create new session"""
        sid = session_id or str(uuid.uuid4())
        state = PageState(session_id=sid)
        self._sessions[sid] = state
        return state

    def get_session(self, session_id: str) -> Optional[PageState]:
        """Get session by ID, return None if not found or expired"""
        if session_id not in self._sessions:
            return None

        state = self._sessions[session_id]
        # Check if session expired
        if datetime.now() - state.last_updated > self._session_timeout:
            del self._sessions[session_id]
            return None

        return state

    def update_state(
        self,
        session_id: str,
        current_url: str = None,
        dom_snapshot: str = None,
        form_data: Dict[str, Any] = None,
        page_title: str = None,
        visible_text: str = None,
        last_screenshot: Optional[str] = None,
    ) -> PageState:
        """Update session state"""
        state = self.get_session(session_id)
        if not state:
            state = self.create_session(session_id)

        if current_url is not None:
            state.current_url = current_url
        if dom_snapshot is not None:
            state.dom_snapshot = dom_snapshot
        if form_data is not None:
            state.form_data = form_data
        if page_title is not None:
            state.page_title = page_title
        if visible_text is not None:
            state.visible_text = visible_text
        if last_screenshot is not None:
            state.last_screenshot = last_screenshot

        state.last_updated = datetime.now()
        return state

    def clear_session(self, session_id: str) -> None:
        """Remove session"""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_session_state_dict(self, session_id: str) -> Optional[dict]:
        """Get session state as dict (without screenshot)"""
        state = self.get_session(session_id)
        return state.to_dict() if state else None

    async def _cleanup_expired_sessions(self) -> None:
        """Periodically clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                now = datetime.now()
                expired_sessions = [
                    sid for sid, state in self._sessions.items()
                    if now - state.last_updated > self._session_timeout
                ]
                for sid in expired_sessions:
                    del self._sessions[sid]
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Ignore errors in cleanup task


# Global state manager instance
page_state_manager = PageStateManager()
