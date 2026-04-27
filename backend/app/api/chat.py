import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, StructuredChatResponse
from app.services.agent_service import agent_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    处理用户对话请求
    支持：知识问答(RAG)、数据查询(SQL)、智能操作(Operation)
    """
    response = await agent_service.process_message(
        message=request.question,
        db=db,
        session_id=request.session_id,
    )

    return response


@router.post("/stream")
async def process_chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    流式处理用户对话请求。
    返回 NDJSON：sources/delta/done/error 事件，每行一个 JSON 对象。
    """

    async def event_stream():
        try:
            async for event in agent_service.process_message_stream(
                message=request.question,
                db=db,
                session_id=request.session_id,
                top_k=request.top_k,
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "message": f"对话处理失败：{e}",
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


@router.post("/structured", response_model=StructuredChatResponse)
async def process_chat_structured(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    处理用户对话请求 - 结构化版本
    返回结构化的 sections 而不是原始 markdown
    """
    # 获取 RAG 服务实例
    from app.services.rag_service import rag_service

    response = await rag_service.generate_structured_sections(
        question=request.question,
        top_k=request.top_k,
    )
    # 设置 session_id
    response.session_id = request.session_id or "default"
    return response


@router.post("/structured/stream")
async def process_chat_structured_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    流式处理用户对话请求 - 结构化版本
    返回 NDJSON：sources/section/done/error 事件，每行一个 JSON 对象。
    """

    async def event_stream():
        try:
            async for event in agent_service.process_message_structured_stream(
                message=request.question,
                db=db,
                session_id=request.session_id,
                top_k=request.top_k,
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "message": f"对话处理失败：{e}",
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


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """获取对话历史"""
    return {
        "session_id": session_id,
        "messages": [],
    }


@router.delete("/{session_id}")
async def clear_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """清除对话历史"""
    return {"status": "success", "message": "对话历史已清除"}
