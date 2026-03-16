from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import ChatRequest, ChatResponse
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
