# ADR-0002: 内容格式规范化方案对比

**日期**: 2026-04-27  
**状态**: 研究档案  
**背景**: 多格式内容渲染系统(2026-04-23)的设计决策回顾

## 问题背景

在实施多格式内容渲染时，面临两个核心方案选择：

**方案 1：Markdown + 后端规范化**（豆包/字节做法）  
**方案 2：Markdown + Prompt 工程**（ChatGPT 官方建议）

## 方案 1: Markdown + 后端规范化

### 定义
后端在生成内容时，强制输出为**格式规范化的 Markdown**。前端只负责渲染 Markdown，无需处理多种格式。

### 核心机制
```
用户问题
  ↓
LLM 生成响应
  ↓
后端 Markdown 规范化层
  ├─ 检测原始格式（纯文本、Markdown、JSON、HTML）
  ├─ 转换为统一 Markdown 格式
  ├─ 修复 Markdown 语法错误
  └─ 标准化列表、表格、代码块等
  ↓
发送规范化 Markdown 给前端
  ↓
前端 MarkdownRenderer 渲染
```

### 实现特征

#### 后端职责（重）
```python
class ContentNormalizer:
    """规范化各种格式为标准 Markdown"""
    
    def normalize(self, content: str, detected_format: str) -> str:
        if detected_format == 'json':
            return self.json_to_markdown(content)  # JSON 表格化
        elif detected_format == 'html':
            return self.html_to_markdown(content)  # HTML 转 Markdown
        elif detected_format == 'text':
            return self.text_to_markdown(content)  # 纯文本结构化
        else:
            return self.fix_markdown(content)      # 修复 Markdown 语法
    
    def fix_markdown(self, md: str) -> str:
        """修复常见 LLM 生成的 Markdown 问题"""
        # 1. 修复缺失的空行
        # 2. 标准化表格格式
        # 3. 修复代码块围栏
        # 4. 统一列表缩进
        # 5. 规范链接格式
        pass
```

#### 前端职责（轻）
```typescript
// 前端只需一个 MarkdownRenderer
function renderMessage(msg: Message) {
  return <MarkdownRenderer content={msg.content} />;
}
```

### 优点 ✅

| 优点 | 说明 |
|-----|------|
| **前端极简** | 只需一个 MarkdownRenderer，无复杂路由逻辑 |
| **渲染性能** | 统一格式，浏览器优化空间大 |
| **SEO友好** | Markdown 文本友好，便于搜索和索引 |
| **用户体验** | 格式一致，用户学习成本低 |
| **降级方案清晰** | 格式错误时直接显示 Markdown 源码即可 |
| **适合长期维护** | 后端规范化是"一次性投资" |

### 缺点 ❌

| 缺点 | 影响 |
|-----|------|
| **后端复杂度高** | 需要实现多种格式转换器（json→md、html→md等） |
| **信息损失风险** | JSON 结构复杂度可能被简化（如深层嵌套） |
| **LLM 契合度差** | LLM 本身倾向生成不同格式，强制转换效果不佳 |
| **维护成本高** | 新格式、新规则都需后端修改发布 |
| **响应延迟** | 后端需处理文本转换，增加延迟 |

### 应用场景

✅ **豆包 (字节)**
- 2024 年全面推行 Markdown 规范化
- 后端强制输出统一 Markdown
- 前端仅用 react-markdown 渲染
- 结果：产品风格统一，用户体验稳定

✅ **适用于 AIGovern Pro 的情况**
- 企业场景（格式需要可控、可审计）
- 导出需求强（Markdown 导出最便宜）
- 长期维护团队充足

---

## 方案 2: Markdown + Prompt 工程

### 定义
通过精细的 Prompt 工程，引导 LLM **倾向生成 Markdown 格式**。后端接收任何格式都不转换，前端动态检测渲染。

### 核心机制
```
用户问题 + Markdown Prompt
  ↓
LLM 生成（优先 Markdown）
  ↓
后端流式转发（无处理）
  ↓
前端 detectContentFormat()
  ├─ 尝试 JSON.parse()
  ├─ 检查 HTML 标签
  ├─ 扫描 Markdown 特征 (#, **, ```)
  └─ 默认文本
  ↓
根据检测结果选择渲染器
```

### 实现特征

#### 后端职责（极轻）
```python
# 后端只做流转，无格式处理
@app.post("/api/chat/stream")
async def stream_chat(query: str):
    for token in llm_stream(query):
        yield {"type": "delta", "content": token}
```

#### 前端职责（中等）
```typescript
// 前端自动检测
function detectContentFormat(content: string) {
  if (isValidJSON(content)) return 'json';
  if (isHTML(content)) return 'html';
  if (isMarkdown(content)) return 'markdown';
  return 'text';
}

// 支持多个渲染器
const renderers = {
  markdown: MarkdownRenderer,
  json: JsonRenderer,
  html: HtmlRenderer,
  text: TextRenderer,
};
```

#### Prompt 工程
```markdown
系统提示词增强（System Prompt）：

"请优先使用 Markdown 格式输出：
  
## 列表用 - 或 * 开头
## 代码用 ``` 包裹
## 强调用 **bold** 或 *italic*
## 表格用 | 分列

如果输出 JSON 数据，请用 \`\`\`json 代码块包裹。
如果输出结构化数据，优先用 Markdown 表格而非原始 JSON。"
```

### 优点 ✅

