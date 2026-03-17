from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.api import documents, chat, query, operations, diagnosis, products

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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://ai-govern-pro.vercel.app",  # Vercel 生产域名
        "https://*.vercel.app",  # 允许所有 Vercel 子域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册 API 路由（必须在静态文件之前注册）
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(query.router)
app.include_router(operations.router)
app.include_router(diagnosis.router)
app.include_router(products.router)


# 健康检查
@app.get("/health")
@app.head("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "database": "pgvector",
    }


# 前端静态文件路径
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "dist")
frontend_index_path = os.path.join(frontend_dist_path, "index.html")

# 如果前端构建文件存在，配置前端路由
if os.path.exists(frontend_dist_path) and os.path.exists(frontend_index_path):
    # 挂载静态文件目录
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    
    # 根路径返回前端首页
    @app.get("/")
    async def root():
        """根路径 - 返回前端首页"""
        return FileResponse(frontend_index_path)
    
    # 支持 HEAD 请求（CloudStudio 健康检查需要）
    @app.head("/")
    async def root_head():
        """根路径 HEAD 检查"""
        return {"status": "ok"}
    
    # 所有其他路径也返回前端首页（支持前端路由）
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        """捕获所有路径，返回前端首页（支持 React Router）"""
        # API 路径不应该走到这里，因为上面已经注册了 API 路由
        # 如果文件存在，返回文件；否则返回 index.html
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(frontend_index_path)
        
else:
    # 开发环境：没有前端构建文件时返回 API 信息
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "AIGovern Pro API",
            "docs": "/docs",
            "version": "0.1.0",
        }
    
    @app.head("/")
    async def root_head():
        """根路径 HEAD 检查"""
        return {"status": "ok"}


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
