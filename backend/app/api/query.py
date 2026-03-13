from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import QueryRequest, QueryResponse
from typing import Any

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """执行数据查询 - 自然语言 → SQL 生成 → 查询执行"""

    sql = "SELECT * FROM orders LIMIT 10"
    result = []
    chart_type = "table"

    return QueryResponse(
        sql=sql,
        result=result,
        chart_type=chart_type,
        rows_count=len(result),
        execution_time=0.1,
    )


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """获取查询历史"""
    return {
        "total": 0,
        "items": [],
    }


@router.post("/{query_id}/export")
async def export_query_result(
    query_id: int,
    format: str = "csv",
    db: Session = Depends(get_db),
):
    """导出查询结果"""
    return {
        "status": "success",
        "format": format,
        "download_url": "/files/query_result.csv",
    }