| 优点 | 说明 |
|-----|------|
| **后端极简** | 无格式处理逻辑，纯流转 |
| **LLM 友好** | 顺应 LLM 自然倾向，无强制转换 |
| **灵活扩展** | 新格式只需新 Prompt + 新 Renderer，无后端发布 |
| **响应速度** | 后端零处理，最小延迟 |
| **支持动态内容** | LLM 可根据内容自主选择最佳格式 |
| **适合多模型** | Prompt 可跨多个 LLM 使用 |

### 缺点 ❌

| 缺点 | 影响 |
|-----|------|
| **前端复杂度** | 需实现多个 Renderer + 检测逻辑 |
| **格式不一致** | LLM 输出风格可能变化，用户体验波动 |
| **Prompt 脆弱性** | LLM 更新可能导致输出格式变化 |
| **渲染器维护** | 多个 Renderer 意味着多个潜在 bug |
| **降级成本** | 未知格式需要回退处理 |
| **导出复杂** | 导出时需把多种格式转为统一格式 |

### 应用场景

✅ **ChatGPT 官方建议**
- OpenAI 提供的 Prompt 工程指南
- 充分利用 GPT 的 Markdown 能力
- 结果：灵活、快速迭代

✅ **Claude 的做法**
- Anthropic 建议前端检测 + Prompt 引导
- 官方 Claude App 使用此方案
- 支持富文本、代码片段、表格等自动选择

✅ **适用于 AIGovern Pro 的情况**
- 多模型支持（Deepseek、通义等）
- 快速迭代，Prompt 调整快于后端发布
- 前端研发能力强

---

## 对比矩阵

| 维度 | 方案 1（后端规范化） | 方案 2（Prompt工程） |
|-----|------------------|------------------|
| **后端复杂度** | 🔴 高 | 🟢 极低 |
| **前端复杂度** | 🟢 低 | 🟠 中 |
| **实施成本** | 中（需后端改造） | 低（主要前端） |
| **维护成本** | 中-高 | 低 |
| **响应延迟** | 🔴 较高（+格式转换） | 🟢 最低 |
| **格式一致性** | 🟢 极高 | 🟠 中等 |
| **用户体验** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **扩展性** | 🔴 后端发布周期 | 🟢 Prompt 即时 |
| **多模型支持** | 🔴 每个模型需适配 | 🟢 Prompt 通用 |
| **导出复杂性** | 🟢 简单 | 🟠 较复杂 |

## AIGovern Pro 现状评估

### 当前采取的方案

我们在 **2026-04-24 commit (ab5bbbd)** 中实施的是：

**混合方案：后端 0 处理 + 前端自动检测**

```typescript
// 前端实现的 detectContentFormat()
function detectContentFormat(content: string) {
  // 检测 JSON
  if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
    try { JSON.parse(content); return 'json'; } catch {}
  }
  // 检测 HTML
  if (content.includes('<') && content.includes('>')) return 'html';
  // 检测 Markdown
  if (content.includes('#') || content.includes('**') || 
      content.includes('- ') || content.includes('```')) return 'markdown';
  return 'text';
}
```

**这实际上是方案 2 的简化版实现**：
- ✅ 后端极简（无处理）
- ✅ 前端自动检测
- ❌ 缺少 Prompt 工程层（未优化 LLM 输出倾向）

### 改进建议

#### 短期（<1 周）
增加 Prompt 工程：

```python
# backend/app/services/agent_service.py
SYSTEM_PROMPT = """
你是企业 AI 助手。回答问题时：

1. **优先使用 Markdown 格式**
   - 列表用 - 或 * 
   - 代码用 ```language
   - 表格用 | 分列
   
2. **结构化数据**
   - JSON 数据用 ```json 代码块
   - 复杂对象优先用 Markdown 表格

3. **代码片段**
   - 必须指定语言：```python、```sql、```javascript

这样前端可自动检测和正确渲染。
"""
```

#### 中期（1-2 周）
可选升级至方案 1（如需极高格式稳定性）：

```python
# backend/app/services/content_normalizer.py
class ContentNormalizer:
    def normalize_to_markdown(self, content: str) -> str:
        """统一输出为 Markdown"""
        # 1. JSON to Markdown table
        # 2. HTML to Markdown
        # 3. Fix Markdown syntax errors
        pass
```

## 决策建议

| 选项 | 推荐指数 | 条件 |
|-----|--------|------|
| **保持现状**（简化方案 2） | ⭐⭐⭐⭐ | 加强 Prompt 工程即可 |
| **升级至完整方案 2** | ⭐⭐⭐⭐⭐ | 追求灵活性 + 多模型支持 |
| **迁移至方案 1** | ⭐⭐ | 仅在企业需要极高控制时 |

### 对 AIGovern Pro 的建议

**优先完整方案 2（Markdown + Prompt工程）** 原因：

1. **商业前景**：多客户可能要求集成不同 LLM（Claude、Deepseek、通义等）
2. **快速迭代**：企业管理系统需要快速反应市场需求
3. **成本效益**：前端投入已完成（StructuredRenderer），后端只需 Prompt 调整
4. **未来扩展**：当需要 Markdown → 专业格式（PDF、RTF）时，统一的 Markdown 中间格式是最优选择

---

## 参考资源

**方案 1 案例研究**：
- [字节豆包官方文档](https://www.doubao.com) - 内容规范化
- 企业级 LLM 应用最佳实践

**方案 2 案例研究**：
- [OpenAI Prompt Engineering Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Claude Docs - Prompt Tips](https://docs.anthropic.com/en/docs/build-a-claude-app)

**相关 ADR**：
- ADR-0001: 自动内容格式检测 (当前实施的方案基础)

---

**档案完成**：2026-04-27  
**相关代码**：`frontend/src/components/ContentRenderer/` + `backend/app/services/agent_service.py`
