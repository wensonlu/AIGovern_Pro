---
date: 2026-03-31 15:30:00 CST
researcher: Claude Code - research-codebase skill
git_commit: a778157ad9a56c5191d9abe6e001cab92b093e86
branch: main
repository: AIGovern_Pro
topic: 完整项目启动指南 - 前后端环境配置与初始化流程
tags: [startup, frontend, backend, configuration, dependencies, database, lvm-integration]
status: complete
last_updated: 2026-03-31
last_updated_by: Claude Code
---

# AIGovern Pro - 完整启动指南

## 摘要

AIGovern Pro 是一个全栈 AI 原生的企业级 B 端管理系统，包含：
- **前端**：React 18 + TypeScript + Vite + Ant Design，运行在 port 3000
- **后端**：FastAPI + Python + SQLAlchemy ORM，运行在 port 8000
- **数据库**：PostgreSQL（生产）或 SQLite（开发），带 pgvector 向量扩展
- **LLM 集成**：支持豆包（Doubao）或通义千问（Qwen）API

项目已完全配置，所有依赖、启动脚本和初始化流程都已就位。本文档描述项目的当前状态和完整的启动步骤。

---

## 项目架构概览

```
┌─────────────────────────────────┐
│   React Frontend                │
│   (port 3000)                   │
│  ┌─────────────────────────────┐│
│  │ Dashboard                   ││
│  │ Documents (RAG)             ││
│  │ DataQuery (SQL生成)         ││
│  │ SmartOps (自动执行)         ││
│  │ Diagnosis (诊断分析)        ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
           ↓ /api/* 代理
┌─────────────────────────────────┐
│   FastAPI Backend (port 8000)   │
│  ┌─────────────────────────────┐│
│  │ • documents API             ││
│  │ • chat API (RAG)            ││
│  │ • query API (SQL)           ││
│  │ • operations API (执行)     ││
│  │ • diagnosis API (分析)      ││
│  │ • products API (CRUD)       ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   PostgreSQL + pgvector         │
│   (PostgreSQL/SQLite)           │
│   • Users, Products, Orders     │
│   • Documents, Embeddings       │
│   • OperationLog, QueryCache    │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   LLM Provider (Optional)       │
│   • Doubao (豆包) API           │
│   • Qwen (通义千问) API         │
└─────────────────────────────────┘
```

---

## 系统依赖检查

### 已安装环境
```
✓ Node: v22.22.0 (/usr/bin/node)
✓ npm: 9.x+ (/usr/bin/npm)
✓ pnpm: installed (/usr/bin/pnpm)
✓ Python 3: /usr/bin/python3
```

### 前端依赖

**生产依赖** (`frontend/package.json`):
| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.3.1 | React 框架 |
| react-router-dom | ^6.20.0 | 路由管理 |
| antd | ^5.11.0 | UI 组件库 |
| recharts | ^2.10.3 | 图表库 |
| axios | ^1.6.2 | HTTP 客户端 |

**开发依赖** (`frontend/package.json`):
| Package | Version | Purpose |
|---------|---------|---------|
| typescript | ^5.2.2 | 类型系统 |
| vite | ^5.0.0 | 构建工具 |
| eslint | ^8.51.0 | Linting |
| prettier | ^3.1.0 | 代码格式化 |
| vitest | ^0.34.6 | 测试框架 |

**NPM 脚本**:
- `npm run dev` - 启动开发服务器（http://localhost:3000）
- `npm run build` - 生产构建（输出到 dist/）
- `npm run lint` - ESLint 检查
- `npm run type-check` - TypeScript 类型检查
- `npm run format` - Prettier 代码格式化
- `npm run test` - 运行单元测试

### 后端依赖

**核心** (`backend/requirements.txt`):
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.110.0 | Web 框架 |
| uvicorn[standard] | >=0.27.0 | ASGI 服务器 |
| sqlalchemy | >=2.0.30 | ORM |
| psycopg2-binary | >=2.9.0 | PostgreSQL 驱动 |
| pgvector | >=0.3.0 | 向量扩展 |
| pydantic | >=2.10.0 | 数据验证 |
| python-dotenv | >=1.0.0 | 环境变量管理 |
| dashscope | (latest) | 通义千问 SDK |
| PyPDF2 | >=3.0.0 | PDF 解析 |
| python-docx | >=1.0.0 | DOCX 解析 |

