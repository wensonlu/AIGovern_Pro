# ADR-0001: 自动内容格式检测方案

**日期**: 2026-04-24  
**状态**: 已实施  
**提交**: ab5bbbd - refactor: remove format event from backend, implement auto-detection in frontend

## 问题背景

### 原始设计问题
**后端在流式响应前**通过 `format` 事件预先声明内容格式：
```python
# backend/app/services/agent_service.py (旧方案)
content_type = self._determine_content_type(intent)  # 基于意图推断
yield {"type": "format", "content_type": content_type}  # 前置声明格式
```

### 暴露的问题
1. **推断准确度低**：同一意图的响应可能包含多种格式
   - `knowledge_qa` 可能返回 markdown 表格、JSON 数据、纯文本的混合
   - `business_diagnosis` 返回格式由 LLM 动态决定，不仅限 markdown

2. **无法支持混合格式**：一个响应中包含多种内容类型时无法处理
   - 例：markdown 文本 + JSON 代码块 + 表格

3. **后端职责不清**：不应该由后端猜测前端需要什么格式

## 解决方案

### 设计原则
**转变思路：从"声明式"到"检测式"**
- ✅ 后端：只负责返回内容本身，无需格式声明
- ✅ 前端：根据实际内容动态检测并选择合适的渲染器

### 实现细节

#### 1. 后端改动（删除元数据）
```python
# 删除三处 format 事件
- yield {"type": "format", "content_type": content_type}

# 删除辅助方法
- def _determine_content_type(self, intent: str) -> Literal[...]
```

#### 2. 前端自动检测函数
```typescript
// frontend/src/components/AGUI/ChatPanel.tsx
function detectContentFormat(content: string): 'text' | 'markdown' | 'html' | 'json' {
  // 1. 检测 JSON （最严格）
  if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
    try {
      JSON.parse(content);
      return 'json';
    } catch {}
  }

  // 2. 检测 HTML
  if (content.includes('<') && content.includes('>')) {
    return 'html';
  }

  // 3. 检测 Markdown（特征扫描）
  if (content.includes('#') || content.includes('**') || 
      content.includes('- ') || content.includes('```')) {
    return 'markdown';
  }

  // 4. 默认纯文本
  return 'text';
}
```

#### 3. 消息追加时动态更新格式
```typescript
const appendAssistantDelta = useCallback((assistantId: string, content: string) => {
  updateAssistantMessage(assistantId, msg => {
    const newContent = msg.content === '正在检索知识库...' 
      ? content 
      : `${msg.content}${content}`;
    
    // 关键：每次追加内容都重新检测格式
    const newContentType = msg.content_type || detectContentFormat(newContent);
    
    return {
      ...msg,
      content: newContent,
      content_type: newContentType,  // 动态更新
    };
  });
}, [updateAssistantMessage]);
```

## 权衡分析

| 维度 | 旧方案（后端声明） | 新方案（前端检测） |
|------|------------------|-----------------|
| 后端复杂度 | 高 | 低 ✅ |
| 前端复杂度 | 低 | 中 |
| 格式支持 | 单一格式 | 混合格式 ✅ |
| 准确度 | 基于意图推断（易失误） | 基于实际内容（准确） ✅ |
| 响应延迟 | 有（需前置事件） | 无 ✅ |
| 流式支持 | 支持 | 支持（每块增量检测） ✅ |

## 实现成果

✅ **删除代码**：后端减少 ~15 行（`_determine_content_type` 方法和 3 处 yield）  
✅ **添加代码**：前端增加 ~25 行（检测函数 + 增量更新逻辑）  
✅ **支持混合格式**：同一响应可动态切换渲染器  
✅ **更低耦合**：前后端职责清晰分离  

## 验证方式

1. **单一格式测试**
   - ✅ JSON 响应 → 自动识别为 `json` 格式
   - ✅ Markdown 表格 → 自动识别为 `markdown` 格式

2. **混合格式测试**
   - ✅ Markdown + JSON 代码块 → 按 Markdown 渲染，代码块内 JSON 高亮
   - ✅ 纯文本 + HTML → 自动切换至 HTML 渲染

3. **流式响应测试**
   - ✅ 逐块接收响应时，格式检测实时更新
   - ✅ 无"格式闪烁"或渲染器切换延迟

## 后续演进

该方案为后续的 **StructuredRenderer** 铺路：
- 当前：基于格式特征的简单检测
- v2：支持 JSON Schema 验证和嵌套结构渲染（见 `StructuredRenderer.tsx`）
- v3：可考虑前端语义检测或 LLM 辅助分类

## 与结构化输出框架的关联

### 演进关系

```
ADR-0001（格式检测）
    ↓
ADR-0002（格式规范化方案对比）
    ↓
TECH_SPEC_STRUCTURED_OUTPUT（完整实施框架）
    ├─ 细化格式检测：优先识别 JSON sections
    ├─ 扩展 Prompt 工程：引导生成结构化 JSON
    └─ 多模型支持：服务级别的流式结构化API
```

### 核心改进

- **ADR-0001**：基础格式检测（text/markdown/json/html）
- **结构化框架**：进阶检测（JSON schema validation）+ 多 section 类型支持

前端集成流程：
```typescript
// 1️⃣ 优先检测结构化格式（新增）
if (content.type === "section") {
  return <StructuredRenderer section={content} />;
}

// 2️⃣ 降级到基础格式检测（原有）
const format = detectContentFormat(content);
return renderers[format] ? <renderers[format] /> : <TextRenderer />;
```

## 相关代码位置

- 后端改动：`backend/app/services/agent_service.py:60-85`
- 前端实现：`frontend/src/components/AGUI/ChatPanel.tsx:25-50`（检测函数）、`184-194`（增量更新）
- 渲染器注册：`frontend/src/components/ContentRenderer/registry.ts`（使用 `content_type`）
- 结构化检测：`frontend/src/components/ContentRenderer/StructuredRenderer.tsx`（新增）
- 技术规范：`docs/architecture/TECH_SPEC_STRUCTURED_OUTPUT.md`（完整框架）
