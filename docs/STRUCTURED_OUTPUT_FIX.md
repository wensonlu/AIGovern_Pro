# 结构化输出框架 - 问题诊断与修复

**日期**: 2026-04-27  
**问题**: 前端调用的仍然是旧的流式 API，而不是新的结构化 API  
**状态**: ✅ 已修复

---

## 🔍 问题诊断

### 症状
用户收到的实际响应：
```json
{
  "type": "delta",
  "content": "# 入职信息查询结果\n\n系统共查询到 **3 条员工入职记录**..."
}
```

**预期响应**应该是：
```json
{
  "type": "sources",
  "sources": [...]
}
{
  "type": "section",
  "section": {"type": "text", "markdown": "..."}
}
{
  "type": "section",
  "section": {"type": "list_ordered", "items": [...]}
}
{
  "type": "done",
  "confidence": 0.95
}
```

### 根本原因

虽然后端实现了完整的结构化流式 API：
- ✅ `/api/chat/structured` — 非流式结构化 API
- ✅ `/api/chat/structured/stream` — 流式结构化 API
- ✅ `AgentService.process_message_structured_stream()` 正确调用各服务的 `stream_with_structure()`

**但前端仍在调用旧的 API**：
```javascript
// frontend/src/services/api.ts:211
const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {  // ❌ 旧 API
```

前端的 `streamChatWithKnowledge()` 调用的是 `/api/chat/stream`，这会触发旧的处理流程：
```python
# backend/app/services/agent_service.py:94
yield {"type": "delta", "content": response.answer}  # ❌ 返回平面 Markdown
```

---

## ✅ 修复方案

### 修复 1: API 层 — 切换到结构化 API

**文件**: `frontend/src/services/api.ts:205-211`

```typescript
// 之前
const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {

// 之后  
const endpoint = useStructured ? '/api/chat/structured/stream' : '/api/chat/stream';
const response = await fetch(`${API_BASE_URL}${endpoint}`, {
  // 默认 useStructured=true，使用新 API
```

### 修复 2: 类型定义 — 添加 section 事件

**文件**: `frontend/src/services/api.ts:29-53`

```typescript
export type ChatStreamEvent =
  | { type: 'sources'; sources: SourceReference[]; ... }
  | { type: 'section';  // ✅ 新增
      section: {
        type: 'text' | 'list_ordered' | 'code_block' | 'table';
        markdown?: string;
        items?: any[];
        ...
      };
    }
  | { type: 'delta'; content: string; }
  | { type: 'done'; ... }
```

### 修复 3: Handler 接口 — 支持 section 处理

**文件**: `frontend/src/services/api.ts:55-59`

```typescript
export interface ChatStreamHandlers {
  onSources?: (event) => void;
  onSection?: (section: any) => void;  // ✅ 新增
  onDelta?: (content: string) => void;
  onDone?: (event) => void;
}
```

### 修复 4: 事件处理 — 区分 section 和 delta

**文件**: `frontend/src/services/api.ts:260-265`

```typescript
// 处理结构化 API 的 section 事件
if (event.type === 'section') {
  const section = event.section;
  if (section) {
    sections.push(section);
    handlers.onSection?.(section);  // ✅ 调用新 handler
  }
  return;
}
```

### 修复 5: ChatPanel — 处理结构化 sections

**文件**: `frontend/src/components/AGUI/ChatPanel.tsx:259-261`

```typescript
const response = await streamChatWithKnowledge(question, sessionId, 5, {
  onSources: event => { ... },
  onSection: section => {
    // ✅ 处理结构化 section：作为独立 JSON 对象发送
    const sectionJson = JSON.stringify(section);
    appendAssistantDelta(assistantMessageId, sectionJson);
  },
  onDelta: content => { ... },
```

### 修复 6: 格式检测 — 识别 section 对象

**文件**: `frontend/src/components/AGUI/ChatPanel.tsx:26-56`

```typescript
function detectContentFormat(content: string) {
  if (content.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(content);
      
      // ✅ 识别完整的结构化格式
      if ('sections' in parsed && Array.isArray(parsed.sections)) {
        return 'structured';
      }
      
      // ✅ 识别单个 section 对象
      if ('type' in parsed) {
        const type = parsed.type;
        if (['text', 'list_ordered', 'list_unordered', 'code_block', 'table'].includes(type)) {
          return 'structured';
        }
      }
      
      return 'json';
    } catch {}
  }
  // ... 其他检测
}
```

