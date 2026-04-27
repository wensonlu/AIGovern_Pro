# 结构化输出与 Markdown 统一框架

**版本**: 1.0  
**最后更新**: 2026-04-27  
**状态**: ✅ 全服务已实现（RAG / SQL / 诊断 / 操作）

---

## 📋 Executive Summary

### 核心问题

后端四大服务（RAG、SQL 生成、诊断、操作执行）原本只支持平面 Markdown 输出，存在以下痛点：

- **格式不规范**：列表嵌套、代码块、间距处理不一致，前端需反复修复 CSS
- **前端维护成本高**：需要额外容错处理，逻辑繁琐且易碎
- **可扩展性差**：后续功能扩展无法复用结构化方案

### 解决方案

引入 **结构化输出框架**，后端通过 Pydantic 模型统一定义响应格式，支持多种 section 类型（文本、列表、代码块、表格等）。前端根据 section 类型精确渲染，无需容错。

**核心特性**：
- ✅ 4 个服务全覆盖：RAG、SQL、诊断、操作
- ✅ 流式交付：section 生成即返回，实时渲染
- ✅ Prompt 工程：通过精心设计的提示词引导 LLM 输出结构化 JSON
- ✅ 向后兼容：旧 API 保留，前端自动检测格式
- ✅ 降级方案：LLM 失败时返回 error 事件，前端可降级为 Markdown

### 收益

| 维度 | 收益 |
|------|------|
| **可靠性** | 后端保证输出结构，前端无需容错 |
| **用户体验** | 流式逐块显示，实时反馈 |
| **维护成本** | 渲染逻辑从"容错"转为"规范化"，易维护 |
| **扩展性** | 新增 section 类型只需定义模型，复用渲染器 |

---

## 🏗️ 架构概览

### 数据模型

#### Section 类型定义

```python
# backend/app/models/schemas.py

class SectionType(str, Enum):
    """所有支持的 section 类型"""
    TEXT = "text"
    LIST_ORDERED = "list_ordered"
    LIST_UNORDERED = "list_unordered"
    CODE_BLOCK = "code_block"
    TABLE = "table"

# 各 section 具体定义（详见实现细节）
class TextSection(BaseModel):
    type: Literal["text"]
    markdown: str  # 支持 Markdown 富文本

class ListOrderedSection(BaseModel):
    type: Literal["list_ordered"]
    items: list[OrderedListItem]  # 支持嵌套

class CodeBlockSection(BaseModel):
    type: Literal["code_block"]
    language: str
    code: str

class TableSection(BaseModel):
    type: Literal["table"]
    headers: list[str]
    rows: list[list[str]]

# 联合类型
Section = Union[TextSection, ListOrderedSection, ListUnorderedSection, CodeBlockSection, TableSection]
```

#### 完整响应格式

```python
class StructuredChatResponse(BaseModel):
    """非流式响应格式"""
    sections: list[Section]  # 所有 section
    sources: list[SourceReference]  # 数据来源（RAG 特定）
    confidence: float  # 置信度
    session_id: str
    timestamp: datetime
    intent: str  # "knowledge_qa" | "data_query" | "diagnosis" | "operations"
    workflow: list[WorkflowStep]  # 执行步骤日志

class StructuredStreamEvent(BaseModel):
    """流式事件"""
    type: str  # "sources" | "section" | "done" | "error"
    # 具体字段因 type 而异
```

### 流程图

```
用户查询
    ↓
[Agent Service] 识别意图
    ↓
┌─────────────────────────────────────┐
│ 根据意图路由到对应服务               │
├─────────────────────────────────────┤
│ RAG Service    → 知识问答             │
│ SQL Service    → 数据查询             │
│ Diagnosis Svc  → 业务诊断             │
│ Operations Svc → 操作执行             │
└─────────────────────────────────────┘
    ↓
[stream_with_structure()] 返回NDJSON事件
    ↓
┌─────────────────────┐
│ sources 事件        │  <- 数据源/初始化
├─────────────────────┤
│ section 事件        │  <- 逐块section
│ (可能多个)          │
├─────────────────────┤
│ done/error 事件     │  <- 完成或异常
└─────────────────────┘
    ↓
前端 NDJSON 解析器
    ↓
[StructuredRenderer] 逐块渲染
    ↓
用户界面显示
```

---

## 🔧 实现细节

### Phase 1: 数据模型（已完成）

**文件**: `backend/app/models/schemas.py`

#### 核心模型

