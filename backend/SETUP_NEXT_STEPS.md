# 🔄 Supabase 配置 - 5分钟快速指南

## 当前状态
- ✅ 后端代码已改为使用 pgvector
- ✅ LLM 模型已配置
- ❌ 数据库仍使用 SQLite（不支持 pgvector）

## 问题说明
SQLite 无法存储向量，需要切换到 PostgreSQL。您有两个选择：

### 方案 A: Supabase（推荐，最快）
1. 访问 https://supabase.com
2. 点击 "Start your project"
3. 使用 GitHub 或邮箱注册
4. 创建新项目：
   - 项目名：`aigovern-pro`
   - 密码：设置强密码
   - 地区：Singapore
5. 项目创建后，进入 **Settings** → **Database** → **Connection string**
6. 复制 "Connection pooler" 连接字符串
7. 在 Supabase SQL Editor 执行：
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
8. 更新 `.env` 文件：
   ```bash
   DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres
   ```

### 方案 B: 本地 PostgreSQL（可选）
1. 使用 Docker：
   ```bash
   docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:latest
   ```
2. 安装 pgvector：
   ```bash
   docker exec postgres psql -U postgres -c "CREATE EXTENSION vector;"
   ```
3. 更新 `.env`：
   ```bash
   DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
   ```

## 配置完成后
1. 测试 LLM：
   ```bash
   source venv/bin/activate
   set -a && source .env && set +a
   python3 test_llm.py
   ```

2. 初始化数据库：
   ```bash
   python3 run.py
   ```

3. 启动后端：
   ```bash
   python3 run.py
   ```

4. 启动前端（新终端）：
   ```bash
   cd ../frontend
   npm run dev
   ```

## 测试验证
- [ ] LLM 模型正常（能生成向量和文本）
- [ ] 数据库连接成功
- [ ] 后端启动成功
- [ ] 前端启动成功
- [ ] 上传文档并进行知识问答

---
**更多详情见**：`SUPABASE_SETUP.md` 和 `SUPABASE_QUICKREF.md`
