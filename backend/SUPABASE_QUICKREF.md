# Supabase + pgvector 快速参考卡

## 🎯 核心配置（5分钟快速版）

### 1️⃣ Supabase 项目创建
```
访问 https://supabase.com → Start project
- 项目名：aigovern-pro
- 地区：Singapore
- 保存密码和连接字符串
```

### 2️⃣ 启用 pgvector（SQL Editor）
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3️⃣ 创建表（SQL Editor）
```sql
-- 复制 SUPABASE_SETUP.md 中第三阶段的所有 SQL
-- 或直接运行脚本文件
```

### 4️⃣ 配置环境变量
```bash
# 编辑 .env
DATABASE_URL=postgresql://postgres.YOUR_PROJECT:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres
LLM_API_KEY=your_key_here
```

### 5️⃣ 安装依赖 & 启动
```bash
pip install -r requirements.txt
python run.py
```

---

## 🔑 关键环境变量

| 变量 | 值 | 说明 |
|------|-----|------|
| `DATABASE_URL` | `postgresql://...` | Supabase 连接串 |
| `VECTOR_DIMENSIONS` | `768` | 向量维度（固定） |
| `VECTOR_SIMILARITY_METRIC` | `cosine` | 相似度计算方式 |
| `LLM_PROVIDER` | `doubao` | 大模型服务商 |
| `LLM_API_KEY` | `your_key` | API Key |

---

## 🧪 验证命令

```bash
# 1. 检查数据库连接
psql "postgresql://postgres.YOUR_PROJECT:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres" -c "SELECT 1"

# 2. 检查 pgvector
psql "..." -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname = 'vector';"

# 3. 测试后端
curl http://localhost:8000/health

# 4. 上传文档
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.txt" -F "title=Test"

# 5. 提问
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is in the document?"}'
```

---

## 📊 SQL 向量查询示例

```sql
-- 基础相似度查询
SELECT id, chunk_text, embedding <=> query_vector AS distance
FROM document_chunks_with_vectors
ORDER BY embedding <=> query_vector
LIMIT 5;

-- 带距离转换为相似度（0-1）
SELECT id, chunk_text, 1 - (embedding <=> query_vector) AS relevance
FROM document_chunks_with_vectors
ORDER BY embedding <=> query_vector
LIMIT 5;

-- 计数
SELECT COUNT(*) FROM document_chunks_with_vectors WHERE embedding IS NOT NULL;
```

---

## ⚡ 性能提示

- **创建索引**：向量查询建议在 embedding 列上创建 ivfflat 或 hnsw 索引
- **批量插入**：大量文档时使用批量上传优化性能
- **连接池**：生产环境使用 "Connection pooler" 而非 "Transaction pooler"

---

## 🚨 常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `type "vector" does not exist` | pgvector 未启用 | 执行 `CREATE EXTENSION vector;` |
| `could not translate host name` | 连接字符串错误 | 检查 DATABASE_URL |
| `embedding_status = "failed"` | LLM API 问题 | 检查 LLM_API_KEY 和网络 |
| `no results` | 向量未存储 | 检查文档是否成功上传 |

---

## 📝 核心文件修改清单

✅ `requirements.txt` - 移除 pymilvus，添加 pgvector
✅ `.env` - 替换 DATABASE_URL 为 Supabase
✅ `app/core/config.py` - 移除 Milvus 配置
✅ `app/core/database.py` - 移除 Milvus 初始化
✅ `app/models/db_models.py` - 使用 Vector(768) 类型
✅ `app/services/rag_service.py` - 使用 pgvector SQL 查询
✅ `app/api/documents.py` - 存储向量到 pgvector
✅ `app/main.py` - 移除 Milvus 启动事件

---

## 🎓 学习资源

- pgvector 文档：https://github.com/pgvector/pgvector
- Supabase 向量指南：https://supabase.com/docs/guides/ai
- SQLAlchemy + pgvector：https://github.com/pgvector/pgvector-python