**测试**:
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.4.4 | 测试框架 |
| pytest-asyncio | >=0.23.0 | 异步测试支持 |

---

## 完整启动步骤

### 步骤 1：克隆和初始化项目

```bash
cd /Users/wclu/AIGovern_Pro

# 验证项目结构
ls -la
# 应该看到: frontend/, backend/, docs/, .env.example, etc.
```

### 步骤 2：配置后端环境变量

```bash
cd /Users/wclu/AIGovern_Pro/backend

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（必须配置项标记 ★）
vim .env
```

**必填项** (`backend/.env`):

```env
# FastAPI 配置
API_VERSION=v1
DEBUG=true                    # 开发模式启用热重载
HOST=0.0.0.0
PORT=8000

# ★ 数据库配置（二选一）
# 选项 A: SQLite（开发推荐，无需额外配置）
DATABASE_URL=sqlite:///./aigovern.db

# 选项 B: PostgreSQL（生产环境）
# DATABASE_URL=postgresql://user:password@localhost:5432/aigovern_db
DB_ECHO=false

# ★ 向量化配置
VECTOR_DIMENSIONS=768
VECTOR_SIMILARITY_METRIC=cosine

# ★ LLM 提供商配置（选择一个）
# 选项 A: 豆包 (Doubao)
LLM_PROVIDER=doubao
LLM_API_KEY=your_doubao_api_key_here
LLM_MODEL_NAME=doubao-pro
LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3

# 选项 B: 通义千问 (Qwen)
# LLM_PROVIDER=qwen
# LLM_API_KEY=your_qwen_api_key_here
# LLM_MODEL_NAME=qwen-plus
# EMBEDDING_MODEL_NAME=text-embedding-v2

# JWT 认证
SECRET_KEY=your-secret-key-here-change-in-production  # ★ 改为安全的值
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件上传
MAX_UPLOAD_SIZE=52428800    # 50MB
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=pdf,docx,txt,md

# 日志
LOG_LEVEL=INFO

# Redis（可选）
# REDIS_URL=redis://localhost:6379/0
```

**关键说明**：
- 开发环境默认使用 SQLite（`aigovern.db`），无需数据库配置
- `LLM_API_KEY` 必须配置才能使用 RAG 和 SQL 生成功能
- 若无 LLM Key，后端仍可运行，但 AI 功能返回 mock 数据

### 步骤 3：创建并激活 Python 虚拟环境

```bash
cd /Users/wclu/AIGovern_Pro/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 验证激活
which python  # 应该显示 .../venv/bin/python
```

### 步骤 4：安装后端依赖

```bash
cd /Users/wclu/AIGovern_Pro/backend

# 确保虚拟环境激活
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

### 步骤 5：初始化数据库

```bash
cd /Users/wclu/AIGovern_Pro/backend
source venv/bin/activate

# 选项 A: 通过启动脚本（推荐）
python run.py
# 此脚本会：
# 1. 创建数据库表（SQLite 或 PostgreSQL）
# 2. 插入示例数据（用户、产品、订单、指标）
# 3. 启动 FastAPI 服务

# 选项 B: 单独初始化数据库
python scripts/init_db.py
# 然后用以下命令启动：
python -m uvicorn app.main:app --reload --port 8000
```

**初始化结果**:
- 创建表：User, Product, Order, Metric, Document, DocumentChunk, OperationLog, QueryCache
- 示例数据：3 个用户、4 个产品、4 个订单、4 个指标
- 数据库文件：`backend/aigovern.db`（SQLite 情况）

### 步骤 6：验证后端运行

```bash
# 在后端完全启动后，另开终端检查健康状态
curl http://localhost:8000/health

# 预期响应：
# {"status":"ok","version":"0.1.0","database":"pgvector"}
```

**API 文档**：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 步骤 7：前端依赖安装

```bash
cd /Users/wclu/AIGovern_Pro/frontend

# 使用 pnpm（推荐）
pnpm install

# 或使用 npm
npm install

# 验证安装
ls node_modules/ | grep -E "react|antd|vite"
```

### 步骤 8：配置前端环境变量

```bash
cd /Users/wclu/AIGovern_Pro/frontend

# 复制环境变量模板
cp .env.example .env.local

