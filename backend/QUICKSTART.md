# FastAPI 后端项目 - 快速启动指南

## 环境要求

- Python 3.11+
- PostgreSQL 13+（可选，本地开发可用 SQLite）
- Redis 7.0+（可选）
- Milvus 2.3+（可选）

## 安装依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env，填入实际配置
vim .env  # 或使用你的编辑器
```

## 启动后端服务

### 方式一：使用启动脚本

```bash
python run.py
```

### 方式二：直接使用 Uvicorn

```bash
# 开发模式（支持热重载）
python -m uvicorn app.main:app --reload --port 8000

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 方式三：使用 Gunicorn（生产环境推荐）

```bash
# 需要先安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

## 初始化数据库

```bash
# 创建数据库表并插入示例数据
python scripts/init_db.py
```

## API 测试

### 1. 查看 API 文档

启动服务后，访问以下 URL：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. 健康检查

```bash
curl http://localhost:8000/health
```

响应：
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### 3. 知识问答 API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "新员工入职有哪些步骤？",
    "session_id": "user123",
    "top_k": 5
  }'
```

### 4. 数据查询 API

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "过去7天的订单总数",
    "context": null
  }'
```

### 5. 智能操作 API

```bash
# 获取操作模板
curl http://localhost:8000/api/operations/templates

# 执行操作
curl -X POST http://localhost:8000/api/operations/approve_order/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "approve_order",
    "parameters": {
      "order_ids": [1, 2, 3],
      "reason": "自动审批"
    }
  }'
```

### 6. 经营诊断 API

```bash
# 获取诊断总结
curl http://localhost:8000/api/diagnosis/summary

# 获取诊断指标
curl http://localhost:8000/api/diagnosis/metrics
```

## 常见问题

### Q: 如何连接真实的 PostgreSQL 数据库？

A: 在 `.env` 中修改 `DATABASE_URL`：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/aigovern_db
```

### Q: 如何配置 LLM API？

A: 在 `.env` 中设置：

```env
LLM_PROVIDER=doubao
LLM_API_KEY=your_api_key
LLM_MODEL_NAME=doubao-pro
```

### Q: 后端启动失败怎么办？

A: 检查以下几点：

1. 检查 Python 版本：`python --version`
2. 检查依赖安装：`pip list | grep fastapi`
3. 查看错误日志：启动时的完整错误信息
4. 检查端口占用：`lsof -i :8000`

### Q: 如何运行单元测试？

A: 暂时未实现，敬请期待。

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   ├── services/         # 业务逻辑
│   ├── models/           # 数据模型
│   ├── core/             # 核心配置
│   ├── tools/            # 工具模块
│   ├── middleware/       # 中间件
│   └── main.py          # 应用入口
├── scripts/             # 脚本
├── run.py              # 启动脚本
├── requirements.txt    # 依赖
├── .env.example       # 环境变量模板
└── README.md          # 本文件
```

## 下一步

1. ✅ 实现四大核心 API 端点
2. ⏳ 集成 LLM（豆包/通义千问）
3. ⏳ 连接 Milvus 向量库
4. ⏳ 实现数据库查询执行
5. ⏳ 添加认证和权限控制
6. ⏳ 编写单元测试

## 支持

如有问题，请提交 Issue 或联系开发团队。