### 修复 7: StructuredRenderer — 支持单个 section

**文件**: `frontend/src/components/ContentRenderer/StructuredRenderer.tsx:53-70`

```typescript
const data = useMemo(() => {
  try {
    const parsed = JSON.parse(content);

    // ✅ 如果已有 sections 字段，直接返回
    if (parsed && 'sections' in parsed && Array.isArray(parsed.sections)) {
      return parsed as StructuredContent;
    }

    // ✅ 如果是单个 section 对象，包装为 StructuredContent
    if (parsed && 'type' in parsed) {
      return {
        sections: [parsed as Section],
      } as StructuredContent;
    }

    return { sections: [] };
  } catch (e) {
    return { sections: [] };
  }
}, [content]);
```

---

## 🔄 修复后的流程

```
用户提问
  ↓
ChatPanel.handleSendMessage()
  ↓
streamChatWithKnowledge(question, ..., { useStructured: true })  // ✅ 调用新 API
  ↓
fetch('/api/chat/structured/stream')  // ✅ 新的结构化流式 API
  ↓
后端 Agent Service
  ↓
SQL Service.stream_with_structure()  // ✅ 返回结构化 sections
  ↓
前端接收到：
  - sources 事件 → 显示数据来源
  - section 事件* → 逐块 JSON 对象
  - done 事件 → 流完成
  ↓
onSection handler
  ↓
convertToJSON → appendAssistantDelta
  ↓
detectContentFormat 识别为 'structured'
  ↓
StructuredRenderer 渲染单个 section
  ↓
用户界面显示结构化内容
```

---

## 📊 对比表

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| API 调用 | `/api/chat/stream` (旧) | `/api/chat/structured/stream` (新) |
| 返回事件 | `sources` → `delta` → `done` | `sources` → `section`* → `done` |
| Delta 内容 | 完整 Markdown | 单个 JSON 对象 |
| 前端处理 | 一坨文本累积 | Section 逐块结构化 |
| 渲染类型 | MarkdownRenderer | StructuredRenderer |
| 内容格式 | 平面 Markdown | 结构化 sections |

---

## 🧪 验证步骤

### 1. 检查 API 层实现

```bash
cd frontend
grep -n "useStructured" src/services/api.ts | head -5
# 预期：看到 useStructured 参数的定义和使用
```

### 2. 测试 API 调用

```bash
# 启动后端
cd backend && source venv/bin/activate && python run.py

# 启动前端  
cd frontend && pnpm dev

# 访问 http://localhost:3001 并在 ChatPanel 提问
# 打开浏览器 DevTools 的 Network 标签，观察请求

# 预期：
# - 请求 URL: http://localhost:8000/api/chat/structured/stream ✅
# - 响应内容: NDJSON 格式，包含 sources、section、done 事件 ✅
```

### 3. 检查前端日志

```javascript
// 在 DevTools Console 中运行
// 观察 ChatPanel 是否接收到 onSection 回调
console.log = (...args) => console.log('[APP]', ...args);
// 然后提问，观察日志输出
```

---

## 🚀 改进点

| 改进 | 效果 |
|------|------|
| 结构化 API | 后端保证输出结构，前端精确渲染 |
| Section 逐块返回 | 实时渲染，用户体验更好 |
| 自动格式检测 | 灵活处理多种内容类型 |
| 向后兼容 | 旧 API 保留，可通过参数降级 |

---

## 📝 核心改变

**之前**: 前端 → `/api/chat/stream` → 后端 → `delta` Markdown → MarkdownRenderer → 平面文本  
**之后**: 前端 → `/api/chat/structured/stream` → 后端 → `section` JSON → StructuredRenderer → 结构化渲染

---

## 🔗 相关代码

**Commit**: `9fe41e6`

```
fix: enable structured output API in frontend

3 files changed:
- frontend/src/services/api.ts
- frontend/src/components/AGUI/ChatPanel.tsx  
- frontend/src/components/ContentRenderer/StructuredRenderer.tsx
```

---

**✅ 修复完成 — 前后端现已完全集成！**