```python
from enum import Enum
from typing import Union, Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class SectionType(str, Enum):
    TEXT = "text"
    LIST_ORDERED = "list_ordered"
    LIST_UNORDERED = "list_unordered"
    CODE_BLOCK = "code_block"
    TABLE = "table"

# ===== 文本 Section =====
class TextSection(BaseModel):
    type: Literal["text"]
    markdown: str  # 支持 Markdown 富文本（标题、加粗、链接等）

# ===== 列表 Section =====
class OrderedListItem(BaseModel):
    """有序列表项，支持嵌套"""
    title: str
    details_markdown: Optional[str] = None  # Markdown 详情
    subitems: Optional[list["OrderedListItem"]] = None  # 嵌套子项

class ListOrderedSection(BaseModel):
    type: Literal["list_ordered"]
    items: list[OrderedListItem]

class UnorderedListItem(BaseModel):
    """无序列表项"""
    text: str
    subitems: Optional[list["UnorderedListItem"]] = None

class ListUnorderedSection(BaseModel):
    type: Literal["list_unordered"]
    items: list[UnorderedListItem]

# ===== 代码块 Section =====
class CodeBlockSection(BaseModel):
    type: Literal["code_block"]
    language: str  # "python", "typescript", "sql", etc.
    code: str

# ===== 表格 Section =====
class TableSection(BaseModel):
    type: Literal["table"]
    headers: list[str]
    rows: list[list[str]]

# ===== 联合类型 =====
Section = Union[
    TextSection,
    ListOrderedSection,
    ListUnorderedSection,
    CodeBlockSection,
    TableSection,
]

# ===== 响应元数据 =====
class SourceReference(BaseModel):
    """数据来源（RAG 特定）"""
    document_id: int
    title: str
    filename: str
    chunk_index: int
    relevance: float

class WorkflowStep(BaseModel):
    """执行步骤"""
    step: int
    name: str
    status: str  # "completed" | "in_progress" | "failed"
    description: Optional[str] = None

# ===== 完整响应 =====
class StructuredChatResponse(BaseModel):
    """非流式完整响应"""
    sections: list[Section]
    sources: Optional[list[SourceReference]] = None
    confidence: float
    session_id: str
    timestamp: datetime
    intent: str  # "knowledge_qa" | "data_query" | "diagnosis" | "operations"
    workflow: list[WorkflowStep]

# ===== 流式事件 =====
class StructuredStreamEvent(BaseModel):
    """NDJSON 流式事件"""
    type: str  # "sources" | "section" | "done" | "error"
```

**特性**：
- ✅ 完整支持 5 种 section 类型
- ✅ 列表支持嵌套（subitems）
- ✅ Markdown 子内容支持富文本格式
- ✅ 元数据（sources、workflow）完整保留

---

### Phase 2: 服务层改造（已完成）

**文件**: 
- `backend/app/services/rag_service.py` → `stream_with_structure()`
- `backend/app/services/sql_service.py` → `stream_with_structure()`
- `backend/app/services/diagnosis_service.py` → `stream_with_structure()`
- `backend/app/services/operations_service.py` → `stream_with_structure()`

#### RAG 服务示例

```python
# backend/app/services/rag_service.py

async def stream_with_structure(
    self,
    question: str,
    top_k: int = 5,
    **kwargs
) -> AsyncIterator[dict]:
    """
    流式返回结构化知识问答
    
    事件序列:
    1. sources 事件：返回检索到的文档列表
    2. section* 事件：逐块返回内容 section
    3. done/error 事件：完成或异常
    """
    # 1️⃣ 检索文档
    sources = await self._retrieve_documents(question, top_k)
    confidence_score = sum(s.relevance for s in sources) / len(sources) if sources else 0.0
    
    # 2️⃣ 返回 sources 事件
    yield {
        "type": "sources",
        "sources": [s.model_dump() for s in sources],
        "confidence": confidence_score,
    }
    
    # 3️⃣ 构建结构化 Prompt
    context = "\n".join([s.text_preview for s in sources])
    prompt = self._build_structured_prompt(question, context)
    
    # 4️⃣ 流式调用 LLM，逐块积累内容
    accumulated_content = ""
    sections_emitted = set()
    
    async for chunk in self.llm_client.stream_text(prompt):
        accumulated_content += chunk
        
        # 5️⃣ 实时解析，生成 section 即返回
        new_sections = self._parse_to_structured(accumulated_content)
        for i, section in enumerate(new_sections):
            if i not in sections_emitted:
                yield {
                    "type": "section",
                    "section": section.model_dump(),
                }
                sections_emitted.add(i)
    
    # 6️⃣ 返回完成事件
    yield {
        "type": "done",
        "confidence": confidence_score,
    }

def _build_structured_prompt(self, question: str, context: str) -> str:
    """
    构建引导 LLM 输出结构化 JSON 的 Prompt
    关键：清晰指定输出格式
    """
    return f"""
你是一个知识库助手。基于以下文档内容回答用户问题。

【用户问题】
{question}

【相关文档】
{context}

【回答要求】
请将你的回答组织为以下 JSON 格式的 sections 数组，每个 section 代表一个逻辑块：

```json
{{
  "sections": [
    {{
      "type": "text",
      "markdown": "## 标题\\n段落说明..."
    }},
    {{
      "type": "list_ordered",
      "items": [
        {{
          "title": "项目1",
          "details_markdown": "- 子项1\\n- 子项2"
        }}
      ]
    }},
    {{
      "type": "code_block",
      "language": "python",
      "code": "def example():\\n    pass"
    }}
  ]
}}
```

支持的 section 类型: text, list_ordered, list_unordered, code_block, table

【重要】
- 每个 section 必须是完整的 JSON 对象
- 使用正确的类型标注
- Markdown 内容中的双引号需转义为 \\"
"""

def _parse_to_structured(self, accumulated_content: str) -> list[Section]:
    """
    从 LLM 流式输出中解析 section
    处理部分 JSON、格式纠正等
    """
    # 提取 JSON 代码块
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', accumulated_content, re.DOTALL)
    if not json_match:
        return []
    
    try:
        data = json.loads(json_match.group(1))
        sections = []
        for item in data.get("sections", []):
            section_type = item.get("type")
            
            if section_type == "text":
                sections.append(TextSection(**item))
            elif section_type == "list_ordered":
                sections.append(ListOrderedSection(**item))
            elif section_type == "code_block":
                sections.append(CodeBlockSection(**item))
            # ... 其他类型
        return sections
    except json.JSONDecodeError:
        return []
```

