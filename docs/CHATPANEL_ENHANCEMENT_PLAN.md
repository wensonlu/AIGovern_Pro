# AGUI ChatPanel 增强计划

基于 AI 助手设计趋势研究，为 AIGovern Pro 的对话面板制定分阶段增强方案。

## 核心增强方向

### 🎯 阶段 1：交互基础（第 2.5 期）

#### 1.1 全局命令面板 (Cmd+K)

**目标**：快速打开对话、操作、设置

**实现**：
```typescript
// frontend/src/components/ChatPanel/CommandPalette.tsx
export const CommandPalette = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);
  
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <Input placeholder="Search conversations or commands..." />
      <CommandList>
        {/* 对话搜索结果 + 快速操作 */}
      </CommandList>
    </Dialog>
  );
};
```

**优先级**：🔴 P1 - 关键交互

---

#### 1.2 消息流式输出优化

**目标**：逐字显示，提升 UX

**当前问题**：可能存在一次性显示完整内容

**优化方案**：
```typescript
// 在 ChatMessage 组件中启用流式显示
const [displayContent, setDisplayContent] = useState('');
const [isStreaming, setIsStreaming] = useState(false);

// 流式更新逻辑
useEffect(() => {
  if (message.streaming && message.content) {
    const interval = setInterval(() => {
      setDisplayContent(prev => {
        if (prev.length < message.content.length) {
          return message.content.slice(0, prev.length + 1);
        }
        return prev;
      });
    }, 20); // 50 字符/秒
    
    return () => clearInterval(interval);
  }
}, [message.streaming, message.content]);
```

**优先级**：🔴 P1 - 核心体验

---

#### 1.3 消息操作浮层

**目标**：Hover 时显示快速操作

**实现**：
```typescript
// frontend/src/components/ChatPanel/MessageActions.tsx
export const MessageActions = ({ message, onCopy, onEdit, onDelete }: Props) => {
  return (
    <div className="message-actions" role="toolbar">
      <IconButton
        icon="copy"
        onClick={() => onCopy(message.content)}
        title="Copy (Cmd+C)"
      />
      <IconButton
        icon="edit"
        onClick={() => onEdit(message.id)}
        title="Edit (Cmd+E)"
      />
      {message.role === 'assistant' && (
        <IconButton
          icon="rotate"
          onClick={() => onRegenerate(message.id)}
          title="Regenerate (Cmd+R)"
        />
      )}
      <IconButton
        icon="trash"
        onClick={() => onDelete(message.id)}
        title="Delete"
      />
    </div>
  );
};
```

**优先级**：🔴 P1 - 核心交互

---

#### 1.4 来源溯源与相关度显示

**目标**：增强信息透明度和可信度

**设计**：
```
消息下方显示：
┌─────────────────────────────────┐
│ 📄 参考文档                      │
│ • sales_report_q1.pdf (相关度: 92%) │
│ • monthly_trend.xlsx (相关度: 87%)  │
└─────────────────────────────────┘

置信度指示器：
Confidence: ████████░ 85%
```

**实现**：
```typescript
<div className="message-metadata">
  {message.sources && (
    <div className="sources">
      <label>Sources</label>
      {message.sources.map(source => (
        <SourceTag
          key={source.id}
          name={source.name}
          relevance={source.relevance}
        />
      ))}
    </div>
  )}
  <div className="confidence">
    Confidence: {message.confidence}%
  </div>
</div>
```

**优先级**：🔴 P1 - 核心体验

---

### 🚀 阶段 2：功能增强（第 3 期）

#### 2.1 对话搜索与过滤

**优先级**：🟠 P2

```typescript
// 搜索功能
<SearchInput 
  placeholder="Search conversations..."
  debounce={300}
  onSearch={(query) => {
    const results = conversations.filter(conv =>
      conv.title.includes(query) || 
      conv.messages.some(msg => msg.content.includes(query))
    );
    setFilteredConversations(results);
  }}
/>
```

#### 2.2 多模态输入

**优先级**：🟠 P2

```typescript
// 支持图片、文件、语音输入
<MultimodalInput
  onImageUpload={(file) => uploadImage(file)}
  onFileUpload={(file) => uploadFile(file)}
  onVoiceInput={(transcript) => handleVoiceInput(transcript)}
/>
```

#### 2.3 对话导出

**优先级**：🟠 P2

```typescript
// 导出为 Markdown / PDF
const exportConversation = async (conversationId: string, format: 'md' | 'pdf') => {
  const response = await fetch(`/api/conversations/${conversationId}/export`, {
    method: 'POST',
    body: JSON.stringify({ format }),
  });
  // 下载文件
};
```

---

### 💫 阶段 3：高级功能（第 4 期）

#### 3.1 对话分享与权限

**优先级**：🟢 P3

- 生成分享链接
- 权限管理（Owner/Editor/Viewer）
- 分享统计

#### 3.2 语音输入

**优先级**：🟢 P3

- Cmd+M 快捷键启动
- 实时转录显示
- 支持多语言

#### 3.3 本地模型集成

**优先级**：🟢 P3

- Ollama 支持
- 离线模式
- 模型管理界面

---

## 技术实施清单

### 前端优化

- [ ] 集成 `hotkeys-js` 库处理全局快捷键
- [ ] 实现虚拟滚动（>1000 消息）
- [ ] 优化流式输出渲染性能
- [ ] 添加 IndexedDB 本地存储
- [ ] 完善错误边界和加载状态
- [ ] 深色主题完整支持

### 后端优化

- [ ] 实现 SSE 流式输出端点
- [ ] 添加消息搜索 API
- [ ] 实现对话导出功能
- [ ] 增加操作审计日志
- [ ] 优化数据库查询性能

### 产品需求

- [ ] 确定导出格式（Markdown/PDF）
- [ ] 设计分享权限模型
- [ ] 定义相关度评分算法
- [ ] 规划 Token 监控指标

---

## 时间表

| 阶段 | 范围 | 预计 | 状态 |
|------|------|------|------|
| 2.5 | P1 核心 | 2-3 周 | 待评估 |
| 3.0 | P2 功能 | 2-3 周 | 计划中 |
| 3.5 | P3 高级 | 3-4 周 | 计划中 |

---

## 参考文档

- `/docs/AI_ASSISTANT_DESIGN_TRENDS.md` - 完整设计趋势研究
- `frontend/QUICKSTART.md` - 前端开发指南
- `backend/QUICKSTART.md` - 后端开发指南

---

**更新时间**: 2026-03-31  
**维护者**: AI Research Assistant  
**状态**: 📋 计划阶段
