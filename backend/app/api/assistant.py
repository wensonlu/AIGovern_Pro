from __future__ import annotations

import re
import time
import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import (
    AssistantApproval,
    AssistantAuditEvent,
    AssistantMessage,
    AssistantSession,
    AssistantToolCall,
    OperationLog,
)
from app.models.schemas import (
    AssistantApprovalRequest,
    AssistantApprovalResponse,
    AssistantSessionCreateRequest,
    AssistantSessionResponse,
    AssistantTimelineItem,
    AssistantTimelineResponse,
    AssistantToolRequest,
    AssistantToolResponse,
)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

READ_ONLY_BLOCKLIST = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke)\b", re.IGNORECASE)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _create_audit_event(db: Session, tenant_id: str, session_id: str, event_type: str, payload: dict[str, Any]) -> None:
    evt = AssistantAuditEvent(
        id=_new_id("evt"),
        tenant_id=tenant_id,
        session_id=session_id,
        event_type=event_type,
        payload_json=payload,
    )
    db.add(evt)


def _summarize(data: Any) -> str:
    if data is None:
        return "no output"
    text_summary = str(data)
    return text_summary if len(text_summary) <= 180 else f"{text_summary[:177]}..."


def _json_safe(value: Any) -> Any:
    """Convert Python objects to JSON-serializable values."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _validate_read_sql(query: str, limit: int) -> None:
    lowered = query.lower().strip()
    if not lowered.startswith("select"):
        raise HTTPException(status_code=400, detail="SQL_READONLY_VIOLATION: only SELECT is allowed")
    if ";" in lowered:
        raise HTTPException(status_code=400, detail="SQL_READONLY_VIOLATION: multi-statement is not allowed")
    if READ_ONLY_BLOCKLIST.search(lowered):
        raise HTTPException(status_code=400, detail="SQL_READONLY_VIOLATION: write keywords are not allowed")
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR: limit must be 1..200")


@router.post("/sessions", response_model=AssistantSessionResponse)
async def create_session(request: AssistantSessionCreateRequest, db: Session = Depends(get_db)) -> AssistantSessionResponse:
    session_id = _new_id("sess")
    now = datetime.utcnow()
    session_row = AssistantSession(
        id=session_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        started_at=now,
    )
    db.add(session_row)
    _create_audit_event(
        db,
        tenant_id=request.tenant_id,
        session_id=session_id,
        event_type="session_created",
        payload={"user_id": request.user_id},
    )
    db.commit()
    return AssistantSessionResponse(
        session_id=session_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        started_at=now,
    )


@router.post("/tools/call", response_model=AssistantToolResponse)
async def call_tool(request: AssistantToolRequest, db: Session = Depends(get_db)) -> AssistantToolResponse:
    session_row = db.query(AssistantSession).filter(AssistantSession.id == request.session_id).first()
    if not session_row:
        raise HTTPException(status_code=404, detail="NOT_FOUND: session not found")
    if session_row.tenant_id != request.tenant_id or session_row.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN: tenant_id/user_id mismatch")

    tool_call_id = _new_id("tool")
    start = time.time()
    tool_call = AssistantToolCall(
        id=tool_call_id,
        session_id=request.session_id,
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        tool_name=request.tool_name,
        input_json=request.arguments,
        status="draft",
    )
    db.add(tool_call)
    db.add(
        AssistantMessage(
            session_id=request.session_id,
            role="user",
            content=f"tool_request:{request.tool_name}",
        )
    )
    _create_audit_event(
        db,
        tenant_id=request.tenant_id,
        session_id=request.session_id,
        event_type="tool_requested",
        payload={"tool_call_id": tool_call_id, "tool_name": request.tool_name, "arguments": request.arguments},
    )
    db.flush()

    try:
        if request.tool_name == "read_sql":
            query = str(request.arguments.get("query", "")).strip()
            limit = int(request.arguments.get("limit", 200))
            _validate_read_sql(query, limit)
            final_sql = f"{query} LIMIT {limit}" if " limit " not in query.lower() else query

            tool_call.status = "executing"
            rows = db.execute(text(final_sql)).mappings().all()
            result_rows = [dict(r) for r in rows]
            output = {
                "columns": list(result_rows[0].keys()) if result_rows else [],
                "rows": result_rows,
                "row_count": len(result_rows),
                "truncated": len(result_rows) >= limit,
            }
            tool_call.output_json = _json_safe(output)
            tool_call.status = "succeeded"

        elif request.tool_name == "generate_chart_data":
            source_tool_call_id = str(request.arguments.get("source_tool_call_id", "")).strip()
            chart_type = str(request.arguments.get("chart_type", "bar"))
            x_field = str(request.arguments.get("x_field", "")).strip()
            y_field = str(request.arguments.get("y_field", "")).strip()
            if not source_tool_call_id or not x_field or not y_field:
                raise HTTPException(status_code=400, detail="VALIDATION_ERROR: source_tool_call_id/x_field/y_field are required")

            source = (
                db.query(AssistantToolCall)
                .filter(
                    AssistantToolCall.id == source_tool_call_id,
                    AssistantToolCall.session_id == request.session_id,
                    AssistantToolCall.tool_name == "read_sql",
                    AssistantToolCall.status == "succeeded",
                )
                .first()
            )
            if not source:
                raise HTTPException(status_code=404, detail="NOT_FOUND: source read_sql tool call not found")

            rows = (source.output_json or {}).get("rows", [])
            x_values = [r.get(x_field) for r in rows]
            y_values = [r.get(y_field) for r in rows]
            output = {
                "chartType": chart_type,
                "x": x_values,
                "y": y_values,
                "series": [{"name": y_field, "data": y_values}],
            }
            tool_call.status = "executing"
            tool_call.output_json = _json_safe(output)
            tool_call.status = "succeeded"

        else:
            title = str(request.arguments.get("title", "")).strip()
            assignee = str(request.arguments.get("assignee", "")).strip()
            due_date = str(request.arguments.get("due_date", "")).strip()
            priority = str(request.arguments.get("priority", "medium")).strip()
            context = str(request.arguments.get("context", "")).strip()
            if not title or not assignee or not due_date or not context:
                raise HTTPException(status_code=400, detail="VALIDATION_ERROR: title/assignee/due_date/context are required")

            tool_call.status = "pending_approval"
            approval = AssistantApproval(
                id=_new_id("appr"),
                tool_call_id=tool_call_id,
                risk_level="medium",
                status="pending",
            )
            db.add(approval)
            _create_audit_event(
                db,
                tenant_id=request.tenant_id,
                session_id=request.session_id,
                event_type="approval_requested",
                payload={"tool_call_id": tool_call_id},
            )

            elapsed = int((time.time() - start) * 1000)
            tool_call.latency_ms = elapsed
            db.commit()
            return AssistantToolResponse(
                ok=False,
                tool_call_id=tool_call_id,
                status="pending_approval",
                data=None,
                error_code="APPROVAL_REQUIRED",
                error_message="create_followup_task requires explicit user approval",
                duration_ms=elapsed,
            )

        elapsed = int((time.time() - start) * 1000)
        tool_call.latency_ms = elapsed
        _create_audit_event(
            db,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            event_type="tool_succeeded",
            payload={"tool_call_id": tool_call_id, "tool_name": request.tool_name},
        )
        db.commit()

        return AssistantToolResponse(
            ok=True,
            tool_call_id=tool_call_id,
            status=tool_call.status,
            data=tool_call.output_json,
            error_code=None,
            error_message=None,
            duration_ms=elapsed,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        elapsed = int((time.time() - start) * 1000)
        failed_call = db.query(AssistantToolCall).filter(AssistantToolCall.id == tool_call_id).first()
        if failed_call:
            failed_call.status = "failed"
            failed_call.error_code = "INTERNAL_ERROR"
            failed_call.error_message = str(exc)
            failed_call.latency_ms = elapsed
        _create_audit_event(
            db,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            event_type="tool_failed",
            payload={"tool_call_id": tool_call_id, "error": str(exc)},
        )
        db.commit()
        return AssistantToolResponse(
            ok=False,
            tool_call_id=tool_call_id,
            status="failed",
            data=None,
            error_code="INTERNAL_ERROR",
            error_message=str(exc),
            duration_ms=elapsed,
        )


@router.post("/approvals/{tool_call_id}/approve", response_model=AssistantApprovalResponse)
async def approve_tool_call(
    tool_call_id: str,
    request: AssistantApprovalRequest,
    db: Session = Depends(get_db),
) -> AssistantApprovalResponse:
    tool_call = db.query(AssistantToolCall).filter(AssistantToolCall.id == tool_call_id).first()
    if not tool_call:
        raise HTTPException(status_code=404, detail="NOT_FOUND: tool call not found")

    approval = db.query(AssistantApproval).filter(AssistantApproval.tool_call_id == tool_call_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="NOT_FOUND: approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR: approval already processed")

    start = time.time()
    approval.status = "approved"
    approval.approved_by = request.approved_by
    approval.approved_at = datetime.utcnow()

    tool_call.status = "approved"
    tool_call.status = "executing"

    args = tool_call.input_json or {}
    op_log = OperationLog(
        user_id=1,
        operation_type="create_followup_task",
        operation_target="task",
        operation_detail={
            "title": args.get("title"),
            "assignee": args.get("assignee"),
            "due_date": args.get("due_date"),
            "priority": args.get("priority", "medium"),
            "context": args.get("context"),
        },
        status="completed",
    )
    db.add(op_log)
    db.flush()

    result = {"task_id": f"task_{op_log.id}", "status": "created"}
    tool_call.output_json = result
    tool_call.status = "succeeded"
    tool_call.latency_ms = int((time.time() - start) * 1000)

    _create_audit_event(
        db,
        tenant_id=tool_call.tenant_id,
        session_id=tool_call.session_id,
        event_type="approval_approved",
        payload={"tool_call_id": tool_call_id, "approved_by": request.approved_by},
    )
    _create_audit_event(
        db,
        tenant_id=tool_call.tenant_id,
        session_id=tool_call.session_id,
        event_type="tool_succeeded",
        payload={"tool_call_id": tool_call_id, "tool_name": "create_followup_task"},
    )
    db.commit()

    return AssistantApprovalResponse(
        tool_call_id=tool_call_id,
        status="approved",
        approved_by=approval.approved_by,
        approved_at=approval.approved_at,
    )


@router.post("/approvals/{tool_call_id}/reject", response_model=AssistantApprovalResponse)
async def reject_tool_call(
    tool_call_id: str,
    request: AssistantApprovalRequest,
    db: Session = Depends(get_db),
) -> AssistantApprovalResponse:
    tool_call = db.query(AssistantToolCall).filter(AssistantToolCall.id == tool_call_id).first()
    if not tool_call:
        raise HTTPException(status_code=404, detail="NOT_FOUND: tool call not found")

    approval = db.query(AssistantApproval).filter(AssistantApproval.tool_call_id == tool_call_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="NOT_FOUND: approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR: approval already processed")

    approval.status = "rejected"
    approval.approved_by = request.approved_by
    approval.approved_at = datetime.utcnow()
    tool_call.status = "rejected"

    _create_audit_event(
        db,
        tenant_id=tool_call.tenant_id,
        session_id=tool_call.session_id,
        event_type="approval_rejected",
        payload={"tool_call_id": tool_call_id, "approved_by": request.approved_by},
    )
    db.commit()

    return AssistantApprovalResponse(
        tool_call_id=tool_call_id,
        status="rejected",
        approved_by=approval.approved_by,
        approved_at=approval.approved_at,
    )


@router.get("/sessions/{session_id}/timeline", response_model=AssistantTimelineResponse)
async def get_timeline(session_id: str, db: Session = Depends(get_db)) -> AssistantTimelineResponse:
    calls = (
        db.query(AssistantToolCall)
        .filter(AssistantToolCall.session_id == session_id)
        .order_by(AssistantToolCall.created_at.asc())
        .all()
    )

    items = [
        AssistantTimelineItem(
            tool_call_id=call.id,
            tool_name=call.tool_name,
            status=call.status,
            input_summary=_summarize(call.input_json),
            output_summary=_summarize(call.output_json) if call.output_json is not None else None,
            latency_ms=call.latency_ms,
            error_code=call.error_code,
            created_at=call.created_at,
        )
        for call in calls
    ]

    return AssistantTimelineResponse(session_id=session_id, items=items)