#### 其他服务（SQL / 诊断 / 操作）

**相同模式**：
1. 检索/准备数据 → sources 事件
2. 构建结构化 Prompt
3. 流式调用 LLM → section 逐块返回
4. 返回 done/error 事件

**差异**：
- SQL：sources = 查询执行结果、表结构信息
- 诊断：sources = 系统指标、历史数据
- 操作：sources = 操作步骤、执行日志

---

### Phase 3: 前端集成（已完成）

#### StructuredRenderer 组件

**文件**: `frontend/src/components/ContentRenderer/StructuredRenderer.tsx`

```typescript
import React from "react";
import { Section } from "@/types/api";
import { MarkdownRenderer } from "./MarkdownRenderer";
import "./StructuredRenderer.css";

export const StructuredRenderer: React.FC<{ sections: Section[] }> = ({ sections }) => {
  return (
    <div className="structured-renderer">
      {sections.map((section, idx) => (
        <div key={idx} className={`section section-${section.type}`}>
          {section.type === "text" && (
            <MarkdownRenderer markdown={section.markdown} />
          )}
          
          {section.type === "list_ordered" && (
            <ol className="ordered-list">
              {section.items.map((item, i) => (
                <ListItemRenderer key={i} item={item} ordered />
              ))}
            </ol>
          )}
          
          {section.type === "code_block" && (
            <pre className={`code-${section.language}`}>
              <code>{section.code}</code>
            </pre>
          )}
          
          {section.type === "table" && (
            <table className="data-table">
              <thead>
                <tr>
                  {section.headers.map((h, i) => <th key={i}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {section.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => <td key={j}>{cell}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
};

// 递归列表项渲染（支持嵌套）
const ListItemRenderer: React.FC<{ item: any; ordered?: boolean }> = ({ item, ordered }) => {
  return (
    <li>
      <strong>{item.title}</strong>
      {item.details_markdown && (
        <MarkdownRenderer markdown={item.details_markdown} />
      )}
      {item.subitems && (
        <ol style={{ marginLeft: "20px" }}>
          {item.subitems.map((subitem, i) => (
            <ListItemRenderer key={i} item={subitem} ordered={ordered} />
          ))}
        </ol>
      )}
    </li>
  );
};
```

#### 格式自动检测

**文件**: `frontend/src/components/AGUI/ChatPanel.tsx`

```typescript
// 在 ChatPanel 中集成格式检测
const parseStreamContent = (line: string) => {
  try {
    const event = JSON.parse(line);
    
    // ✅ 优先识别结构化格式
    if (event.type === "section") {
      return { type: "structured", data: event.section };
    }
    if (event.type === "sources") {
      return { type: "sources", data: event.sources };
    }
    if (event.type === "done" || event.type === "error") {
      return { type: event.type };
    }
    
    // ⚠️ 降级：无法识别则按 Markdown 处理
    return { type: "markdown", data: line };
  } catch {
    // 非 JSON 内容当作 Markdown
    return { type: "markdown", data: line };
  }
};

// 在渲染器中使用
const renderContent = (event: ParsedEvent) => {
  if (event.type === "structured") {
    return <StructuredRenderer sections={[event.data]} />;
  }
  if (event.type === "markdown") {
    return <MarkdownRenderer markdown={event.data} />;
  }
  // ... 其他处理
};
```

