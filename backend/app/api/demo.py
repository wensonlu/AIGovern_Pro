"""Demo API routes for MCP browser automation"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.llm import llm_client
from app.services.mcp_service import mcp_service

router = APIRouter(prefix="/api/demo", tags=["demo"])


class AITaskRequest(BaseModel):
    """Request for AI-powered task"""
    task: str
    session_id: str = None


class AITaskResponse(BaseModel):
    """Response for AI task"""
    status: str
    session_id: str


@router.post("/ai-task")
async def execute_ai_task(
    request: AITaskRequest,
    db: Session = Depends(get_db),
):
    """
    Execute an AI task that controls the browser.
    Returns NDJSON stream with events: task/tool_call/tool_result/screenshot/response/done/error
    """

    if not request.task or len(request.task) > 500:
        raise HTTPException(status_code=400, detail="Task must be 1-500 characters")

    session_id = request.session_id or f"session_{id(request)}"

    async def event_stream():
        try:
            async for event in mcp_service.stream_ai_task(
                session_id=session_id,
                task=request.task,
                llm_client=llm_client,
                db=db,
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "message": f"Task execution failed: {str(e)}",
                "error": str(e),
            }
            yield json.dumps(error_event, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/screenshot/{session_id}")
async def get_screenshot(session_id: str):
    """
    Get current screenshot for a session.
    Returns: {"image": "data:image/png;base64,..."}
    """
    from app.mcp.page_state import page_state_manager
    from app.mcp.browser_engine import browser_engine

    state = page_state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await browser_engine.screenshot(session_id)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)

    return result.data


@router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset a session (clear page state and browser context)
    """
    from app.mcp.page_state import page_state_manager
    from app.mcp.browser_engine import browser_engine

    await browser_engine.close_session(session_id)
    page_state_manager.clear_session(session_id)

    return {"status": "ok", "message": f"Session {session_id} reset"}


@router.get("/health")
async def health_check():
    """Health check for demo API"""
    return {"status": "ok", "service": "mcp-demo"}