# 编辑 .env.local（通常无需改动，默认已配置）
cat .env.local
# 应该包含：
# VITE_API_URL=http://localhost:8000
```

### 步骤 9：启动前端开发服务器

```bash
cd /Users/wclu/AIGovern_Pro/frontend

# 使用 pnpm
pnpm dev

# 或使用 npm
npm run dev

# 输出示例：
# VITE v5.0.0  ready in 234 ms
# ➜  Local:   http://localhost:3000/
# ➜  press h to show help
```

**开发服务器特性**：
- 自动打开浏览器到 http://localhost:3000
- 热模块更新 (HMR) 启用
- `/api/*` 请求自动代理到 http://localhost:8000

### 步骤 10：访问应用

打开浏览器访问：**http://localhost:3000**

**可用页面**（侧边栏菜单）：
| 页面 | 路由 | 功能 |
|------|------|------|
| 仪表板 | `/` 或 `/dashboard` | KPI 展示、图表、预警 |
| 知识库 | `/documents` | 文档上传、向量化进度、检索 |
| 数据查询 | `/query` | 自然语言查询、SQL 预览、图表 |
| 智能操作 | `/operations` | 操作模板、执行日志、回滚 |
| 经营诊断 | `/diagnosis` | 指标分析、根因分析 |

---

## 后端启动过程详解

### 启动序列（`backend/run.py`）

**阶段 1: 环境加载**
- 加载 `backend/.env` 文件到 `os.environ`
- 读取配置到 `settings` 对象（`app.core.config.Settings`）

**阶段 2: 数据库连接**
- 创建 SQLAlchemy 引擎（SQLite or PostgreSQL）
- 连接字符串来自 `DATABASE_URL` 环境变量

**阶段 3: 数据库初始化**
```python
Base.metadata.create_all(bind=engine)
```
- 检查所有 ORM 模型（导入自 `app.models.db_models`）
- 生成 CREATE TABLE SQL
- 执行 DDL 创建缺失的表

**阶段 4: 示例数据注入**
```python
seed_data()  # 调用 run.py:17-64
```
- 检查 User 表是否已有数据
- 若为空，插入：
  - 3 个用户（admin/manager/user）
  - 4 个产品（laptop/mouse/keyboard/monitor）
  - 4 个订单（with status）
  - 4 个指标（order_count/GMV/conversion_rate/active_users）

**阶段 5: Uvicorn 启动**
```python
uvicorn.run(
    "app.main:app",
    host=settings.host,    # 0.0.0.0
    port=settings.port,    # 8000
    reload=settings.debug  # true in dev
)
```
- 导入 FastAPI 实例 from `app.main:app`
- 注册所有路由（documents, chat, query, operations, diagnosis, products）
- 启用 CORS 中间件
- 设置全局异常处理
- 监听 file changes（如果 DEBUG=true）

### 后端 API 端点（`app/main.py`）

**路由注册**:
```python
app.include_router(documents.router)  # /api/documents/*
app.include_router(chat.router)       # /api/chat/*
app.include_router(query.router)      # /api/query/*
app.include_router(operations.router) # /api/operations/*
app.include_router(diagnosis.router)  # /api/diagnosis/*
app.include_router(products.router)   # /api/products/*
```

**CORS 配置** (允许来自):
- `http://localhost:3000`, `3001`, `5173`（本地开发）
- `https://ai-govern-pro.vercel.app`（生产）
- `https://*.vercel.app`（预览部署）

**健康检查**:
```
GET /health
响应: {"status":"ok","version":"0.1.0","database":"pgvector"}
```

**SPA 服务**:
- 若 `frontend/dist/` 存在（生产构建）：
  - `/` → `index.html`
  - `/assets/*` → 静态文件
  - `/**` → catch-all 返回 `index.html`（支持 React Router）
- 若不存在（开发）：
  - `/` → JSON API 信息

---

## 前端构建配置详解

### Vite 配置 (`frontend/vite.config.ts`)

**开发服务器**:
```typescript
server: {
  port: 3000,
  open: true,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api'),
    },
  },
}
```

**影响**: 所有 `/api/*` 请求自动代理到后端：
```
Frontend: axios.post('/api/chat', {...})
浏览器: POST http://localhost:3000/api/chat
Vite 代理: 转发到 http://localhost:8000/api/chat
后端: 处理请求
```

**代码分割**:
```typescript
manualChunks: {
  'vendor': ['react', 'react-dom'],
  'antd': ['antd', '@ant-design/icons'],
  'charts': ['recharts'],
}
```
输出 3 个独立文件，优化缓存策略

**导入别名** (减少冗长导入):
```typescript
'@': './src',
'@components': './src/components',
'@pages': './src/pages',
'@hooks': './src/hooks',
'@services': './src/services',
'@utils': './src/utils',
```

使用示例:
```typescript
// ✓ 简洁
import { Dashboard } from '@pages/Dashboard'
import { ChatPanel } from '@components/AGUI/ChatPanel'

// ✗ 冗长
import { Dashboard } from '../../../pages/Dashboard'
```

---

## 数据库初始化详解

### 表结构（`backend/app/models/db_models.py`）

| 表名 | 行数 | 用途 |
|------|------|------|
| `user` | 3 | 应用用户（admin/manager/user） |
| `product` | 4 | 产品目录 |
| `order` | 4 | 订单记录 |
| `metric` | 4 | 关键指标 |
| `document` | - | 知识库文档 |
| `document_chunk` | - | 分块文档 + 向量嵌入 |
| `operation_log` | - | 操作执行审计日志 |
| `query_cache` | - | SQL 查询缓存 |

### 示例数据

**用户** (User table):
```
1. admin (admin@example.com) - role: admin
2. manager (manager@example.com) - role: manager
3. user (user@example.com) - role: user
```

**产品** (Product table):
```
1. Laptop Pro - $1299
2. Wireless Mouse - $29
3. Mechanical Keyboard - $99
4. 4K Monitor - $399
```

**订单** (Order table):
```
1. Order#001 - user1 - products [1,2] - status: completed
2. Order#002 - user2 - products [3] - status: pending
3. Order#003 - user1 - products [4] - status: approved
4. Order#004 - user3 - products [1,3] - status: processing
```

**指标** (Metric table):
```
1. total_orders: 1234
2. gmv: $1,234,567
3. conversion_rate: 3.45%
4. active_users: 567
```

---

## 故障排查

### 问题 1: 后端启动失败 - "ModuleNotFoundError: No module named 'fastapi'"

**原因**: Python 依赖未安装

**解决**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 问题 2: 数据库连接错误 - "sqlite3.OperationalError"

**原因**: SQLite 路径不可写

**解决**:
```bash
cd backend
chmod 755 .
touch aigovern.db
python run.py
```

### 问题 3: 前端请求失败 - 504 Gateway Timeout

**原因**: 后端未运行或 API 端点错误

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查前端代理配置
cat frontend/vite.config.ts | grep -A5 "'/api'"
```

### 问题 4: 端口被占用 - "Address already in use"

**原因**: 端口 3000 或 8000 已被其他进程占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :3000    # 查找占用 3000 的进程
lsof -i :8000    # 查找占用 8000 的进程

# 杀死进程（替换 PID）
kill -9 <PID>
```

### 问题 5: LLM 请求失败 - "API Key invalid"

**原因**: `LLM_API_KEY` 配置错误或过期

**解决**:
```bash
# 检查环境变量
cat backend/.env | grep LLM_API_KEY

# 确保 API Key 有效
# 可在 backend/.env 中使用 mock 提供商进行测试
LLM_PROVIDER=mock  # 会返回虚拟数据
```

---

## 常用命令速查表

### 前端

```bash
cd frontend

# 开发
pnpm dev              # 启动开发服务器 (localhost:3000)
pnpm build            # 生产构建 → dist/
pnpm preview          # 本地预览生产构建

# 代码质量
pnpm lint             # ESLint 检查
pnpm type-check       # TypeScript 类型检查
pnpm format           # Prettier 自动格式化

# 测试
pnpm test             # 运行单元测试
```

### 后端

```bash
cd backend
source venv/bin/activate

# 启动
python run.py                           # 完整启动（初始化 DB + 启动服务）
python -m uvicorn app.main:app --reload # 仅启动服务（自动重载）

# 数据库
python scripts/init_db.py               # 创建表并注入示例数据

# 测试
python -m pytest                        # 运行单元测试
python -m pytest -v                     # 详细输出

# 查看依赖
pip list                                # 列出已安装包
pip show fastapi                        # 查看特定包信息
```

---

## 关键文件路径参考

```
/Users/wclu/AIGovern_Pro/
├── frontend/
│   ├── package.json                    ← 依赖列表 + npm scripts
│   ├── vite.config.ts                  ← 构建配置 + API 代理
│   ├── .env.example                    ← 环境变量模板
│   ├── src/
│   │   ├── main.tsx                    ← React 入口
│   │   ├── App.tsx                     ← 路由配置
│   │   ├── pages/                      ← 5 个核心页面
│   │   └── components/
│   │       └── AGUI/ChatPanel.tsx      ← 对话面板
│   └── dist/                           ← 生产构建输出
│
├── backend/
│   ├── run.py                          ← 启动脚本（重要）
│   ├── requirements.txt                ← 依赖列表
│   ├── .env.example                    ← 环境变量模板
│   ├── app/
│   │   ├── main.py                     ← FastAPI 实例 + 路由
│   │   ├── core/
│   │   │   ├── config.py               ← 设置管理
│   │   │   └── database.py             ← SQLAlchemy 配置
│   │   ├── api/                        ← 6 个路由模块
│   │   ├── services/                   ← 业务逻辑
│   │   └── models/
│   │       └── db_models.py            ← ORM 表定义
│   ├── scripts/
│   │   └── init_db.py                  ← 独立初始化脚本
│   └── aigovern.db                     ← SQLite 数据库（开发）
│
├── docs/
│   ├── DESIGN_SYSTEM.md                ← UI 规范
│   ├── IMPLEMENTATION_GUIDE.md         ← 开发指南
│   └── TECH_ARCHITECTURE.md            ← 技术架构
│
├── CLAUDE.md                           ← 项目开发规则
├── README.md                           ← 项目说明
├── vercel.json                         ← Vercel 部署配置
└── research/
    └── docs/                           ← 研究文档
```

---

## 下一步操作

### 即时启动（完整版）

1. **终端 1 - 启动后端**:
   ```bash
   cd backend
   source venv/bin/activate
   python run.py
   # 等待输出: "Uvicorn running on http://0.0.0.0:8000"
   ```

2. **终端 2 - 启动前端**:
   ```bash
   cd frontend
   pnpm dev
   # 等待输出: "➜  Local:   http://localhost:3000/"
   ```

3. **浏览器** - 访问应用:
   ```
   http://localhost:3000
   ```

### 验证清单

- [ ] 后端健康检查: `curl http://localhost:8000/health` 返回 `{"status":"ok"}`
- [ ] Swagger API 文档: http://localhost:8000/docs 可访问
- [ ] 前端主页: http://localhost:3000 加载成功
- [ ] 数据库表创建: `backend/aigovern.db` 存在（SQLite）
- [ ] 示例数据注入: Dashboard 页面显示 KPI 数据

### 推荐后续开发

1. **配置 LLM API**
   - 在 `backend/.env` 配置 `LLM_API_KEY`
   - 测试知识问答 API: `POST /api/chat`

2. **运行代码质量检查**
   - 前端: `pnpm lint && pnpm type-check`
   - 后端: `python -m pytest`

3. **集成 CI/CD**
   - 参考 `vercel.json` 进行 Vercel 部署
   - 或参考 GitHub Actions 工作流

---

## 系统架构决策

### 为什么选择这个技术栈？

**前端: React 18 + Vite**
- 快速开发体验 (HMR 毫秒级)
- TypeScript 类型安全
- Ant Design 企业级组件库
- 小 bundle size (code splitting)

**后端: FastAPI + Python**
- 快速原型开发
- 原生 async/await 支持
- 自动 API 文档生成 (Swagger/ReDoc)
- AI/ML 库生态完整（LangChain, scikit-learn）

**数据库: PostgreSQL + pgvector**
- 成熟的关系型数据库
- pgvector 扩展支持向量相似度搜索（RAG 必须）
- SQLite 用于开发快速迭代

**LLM 集成: 豆包/通义千问**
- 国内 API，低延迟
- 支持嵌入向量生成
- 成本优化

---

**状态**: ✅ 完整 - 项目已就绪，所有依赖已配置，可直接启动

**最后修改**: 2026-03-31
**维护者**: Claude Code
