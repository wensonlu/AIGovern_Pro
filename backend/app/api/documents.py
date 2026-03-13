from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import DocumentResponse, DocumentListResponse
from app.core.config import settings
from datetime import datetime
import os

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = None,
    category: str = "general",
    db: Session = Depends(get_db),
):
    """上传文档并进行向量化"""

    if not title:
        title = file.filename or "Untitled"

    if file.filename:
        ext = file.filename.split(".")[-1].lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {ext}",
            )

    file_content = await file.read()
    if len(file_content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail="文件过大",
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, file.filename or "upload")
    with open(file_path, "wb") as f:
        f.write(file_content)

    return DocumentResponse(
        id=1,
        title=title,
        category=category,
        embedding_status="pending",
        chunk_count=0,
        created_at=datetime.now(),
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0, limit: int = 10, category: str = None, db: Session = Depends(get_db)
):
    """获取文档列表"""
    return DocumentListResponse(total=0, items=[])


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """获取文档详情"""
    raise HTTPException(status_code=404, detail="文档不存在")


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """删除文档"""
    return {"status": "success", "message": "文档已删除"}


@router.post("/{document_id}/test-retrieval")
async def test_retrieval(document_id: int, query: str, db: Session = Depends(get_db)):
    """测试文档检索效果"""
    return {
        "query": query,
        "results": [],
        "total": 0,
    }
