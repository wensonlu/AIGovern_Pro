# Supabase 数据库配置指南

> 本文档指导如何将 AIGovern Pro 连接到 Supabase 数据库

---

## 📋 配置概览

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Vercel 前端   │────▶│  Vercel Serverless│────▶│   Supabase DB   │
│  (React SPA)    │     │   (FastAPI)      │     │  (PostgreSQL)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        环境变量 DATABASE_URL      pgvector 向量扩展
```

---

## 🔑 第一步：获取 Supabase 连接信息

### 1.1 打开 Supabase Dashboard
访问：https://app.supabase.com/project/jdfrubpfjwhbvxfdyzah

### 1.2 获取数据库连接字符串
1. 进入 Project Settings → Database
2. 找到 **Connection string** 部分
3. 选择 **URI** 格式
4. 复制连接字符串（包含密码）

格式示例：
```
postgresql://postgres:[YOUR-PASSWORD]@db.jdfrubpfjwhbvxfdyzah.supabase.co:5432/postgres
```

### 1.3 获取 API 密钥
1. 进入 Project Settings → API
2. 复制 **anon public** 密钥（用于前端）
3. 复制 **service_role secret** 密钥（用于后端，保密！）

---

## 📝 第二步：配置环境变量

### 2.1 本地开发环境

创建 `.env` 文件：

```bash
cd /Users/wclu/AIGovern_Pro/backend
cp ../.env.example .env
```

编辑 `.env` 文件，填入实际值：

```env
# Supabase 数据库连接
DATABASE_URL=postgresql://postgres:your-password@db.jdfrubpfjwhbvxfdyzah.supabase.co:5432/postgres
SUPABASE_URL=https://jdfrubpfjwhbvxfdyzah.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 其他配置
SECRET_KEY=your-secret-key
DOUBAO_API_KEY=your-doubao-api-key
```

### 2.2 Vercel 生产环境

在 Vercel Dashboard 中配置：

1. 进入项目 → Settings → Environment Variables
2. 添加以下变量：

| 变量名 | 值 | 环境 |
|-------|-----|-----|
| `DATABASE_URL` | `postgresql://postgres:xxx@db...supabase.co:5432/postgres` | Production |
| `SUPABASE_URL` | `https://jdfrubpfjwhbvxfdyzah.supabase.co` | Production |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIs...` | Production |
| `SECRET_KEY` | `your-secret-key` | Production |
| `DOUBAO_API_KEY` | `your-doubao-api-key` | Production |

---

## 🗄️ 第三步：数据库初始化（如需要）

如果 Supabase 数据库为空，需要初始化表结构：

### 3.1 使用 Supabase SQL Editor

1. 打开 Supabase Dashboard → SQL Editor
2. 新建查询
3. 执行以下 SQL：

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建商品表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建文档表（RAG 使用）
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    embedding_status VARCHAR(50) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filename VARCHAR(500)
);

-- 创建文档分块表（RAG 使用）
CREATE TABLE IF NOT EXISTS document_chunks_with_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operations_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    operation_target VARCHAR(200) NOT NULL,
    operation_detail JSONB,
    status VARCHAR(50) DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建价格历史表
CREATE TABLE IF NOT EXISTS product_price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    old_price DOUBLE PRECISION NOT NULL,
    new_price DOUBLE PRECISION NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_by_id INTEGER,
    reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_operations_log_created_at ON operations_log(created_at);
```

### 3.2 插入示例数据（可选）

```sql
-- 插入示例用户
INSERT INTO users (name, email, role) VALUES
('管理员', 'admin@example.com', 'admin'),
('张三', 'zhangsan@example.com', 'user'),
('李四', 'lisi@example.com', 'user');

-- 插入示例商品
INSERT INTO products (name, sku, price, stock, category) VALUES
('笔记本电脑', 'LAPTOP001', 5999.00, 50, '电子产品'),
('鼠标', 'MOUSE001', 99.00, 200, '配件'),
('键盘', 'KEYBOARD001', 199.00, 150, '配件'),
('显示器', 'MONITOR001', 1999.00, 30, '电子产品');

-- 插入示例订单
INSERT INTO orders (user_id, product_id, quantity, amount, status) VALUES
(1, 1, 1, 5999.00, 'completed'),
(2, 2, 2, 198.00, 'pending'),
(3, 3, 1, 199.00, 'completed');
```

---

## ✅ 第四步：验证连接

### 4.1 本地测试

```bash
cd /Users/wclu/AIGovern_Pro/backend
source venv/bin/activate

# 设置环境变量
export DATABASE_URL="postgresql://postgres:your-password@db.jdfrubpfjwhbvxfdyzah.supabase.co:5432/postgres"

# 启动服务
python run.py

# 测试 API
curl http://localhost:8000/health
curl http://localhost:8000/api/diagnosis/metrics
```

### 4.2 检查表数据

```python
# 测试脚本
from app.core.database import SessionLocal
from app.models.db_models import Product

db = SessionLocal()
products = db.query(Product).all()
print(f"商品数量: {len(products)}")
for p in products:
    print(f"  - {p.name}: {p.price}元")
db.close()
```

---

## 🔧 常见问题

### Q1: 连接超时或失败
```
Error: connection timeout
```
**解决：**
1. 检查密码是否正确
2. 确认 IP 白名单设置（Supabase → Database → IPv4/IPv6）
3. 使用连接池参数：`?pool_size=20&max_overflow=0`

### Q2: pgvector 扩展未启用
```
Error: type "vector" does not exist
```
**解决：**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Q3: SSL 连接问题
```
Error: SSL connection is required
```
**解决：** Supabase 强制 SSL，连接字符串添加：
```
?sslmode=require
```

### Q4: 数据库权限不足
```
Error: permission denied for table
```
**解决：** 在 Supabase SQL Editor 执行：
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

---

## 📚 相关文档

- [Vercel 部署指南](./DEPLOY_VERCEL.md)
- [环境变量说明](./.env.example)
- [Supabase 官方文档](https://supabase.com/docs)

---

## 🎉 完成！

配置完成后，您的 AIGovern Pro 应用将使用 Supabase 作为数据库，支持：
- ✅ PostgreSQL 关系型数据存储
- ✅ pgvector 向量检索（RAG）
- ✅ 实时数据同步
- ✅ 自动备份和恢复
