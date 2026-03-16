# Supabase + pgvector 配置指南

本文档详细说明如何使用 Supabase PostgreSQL + pgvector 扩展来替代 Milvus，实现真实的向量化 RAG。

## 📋 前提条件

- Supabase 账户（免费）
- Python 3.8+ 环境
- Git 与项目代码

---

## 🚀 第一阶段：Supabase 项目创建

### 步骤 1.1：创建 Supabase 账户

1. 访问 [Supabase](https://supabase.com)
2. 点击 "Start your project"
3. 使用 GitHub 或邮箱注册

### 步骤 1.2：创建新项目

1. **项目名称**：`aigovern-pro`
2. **数据库密码**：设置强密码（需保存）
3. **地区**：选择最近的区域
   - 中国用户建议选择 Singapore（新加坡）
4. 点击 "Create new project"

### 步骤 1.3：获取数据库连接信息

项目创建后，在 Supabase 控制台：

1. 进入 **Settings** → **Database** → **Connection string**
2. 复制 PostgreSQL 连接字符串（选择 "Connection pooler"）
3. 格式如下：
   ```
   postgresql://postgres.YOUR_PROJECT_REF:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres
   ```

保存此连接字符串，后续配置需要。

---

## 🔧 第二阶段：本地环境配置

### 步骤 2.1：安装依赖

```bash
cd /Users/wclu/AIGovern_Pro/backend

# 安装 Python 依赖
pip install -r requirements.txt

# 确认已安装以下关键库
pip list | grep -E "pgvector|psycopg2|sqlalchemy"
```

**关键依赖**：
- `pgvector>=0.3.0` - PostgreSQL 向量扩展的 Python 绑定
- `psycopg2-binary>=2.9.0` - PostgreSQL 驱动
- `sqlalchemy>=2.0.30` - ORM 框架

### 步骤 2.2：配置环境变量

创建 `.env` 文件（复制自 `.env.example`）：

```bash
cp .env.example .env
```

编辑 `.env` 文件，替换以下变量：

```env
# 数据库 - Supabase PostgreSQL with pgvector
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres
DB_ECHO=false

# Redis（可选，本地开发可不配）
REDIS_URL=redis://localhost:6379/0

# pgvector 配置
VECTOR_DIMENSIONS=768
VECTOR_SIMILARITY_METRIC=cosine

# LLM 配置（使用豆包或通义千问）
LLM_PROVIDER=doubao  # 或 qwen
LLM_API_KEY=your_api_key_here
LLM_MODEL_NAME=doubao-pro
LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3
```

**注意**：将 `YOUR_PROJECT_REF` 和 `PASSWORD` 替换为实际值。

---

## 🗄️ 第三阶段：Supabase 数据库初始化

### 步骤 3.1：启用 pgvector 扩展

在 Supabase 控制台执行 SQL（SQL Editor）：

```sql
-- 启用 pgvector 扩展（必须）
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展安装成功
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

### 步骤 3.2：创建表结构

在 SQL Editor 中执行以下 SQL 创建所有必要的表：

```sql
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    sku VARCHAR(50) UNIQUE,
    price DECIMAL(10,2),
    stock INT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    product_id INT REFERENCES products(id),
    quantity INT,
    amount DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识库文档表（带向量）
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    category VARCHAR(50) DEFAULT 'general',
    embedding_status VARCHAR(50) DEFAULT 'pending',
    chunk_count INT DEFAULT 0,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档分块表（带向量）
CREATE TABLE IF NOT EXISTS document_chunks_with_vectors (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 为向量列创建索引（加速查询）
CREATE INDEX IF NOT EXISTS idx_documents_embedding
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON document_chunks_with_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operations_log (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    operation_type VARCHAR(100),
    operation_target VARCHAR(100),
    operation_detail JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 指标表
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_date VARCHAR(10),
    metric_value DECIMAL(12,2),
    dimension_1 VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 查询缓存表
CREATE TABLE IF NOT EXISTS query_cache (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(100) UNIQUE,
    result JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 步骤 3.3：插入示例数据（可选）

```sql
-- 插入示例用户
INSERT INTO users (name, email, role) VALUES
    ('张三', 'zhangsan@company.com', 'admin'),
    ('李四', 'lisi@company.com', 'user');

-- 插入示例商品
INSERT INTO products (name, sku, price, stock, category) VALUES
    ('笔记本电脑', 'SKU001', 5999.00, 50, 'electronics'),
    ('无线鼠标', 'SKU002', 199.00, 200, 'electronics');

-- 插入示例订单
INSERT INTO orders (user_id, product_id, quantity, amount, status) VALUES
    (1, 1, 1, 5999.00, 'completed'),
    (2, 2, 2, 398.00, 'pending');
```

---

## 💻 第四阶段：本地开发和测试

### 步骤 4.1：运行后端服务

```bash
cd /Users/wclu/AIGovern_Pro/backend

# 使用项目的启动脚本
python run.py
```

服务启动成功后，输出：
```
✅ 数据库连接成功
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 步骤 4.2：测试 API 连接

打开浏览器访问 API 文档：
```
http://localhost:8000/docs
```

### 步骤 4.3：测试文档上传和向量化

使用 curl 或 Postman：

```bash
# 创建测试文档
curl -X POST \
  http://localhost:8000/api/documents/upload \
  -F "file=@test.txt" \
  -F "title=测试文档" \
  -F "category=general"

# 预期响应：
{
  "id": 1,
  "title": "测试文档",
  "category": "general",
  "embedding_status": "completed",
  "chunk_count": 3,
  "created_at": "2024-01-15T10:30:45"
}
```

### 步骤 4.4：测试 RAG 检索

```bash
# 测试向量检索
curl -X POST \
  http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档的主要内容是什么？",
    "session_id": "test_session"
  }'

# 预期响应：
{
  "answer": "根据文档内容...",
  "sources": [
    {
      "document_id": 1,
      "title": "文档 1",
      "relevance": 0.92,
      "text_preview": "..."
    }
  ],
  "confidence": 0.92,
  "session_id": "test_session"
}
```

---

## 🔍 第五阶段：Supabase 控制台验证

### 验证向量化数据已存储

在 Supabase SQL Editor 中执行：

```sql
-- 查询文档表
SELECT id, title, embedding_status, chunk_count FROM documents;

-- 查询分块表（检查向量是否存储）
SELECT id, document_id, chunk_index, embedding IS NOT NULL as has_embedding
FROM document_chunks_with_vectors
LIMIT 5;

-- 测试向量相似度查询（示例）
-- 生成查询向量后执行相似度搜索
SELECT
    id,
    chunk_index,
    chunk_text,
    1 - (embedding <=> '[0.1, 0.2, 0.3, ...]'::vector(768)) as similarity
FROM document_chunks_with_vectors
ORDER BY embedding <=> '[0.1, 0.2, 0.3, ...]'::vector(768)
LIMIT 5;
```

---

## 🚀 第六阶段：前后端整合

### 步骤 6.1：启动前端服务

```bash
cd /Users/wclu/AIGovern_Pro/frontend

# 安装依赖
npm install

# 启动开发服务
npm run dev
```

前端运行在：`http://localhost:5173`

### 步骤 6.2：测试完整流程

1. **打开前端**：http://localhost:5173
2. **进入知识库页面**（Documents）
3. **上传文档**：拖拽或选择 PDF/TXT 文件
4. **等待向量化完成**：观察 embedding_status 变为 "completed"
5. **进入 AGUI 对话面板**（右侧浮窗）
6. **提问**：输入与文档相关的问题
7. **验证答案**：
   - 答案应基于上传的文档内容
   - 引用应显示文档来源和相关度
   - 置信度应较高（>0.8）

---

## 🛠️ 常见问题排查

### 问题 1：连接超时

**症状**：`psycopg2.OperationalError: could not translate host name...`

**解决方案**：
1. 检查 DATABASE_URL 中的 host 是否正确
2. 确保 Supabase 项目已启动
3. 尝试使用 "Session pooler" 而非 "Transaction pooler"

### 问题 2：pgvector 扩展未找到

**症状**：`ERROR: type "vector" does not exist`

**解决方案**：
1. 在 Supabase SQL Editor 中重新执行：
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. 确保在正确的数据库中执行

### 问题 3：向量化失败

**症状**：embedding_status = "failed"

**解决方案**：
1. 检查 LLM_API_KEY 是否正确配置
2. 查看后端日志中的错误信息
3. 确保 LLM 服务可访问

### 问题 4：检索结果为空

**症状**：提问后没有返回任何结果

**解决方案**：
1. 确保文档已成功上传（embedding_status = "completed"）
2. 检查向量生成是否成功：
   ```sql
   SELECT COUNT(*) FROM document_chunks_with_vectors
   WHERE embedding IS NOT NULL;
   ```
3. 尝试测试特定关键词的查询

---

## 📚 参考资源

- [Supabase 官方文档](https://supabase.com/docs)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [SQLAlchemy pgvector 集成](https://github.com/pgvector/pgvector-python)

---

## ✅ 配置完成检查清单

- [ ] Supabase 账户创建成功
- [ ] PostgreSQL 连接字符串已获取
- [ ] pgvector 扩展已启用
- [ ] 数据库表已创建
- [ ] 环境变量已配置（DATABASE_URL）
- [ ] Python 依赖已安装
- [ ] 后端服务启动成功
- [ ] 文档上传 API 测试通过
- [ ] 向量化流程验证完成
- [ ] RAG 检索功能正常
- [ ] 前后端整合测试通过

完成以上所有步骤后，Supabase + pgvector 配置完成！🎉
