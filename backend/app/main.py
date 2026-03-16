from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api import documents, chat, query, operations, diagnosis

# 创建 FastAPI 应用
app = FastAPI(
    title="AIGovern Pro API",
    description="AI 原生的企业级 B 端管理系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(query.router)
app.include_router(operations.router)
app.include_router(diagnosis.router)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "database": "pgvector",
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AIGovern Pro API",
        "docs": "/docs",
        "version": "0.1.0",
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
