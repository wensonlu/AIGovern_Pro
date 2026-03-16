from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import OperationExecuteRequest, OperationTemplate, OperationLog
from app.services.operation_service import operation_service
from typing import Any, Optional

router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("/templates", response_model=list[OperationTemplate])
async def get_operation_templates(db: Session = Depends(get_db)):
    """获取操作模板列表"""
    return operation_service.get_templates()


@router.post("/execute")
async def execute_operation(
    request: OperationExecuteRequest,
    db: Session = Depends(get_db),
):
    """执行操作"""
    result = await operation_service.execute_operation(
        request.operation_type,
        request.parameters,
    )
    return result


@router.get("/logs")
async def get_operation_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取操作日志列表"""
    logs = operation_service.get_operation_logs(db, limit=limit)
    return {
        "total": len(logs),
        "items": logs,
    }

