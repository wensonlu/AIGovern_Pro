# ChatPanel API 集成指南

## 🎯 完成的工作

### 第三阶段成果（前后端整合 - P1优先级）✅

#### 1️⃣ API 服务层增强
- ✅ `frontend/src/services/api.ts`
  - 重试机制（最多3次，指数退避）
  - AbortController超时（30秒）
  - 8个API响应接口定义
  - 所有API函数类型注解

#### 2️⃣ useApiCall 自定义Hook
- ✅ `frontend/src/hooks/useApiCall.ts`
  - 统一API状态管理
  - 并发控制
  - Ant Design消息集成
  - 回调支持

#### 3️⃣ ChatPanel 真实API集成
- ✅ `frontend/src/components/AGUI/ChatPanel.tsx`
  - 移除mock逻辑
  - 连接真实/api/chat
  - sessionId持久化
  - 源文档溯源

---

## 🧪 测试验证

### 快速测试步骤

#### 步骤1: 启动后端
```bash
cd backend
source venv/bin/activate
python3 run.py
# 输出: 启动后端服务于 0.0.0.0:8000
```

#### 步骤2: 验证API集成（可选）
```bash
cd backend
source venv/bin/activate
python3 test_api_integration.py
```

预期输出：
```
✓ 健康检查 - GET /health (200 OK)
✓ ChatAPI - POST /api/chat (200 OK)
✓ 多查询测试 - 3个查询通过
✓ 所有测试完成
```

#### 步骤3: 启动前端
```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
```

#### 步骤4: 在ChatPanel测试
1. 点击右下角的消息图标打开ChatPanel
2. 输入问题，例如：
   - "新员工入职有哪些步骤？"
   - "产品的保修期是多久？"
   - "过去7天的订单总数是多少？"
3. 点击发送或按Enter键
4. 观察回答和引用的文档来源

---

## 🔗 API 请求/响应格式

### ChatPanel 调用后端API

**请求**
```typescript
POST /api/chat
{
  "question": "新员工入职有哪些步骤？",
  "session_id": "session_1234567890_abc",
  "top_k": 5
}
```

**响应**
```typescript
{
  "answer": "根据公司入职指南...",
  "sources": [
    {
      "document_id": 1,
      "title": "文档 1",
      "chunk_index": 0,
      "relevance": 0.95,
      "text_preview": "..."
    }
  ],
  "confidence": 0.88,
  "session_id": "session_1234567890_abc",
  "timestamp": "2026-03-15T20:26:42.021845"
}
```

---

## 📝 关键改进

### 类型安全
- ✅ ChatResponse 接口精确匹配后端响应
- ✅ SourceReference 类型正确
- ✅ 所有API函数都有明确的返回类型

### 网络韧性
- ✅ 自动重试失败的请求
- ✅ 指数退避避免频繁重试
- ✅ 30秒超时保护

### 用户体验
- ✅ Loading状态实时反馈
- ✅ 错误消息清晰提示
- ✅ SessionId维持对话连贯性

---

## 📋 下一步任务

### 待完成（P2-P4优先级）

1. **DataQuery页面集成** (P2)
   - 连接 POST /api/query
   - 实现SQL预览
   - 图表展示

2. **SmartOps页面集成** (P3)
   - 连接 GET /api/operations/templates
   - 实现操作执行
   - 日志显示

3. **Diagnosis页面集成** (P4)
   - 连接 GET /api/diagnosis/metrics
   - 实现指标展示
   - 建议生成

---

## 🐛 故障排除

### 如果ChatPanel无法连接后端

1. **检查后端是否运行**
   ```bash
   curl http://localhost:8000/health
   # 应返回: {"status":"ok","version":"0.1.0"}
   ```

2. **检查 CORS 配置**
   - 后端应允许 localhost:5173（Vite 默认端口）
   - 查看 backend/app/main.py 中的 CORSMiddleware

3. **检查前端环境变量**
   - 确保 frontend/.env 包含 VITE_API_URL=http://localhost:8000

4. **查看浏览器控制台错误**
   - F12 → Console 标签
   - 查看 Network 标签确认 API 调用

---

**最后更新**: 2026-03-15 20:30
**测试状态**: ✅ 所有测试通过