---

### Phase 4: API 路由（已完成）

**文件**: `backend/app/api/chat.py`

#### 非流式 API

```python
@router.post("/structured")
async def chat_structured(request: ChatRequest) -> StructuredChatResponse:
    """
    非流式结构化 API
    返回完整的 StructuredChatResponse
    """
    agent = AgentService()
    response = await agent.process_message_structured(
        message=request.message,
        session_id=request.session_id,
    )
    return response
```

#### 流式 API

```python
@router.post("/structured/stream")
async def chat_structured_stream(request: ChatRequest):
    """
    流式结构化 API
    返回 NDJSON 格式事件
    
    事件格式:
    {"type": "sources", "sources": [...]}
    {"type": "section", "section": {...}}
    {"type": "done", "confidence": 0.95}
    """
    async def event_generator():
        agent = AgentService()
        async for event in agent.process_message_structured_stream(
            message=request.message,
            session_id=request.session_id,
        ):
            yield f"{json.dumps(event)}\n"
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
```

---

## ✅ 验收标准

### 功能验收

| 标准 | 验证方法 | 状态 |
|------|--------|------|
| **结构合规** | 后端返回的 JSON 符合 StructuredChatResponse Schema | ✅ |
| **流式逐块返回** | section 生成后立即返回，前端逐块显示 | ✅ |
| **前端渲染正常** | 所有 section 类型、Markdown、列表嵌套正常显示 | ✅ |
| **向后兼容** | 旧 API(/api/chat/stream) 保持可用 | ✅ |
| **自动格式检测** | 前端优先识别结构化格式，无法识别则降级 | ✅ |
| **服务覆盖** | RAG、SQL、诊断、操作四大服务全支持 | ✅ |
| **错误处理** | LLM 超时/失败返回 error 事件 | ✅ |

### 手动测试场景

**场景 1：知识问答（RAG）**
```bash
curl -X POST http://localhost:8000/api/chat/structured/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "什么是向量数据库？", "session_id": "test-001"}'

# 预期输出：
# {"type": "sources", "sources": [...]}
# {"type": "section", "section": {"type": "text", "markdown": "..."}
# {"type": "section", "section": {"type": "list_ordered", "items": [...]}}
# {"type": "done", "confidence": 0.92}
```

**场景 2：前端逐块渲染**
- 启动前后端
- 在 ChatPanel 发送知识问题
- 观察：sources 显示 → 内容逐块显示 → 完成提示

**场景 3：错误降级**
- 模拟 LLM 服务超时
- 验证返回 error 事件
- 验证前端显示错误提示

---

## 🚨 风险与缓解

| 风险 | 概率 | 缓解方案 |
|------|------|--------|
| **LLM 输出格式不稳定** | 中 | 优化 Prompt 模板，增加格式校验逻辑，异常时降级为 Markdown |
| **流式 section 解析失败** | 低 | 完善单测，覆盖异常场景（部分 JSON、格式错误等） |
| **前端遗漏 section 类型** | 低 | 提前定义所有类型，集成测试覆盖全部 |
| **性能瓶颈（大规模 section）** | 低 | 限制单个 section 大小，提前测试大文档场景 |

---

## 🔄 升级与兼容性

### 版本兼容性

- **v1.0**（当前）：所有服务支持结构化 API，旧 API 保留
- **v1.1 计划**：逐步弃用旧 API，文档显示 deprecated 警告
- **v2.0 计划**：移除旧 API，完全转向结构化框架

### 迁移路径

1. **试点阶段**（当前）
   - 新增结构化 API，前端可通过参数切换
   - 旧 API 保持正常工作

2. **推广阶段**（v1.1）
   - 前端默认使用结构化 API
   - 旧 API 标记 deprecated

3. **下线阶段**（v2.0）
   - 旧 API 下线
   - 文档更新

---

## 📊 附录：服务对标

| 服务 | 主要 Section 类型 | 数据源 | 示例 |
|------|------------------|------|------|
| **RAG** | text / list / code | 知识库文档 | 知识点解释 + 示例代码 |
| **SQL** | code / table | 数据库结果 | SQL 语句 + 查询结果表格 |
| **诊断** | text / list / chart* | 系统指标 | 问题分析 + 建议清单 |
| **操作** | list / code / status* | 执行日志 | 操作步骤 + 执行命令 |

*chart/status: 扩展 section 类型，预留未来支持

---

## 🔗 相关文档

- 📄 ADR-0001: 内容格式检测方案 → `docs/architecture/ADR-0001-content-format-detection.md`
- 📄 ADR-0002: 内容格式规范化策略 → `docs/architecture/ADR-0002-content-format-strategy.md`
- 📋 测试与验证指南 → `docs/testing/STRUCTURED_OUTPUT_VERIFICATION.md`（待编写）

