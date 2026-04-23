# 多格式内容渲染系统设计

**日期**: 2026-04-23  
**状态**: 已批准  
**作者**: Claude  

## 概述

当前 ChatPanel 仅支持纯文本渲染。本设计扩展系统以兼容 AI 接口返回的多种格式内容（Markdown、HTML、JSON、纯文本），采用**格式注册器模式**实现高度可扩展的渲染架构。

## 需求

- 支持 4 种格式：纯文本、Markdown、HTML、JSON
- 后端通过 `content_type` 字段显式声明格式
- 信任后端的内容过滤，前端不做额外 sanitize
- 未来可便捷添加新格式（如 LaTeX、Mermaid 图表）
- ChatPanel 改动最小化，保持现有流式传输逻辑不变

## 架构设计

### 1. 消息数据结构

扩展 `Message` interface，添加 `content_type` 顶层字段：

```typescript
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  content_type: 'text' | 'markdown' | 'html' | 'json';  // 新增字段，默认 'text'
  timestamp: Date;
  sources?: SourceReference[];
  confidence?: number;
}
```

**设计决策**：
- 将 `content_type` 放在顶层而非 metadata 中，因为它是消息内容的核心属性
- 提供默认值 `'text'`，确保向后兼容性

### 2. 格式注册器模式

**位置**: `frontend/src/components/ContentRenderer/`

创建注册器工厂函数，根据 `content_type` 动态返回对应的渲染器组件：

```typescript
// registry.ts
import TextRenderer from './TextRenderer';
import MarkdownRenderer from './MarkdownRenderer';
import HtmlRenderer from './HtmlRenderer';
import JsonRenderer from './JsonRenderer';

const renderers = {
  text: TextRenderer,
  markdown: MarkdownRenderer,
  html: HtmlRenderer,
  json: JsonRenderer,
};

export const getContentRenderer = (contentType?: string) => {
  return renderers[contentType || 'text'] || renderers.text;
};

export type ContentType = keyof typeof renderers;
```

**扩展机制**：新增格式时只需：
1. 创建新的 Renderer 组件
2. 在 renderers 对象中注册
3. 更新 ContentType 类型

### 3. 各格式渲染器

#### TextRenderer
- 现有逻辑，纯 `<p>` 标签
- 支持基础换行

#### MarkdownRenderer
- 使用 `react-markdown` 库
- 支持：标题、列表、代码块、表格、链接、强调等
- 依赖：`npm install react-markdown`

#### HtmlRenderer
- 直接渲染 HTML 内容
- 信任后端已过滤危险内容
- 若后续需要 sanitize，可添加 DOMPurify

#### JsonRenderer
- 结构化数据展示
- 树形或表格形式
- 支持折叠/展开交互

### 4. 后端流式事件扩展

在现有 `delta/sources/done` 事件基础上，增加 `format` 事件：

```json
{ "type": "format", "content_type": "markdown" }
{ "type": "delta", "content": "# 标题\n" }
{ "type": "delta", "content": "正文内容" }
{ "type": "sources", "sources": [...] }
{ "type": "done", "confidence": 0.95 }
```

**流程**：
1. 首次发送 `format` event，前端设置消息的 `content_type`
2. 后续 `delta` 正常追加内容
3. `done` 事件确认完成

### 5. ChatPanel 集成

修改 `MessageRow` 组件，使用注册器动态选择渲染器：

```typescript
// MessageRow.tsx
const MessageRow = memo<{ message: Message; onCopy: (text: string) => void }>(
  ({ message: msg, onCopy }) => {
    const ContentComponent = getContentRenderer(msg.content_type);

    return (
      <div className={`${styles.message} ${styles[msg.type]}`}>
        {msg.type === 'assistant' && <div className={styles.avatar}>🤖</div>}

        <div className={styles.messageContent}>
          {/* 动态渲染内容 */}
          <ContentComponent content={msg.content} />

          {/* 时间戳、置信度、信息来源保持不变 */}
          <p className={styles.timestamp}>{msg.timestamp.toLocaleTimeString()}</p>
          {msg.confidence && <ConfidenceIndicator {...} />}
          {msg.sources && msg.sources.length > 0 && <SourcesList {...} />}

          {/* 操作按钮 */}
          {msg.type === 'assistant' && <MessageActions {...} />}
        </div>

        {msg.type === 'user' && <div className={styles.avatar}>👤</div>}
      </div>
    );
  }
);
```

**改动最小化**：只替换内容渲染部分，保留所有现有功能（置信度、信息来源、操作按钮）。

## 文件结构

```
frontend/src/components/
├── ContentRenderer/
│   ├── index.ts                    # 导出 getContentRenderer
│   ├── registry.ts                 # 注册器工厂
│   ├── types.ts                    # ContentType 类型定义
│   ├── TextRenderer.tsx            # 纯文本渲染
│   ├── MarkdownRenderer.tsx        # Markdown 渲染
│   ├── HtmlRenderer.tsx            # HTML 渲染
│   └── JsonRenderer.tsx            # JSON 渲染
├── AGUI/
│   └── ChatPanel.tsx               # 改动：MessageRow 集成 ContentRenderer
```

## 数据流

```
后端流式事件
    ↓
streamChatWithKnowledge 解析事件
    ↓
format event → 设置 message.content_type
delta event → 追加 message.content
done event → 最终化消息
    ↓
ChatPanel 重新渲染
    ↓
MessageRow 获取 content_type
    ↓
getContentRenderer(content_type) 返回组件
    ↓
组件渲染内容
```

## 依赖

| 库 | 用途 | 版本 |
| --- | --- | --- |
| `react-markdown` | Markdown 渲染 | ^9.0+ |
| `remark-gfm` | GitHub Flavored Markdown 扩展 | ^4.0+ |

可选（后续需要）：
- `dompurify` — HTML sanitize
- `react-json-tree` — JSON 树形展示

## 兼容性

- **向后兼容**：未指定 `content_type` 的消息默认为 `'text'`
- **迁移路径**：现有消息保持 text 格式，新接口逐步采用其他格式

## 测试策略

1. **单元测试**
   - 各 Renderer 独立测试，验证正确渲染
   - registry 返回正确的组件

2. **集成测试**
   - ChatPanel 接收不同格式的消息，验证正确渲染
   - 流式事件处理（format → delta → done）

3. **端到端测试**
   - 后端返回各种格式内容
   - 前端正确显示和交互

## 未来扩展

添加新格式（如 LaTeX、Mermaid）的步骤：

1. 创建 `LatexRenderer.tsx` 或 `MermaidRenderer.tsx`
2. 在 `registry.ts` 中注册
3. 后端添加 `content_type: 'latex'` 支持
4. 测试通过即可

无需改动 ChatPanel 或其他现有组件。

## 风险与缓解

| 风险 | 影响 | 缓解方案 |
| --- | --- | --- |
| 新 library 增加包体积 | 性能 | 按需加载 renderer（lazy import） |
| HTML 内容包含恶意脚本 | 安全 | 信任后端过滤；若需要，使用 DOMPurify |
| 格式错误的内容 | UX | 降级到 TextRenderer，显示原始内容 |

## 成功标准

- ✅ 4 种格式渲染正常
- ✅ ChatPanel 集成无破坏
- ✅ 流式传输逻辑不变
- ✅ 新格式添加无需改动现有组件
- ✅ 单元测试 > 80% 覆盖率
- ✅ E2E 测试通过

---

**设计完成** — 等待用户审查后，可转入实现规划阶段。
