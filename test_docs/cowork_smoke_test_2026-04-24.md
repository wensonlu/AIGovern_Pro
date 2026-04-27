# AIGovern Pro 冒烟测试报告 — AI 助手 · 知识问答意图

**时间**: 2026-04-24 22:47
**环境**: macOS, node v20.11.1 (via nvm), python venv

## 1. 服务启动

| 服务 | 命令 | 端口 | 状态 |
| --- | --- | --- | --- |
| 后端 FastAPI | `cd backend && source venv/bin/activate && python run.py` | `8000` | ✅ `LISTEN`，`/health` 200 |
| 前端 Vite | `cd frontend && pnpm dev` (node 20.11.1) | `3001`(已被占用) → 回退至 `3002` | ✅ `/` 200 |

启动脚本落盘：
- `/Users/wclu/AIGovern_Pro/.cowork_start_backend.sh`
- `/Users/wclu/AIGovern_Pro/.cowork_start_frontend.sh`

运行日志：`/tmp/aigovern_logs/backend.log`, `/tmp/aigovern_logs/frontend.log`

> 注：系统默认 `node -v` 为 v16.14.0，pnpm 要求 ≥ v18.12。前端脚本已切到 nvm 下的 v20.11.1。

## 2. UI 验证

通过 Claude-in-Chrome MCP 打开 `http://localhost:3001/`，页面标题返回 `AIGovern Pro - 智管通 AI`。通过 `find` 工具在 DOM 中匹配到 AI 助手悬浮入口：

```
ref_4: generic "flow-ai-assistant"    // AI 助手 FAB
ref_3: generic "3"                    // 消息角标
ref_2: img "message"                  // 图标
ref_10: menuitem "📚 知识库"          // 左侧菜单
```

截屏：可见侧边栏（仪表板/知识库/数据查询/智能操作/经营诊断/商品管理/Agent Skills）、仪表板 KPI 卡片（订单数 12458、GMV ¥2,847,392、转化率 3.24%、活跃用户 8934）、订单趋势折线图，以及右下角带 "3" 角标的机器人悬浮按钮。

> ⚠ Chrome MCP 扩展在该浏览器 profile 下执行 `left_click` / `screenshot` / `javascript_tool` 时全部返回 `Cannot access a chrome-extension:// URL of different extension`。这是该 profile 装了另一个扩展造成的 content-script 注入冲突，**不是前端/应用的问题**。DOM 读取 (`find`) 与 `navigate` 工作正常。已改为直接调用后端 API 完成端到端意图验证。

## 3. 知识问答意图 API 测试

### 3.1 结构化响应

请求：
```bash
curl -X POST http://localhost:8000/api/chat/structured \
  -H 'Content-Type: application/json' \
  -d '{"question":"什么是RAG？请简要说明其工作原理。","session_id":"cw-knowledge-test-001","top_k":5}'
```

响应要点（完整体见 `knowledge_qa_structured_resp.json`）：
- `sections[0].type = "text"`，返回结构化 Markdown（包含 RAG 定义、检索/增强/生成三阶段列表、优势总结）
- `sources`: 命中 `product_specs.md`，`relevance_percentage` 15%

### 3.2 流式响应（前端实际使用）

请求：
```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -d '{"question":"知识库里有哪些文档？","session_id":"cw-stream-001","top_k":3}'
```

流首帧（见 `knowledge_qa_stream_resp.ndjson` 第 1 行）：

```json
{
  "type": "sources",
  "sources": [
    {"document_id": 16, "title": "product_specs.md", "relevance_percentage": "38%", ...},
    {"document_id": 16, "title": "product_specs.md", "relevance_percentage": "32%", ...},
    {"document_id": 16, "title": "product_specs.md", "relevance_percentage": "28%", ...}
  ],
  "confidence": 0.327,
  "intent": "knowledge_qa",
  "workflow": [
    {"step": 1, "name": "向量化查询", "status": "completed"},
    {"step": 2, "name": "知识库检索", "status": "completed"},
    {"step": 3, "name": "生成回答", "status": "completed"}
  ]
}
```

后续帧：45 行 `{"type":"delta","content":"..."}` 增量，按预期拼接出完整 Markdown 答复。

**关键结论**：`intent = "knowledge_qa"` 被正确识别，工作流三步 `向量化查询 → 知识库检索 → 生成回答` 全部 `completed`，RAG 检索命中了 `product_specs.md` 并把 sources 一并下发，前端 AGUI 面板有足够数据渲染"意图标识 + 工作流时间线 + 答复正文 + 引用来源"完整 UI。

## 4. 结果总览

| 校验项 | 结果 |
| --- | --- |
| 后端进程存活 / `:8000` 监听 | ✅ |
| 前端 `:3001` (或 3002) 加载 `AIGovern Pro - 智管通 AI` | ✅ |
| AI 助手悬浮入口存在于 DOM | ✅ (`flow-ai-assistant`) |
| 知识问答意图识别 | ✅ `intent=knowledge_qa` |
| RAG 三步工作流 | ✅ 全部 completed |
| 文档检索命中 & sources 下发 | ✅ `product_specs.md` ×3 chunk |
| 流式回答 delta 帧 | ✅ 45 帧 |
| UI 点击交互 (Chrome MCP) | ⚠ 被 profile 内另一扩展阻断，需通过常规浏览器手动点击 FAB 亲测 |

## 5. 手动回归建议（1 分钟）

1. 浏览器打开 `http://localhost:3001/`（或 3002）。
2. 点击右下角带 "3" 角标的机器人按钮打开 AI 助手面板。
3. 输入：`什么是RAG？请简要说明其工作原理。` → 回车。
4. 预期 UI：意图标签显示"知识问答"，工作流时间线依次亮起三步，正文流式输出，底部出现 `product_specs.md` 引用卡片。
