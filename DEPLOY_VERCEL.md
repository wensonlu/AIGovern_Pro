# 🚀 Vercel 部署指南

> 将 AIGovern Pro 部署到 Vercel 平台

## 📋 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      Vercel 平台                         │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │   前端 (Frontend)    │  │    后端 (Backend)        │  │
│  │   React + Vite      │  │   FastAPI (Serverless)   │  │
│  │   Static Site       │  │   Python Functions       │  │
│  └─────────────────────┘  └─────────────────────────┘  │
│            ↓                          ↓                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │         外部数据库 (Supabase PostgreSQL)         │   │
│  │    - 业务数据存储                                 │   │
│  │    - 向量检索 (pgvector)                         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 前置要求

1. **Vercel 账号**：[注册](https://vercel.com/signup)
2. **GitHub 账号**：代码托管
3. **Supabase 账号**：[注册](https://supabase.com/)（用于 PostgreSQL 数据库）
4. **大模型 API Key**：豆包/通义千问/OpenAI

---

## 📁 步骤 1：项目配置

### 1.1 创建 Vercel 配置文件

在项目根目录创建 `vercel.json`：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    },
    {
      "src": "backend/api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/api/index.py"
    },
    {
      "src": "/docs",
      "dest": "backend/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/dist/$1"
    }
  ],
  "env": {
    "PYTHONPATH": "backend"
  }
}
```

### 1.2 创建后端入口文件

创建 `backend/api/index.py`（Vercel Serverless 入口）：

```python
"""
Vercel Serverless Function 入口
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from mangum import Mangum

# 适配 Vercel Serverless
handler = Mangum(app, lifespan="off")
```

### 1.3 修改后端主文件

修改 `backend/app/main.py`，添加 CORS 和路径适配：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await init_db()
    yield
    # 关闭时执行

app = FastAPI(
    title="AIGovern Pro API",
    description="AI-Native Enterprise Management System",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-url.vercel.app",  # 替换为实际前端地址
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... 其余路由注册代码
```

### 1.4 修改数据库配置

修改 `backend/app/core/config.py`，适配 Supabase：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置（Supabase）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/aigovern"
    )
    
    # LLM 配置
    DOUBAO_API_KEY: str = os.getenv("DOUBAO_API_KEY", "")
    DOUBAO_MODEL: str = os.getenv("DOUBAO_MODEL", "doubao-pro-32k")
    
    # 其他配置...
    
    class Config:
        env_file = ".env"

settings = Settings()
```

修改 `backend/app/core/database.py`：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import ssl

# Vercel 环境下使用 SSL
def get_engine():
    connect_args = {}
    
    # 如果是 Supabase 或其他远程数据库，启用 SSL
    if "supabase" in settings.DATABASE_URL:
        connect_args["sslmode"] = "require"
    
    return create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,  # 自动检测连接有效性
        pool_recycle=300,    # 5分钟回收连接
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

---

## 📁 步骤 2：前端配置

### 2.1 修改 API 基础地址

修改 `frontend/src/utils/api.ts`（或创建配置文件）：

```typescript
// API 配置
const isDevelopment = import.meta.env.DEV;

export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : '/api';  // Vercel 部署后使用相对路径

// 或者使用环境变量
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
```

### 2.2 创建前端环境变量文件

创建 `frontend/.env.production`：

```env
VITE_API_URL=/api
VITE_APP_TITLE=AIGovern Pro
```

### 2.3 修改 vite 配置

修改 `frontend/vite.config.ts`：

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  base: '/',  // Vercel 部署使用根路径
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 📁 步骤 3：数据库准备（Supabase）

### 3.1 创建 Supabase 项目

1. 登录 [Supabase](https://supabase.com/)
2. 创建新项目
3. 记录数据库连接信息：
   - Host: `db.xxxxxx.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - User: `postgres`

### 3.2 启用 pgvector 扩展

在 Supabase SQL Editor 中执行：

```sql
-- 启用向量扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证安装
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 3.3 初始化表结构

执行数据库初始化脚本：

```sql
-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    filename VARCHAR(255),
    category VARCHAR(50) DEFAULT 'general',
    embedding_status VARCHAR(50) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档分块表（带向量）
CREATE TABLE IF NOT EXISTS document_chunks_with_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 其他业务表...
-- orders, users, products, operation_logs 等
```

---

## 📁 步骤 4：环境变量配置

### 4.1 本地环境变量

创建 `backend/.env`：

```env
# 数据库（开发环境）
DATABASE_URL=postgresql://postgres:password@localhost:5432/aigovern

# 数据库（Vercel/Supabase 生产环境）
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxxx.supabase.co:5432/postgres

# LLM API
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_MODEL=doubao-pro-32k
DOUBAO_EMBEDDING_MODEL=doubao-text-embedding

# 其他配置
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### 4.2 Vercel 环境变量

在 Vercel Dashboard 中设置：

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxxx.supabase.co:5432/postgres
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_MODEL=doubao-pro-32k
DOUBAO_EMBEDDING_MODEL=doubao-text-embedding
SECRET_KEY=your-secret-key-here
PYTHONPATH=backend
```

---

## 📁 步骤 5：部署步骤

### 5.1 推送代码到 GitHub

```bash
# 确保所有修改已提交
git add .
git commit -m "chore: prepare for Vercel deployment"
git push origin main
```

### 5.2 Vercel 部署

**方式一：通过 Vercel Dashboard**

1. 登录 [Vercel](https://vercel.com/)
2. 点击 "Add New Project"
3. 选择 GitHub 仓库 `AIGovern_Pro`
4. 配置：
   - Framework Preset: `Other`（或自定义）
   - Root Directory: `./`（根目录）
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
5. 添加环境变量（见 4.2）
6. 点击 Deploy

**方式二：通过 Vercel CLI**

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
vercel

# 或部署到生产环境
vercel --prod
```

### 5.3 配置后端路由（重要）

部署后，需要确保 API 路由正确：

1. 在 Vercel Dashboard 进入项目
2. 进入 Settings → Functions
3. 确认 Function Region 选择离数据库近的区域（如 Supabase 在 us-east-1，Function 也选 us-east-1）

---

## 📁 步骤 6：验证部署

### 6.1 检查前端

访问 Vercel 提供的前端 URL：
```
https://your-project-name.vercel.app
```

### 6.2 检查后端 API

```bash
# 检查健康接口
curl https://your-project-name.vercel.app/api/health

# 检查 API 文档
curl https://your-project-name.vercel.app/docs
```

### 6.3 检查数据库连接

```bash
# 测试数据查询接口
curl https://your-project-name.vercel.app/api/diagnosis/metrics
```

---

## 🔧 常见问题

### Q1: 后端 API 返回 404？

**原因：** 路由配置不正确

**解决：**
1. 检查 `vercel.json` routes 配置
2. 确保 `backend/api/index.py` 存在
3. 重新部署

### Q2: 数据库连接超时？

**原因：** Vercel Serverless Function 冷启动时间长

**解决：**
1. 确保使用连接池：`pool_pre_ping=True`
2. 检查数据库防火墙允许 Vercel IP
3. 使用 Supabase 的连接池（PGBouncer）

### Q3: 前端无法访问后端？

**原因：** CORS 配置问题

**解决：**
1. 检查 `backend/app/main.py` 中的 CORS 配置
2. 确保 `allow_origins` 包含前端域名
3. 使用相对路径 `/api` 而不是完整 URL

### Q4: 向量检索不工作？

**原因：** pgvector 扩展未启用

**解决：**
1. 在 Supabase SQL Editor 执行：`CREATE EXTENSION vector;`
2. 检查表结构是否正确
3. 重新上传文档进行向量化

### Q5: 文件上传失败？

**原因：** Vercel Serverless 有文件大小限制（4.5MB）

**解决：**
1. 限制上传文件大小
2. 使用云存储（如 Supabase Storage）代替本地存储
3. 修改代码使用流式上传

---

## 📊 性能优化建议

### 1. 数据库连接优化

```python
# 使用连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)
```

### 2. 响应优化

```python
# 使用异步路由
@app.get("/api/data")
async def get_data():
    async with SessionLocal() as session:
        result = await session.execute(query)
        return result.scalars().all()
```

### 3. 缓存优化

```python
# 添加简单缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(key):
    return expensive_query(key)
```

---

## 🔐 安全建议

1. **环境变量：** 不要在代码中硬编码密钥，使用 Vercel 环境变量
2. **CORS：** 只允许特定域名访问 API
3. **API 限制：** 添加 Rate Limiting
4. **数据库：** 使用最小权限原则的数据库用户
5. **HTTPS：** Vercel 默认启用 HTTPS，确保前端使用 https 访问 API

---

## 📝 部署检查清单

- [ ] 代码已推送到 GitHub
- [ ] Supabase 数据库已创建并启用 pgvector
- [ ] 数据库表结构已初始化
- [ ] `vercel.json` 配置正确
- [ ] 后端入口文件 `backend/api/index.py` 已创建
- [ ] CORS 配置包含生产域名
- [ ] 环境变量已在 Vercel Dashboard 设置
- [ ] 前端 API 地址配置正确
- [ ] 部署成功并能访问首页
- [ ] API 接口测试正常
- [ ] 数据库连接正常
- [ ] 文件上传功能正常（如有）

---

## 🎉 完成

部署成功后，你将获得：

- **前端地址**：`https://your-project.vercel.app`
- **API 地址**：`https://your-project.vercel.app/api`
- **API 文档**：`https://your-project.vercel.app/docs`

现在可以开始使用 AIGovern Pro 了！

---

**最后更新：2026-03-16**
