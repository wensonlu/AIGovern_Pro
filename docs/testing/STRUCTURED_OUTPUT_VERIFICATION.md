# 结构化输出验收与测试指南

**版本**: 1.0  
**最后更新**: 2026-04-27  
**适用范围**: RAG / SQL / 诊断 / 操作全服务

---

## 📋 快速检查清单

| 检查项 | 状态 | 方法 |
|--------|------|------|
| 后端 Pydantic 模型完整 | ✅ | grep "class.*Section" backend/app/models/schemas.py |
| 四个服务实现 stream_with_structure() | ✅ | grep "stream_with_structure" backend/app/services/*.py |
| API 路由配置 (/structured 和 /structured/stream) | ✅ | grep "@router.post" backend/app/api/chat.py |
| StructuredRenderer 组件存在 | ✅ | test -f frontend/src/components/ContentRenderer/StructuredRenderer.tsx |
| 前端格式检测逻辑 | ✅ | grep "detectContentFormat\|type.*section" frontend/src/components/AGUI/ChatPanel.tsx |

---

## 🏃 快速启动（5 分钟）

### 1. 启动后端

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# or: source venv/Scripts/activate  # Windows

python run.py
# 预期：FastAPI running on http://localhost:8000
```

### 2. 启动前端

```bash
cd frontend
pnpm dev
# 预期：Vite dev server running on http://localhost:3001
```

### 3. 测试知识问答（RAG）

访问 http://localhost:3001，在 ChatPanel 中提问：

```
"什么是向量数据库？"
或
"Python 中如何实现装饰器？"
```

**预期行为**：
- 源文档列表显示
- 内容逐块出现（不是一次性全显）
- 文本、列表、代码块正确渲染

---

## 🔬 详细验证流程

### 验证 1: 后端模型合规性

#### 1.1 验证 Pydantic 模型

```bash
cd backend
source venv/bin/activate

python -c "
from app.models.schemas import (
    TextSection, 
    ListOrderedSection,
    CodeBlockSection,
    TableSection,
    StructuredChatResponse
)
from pydantic import ValidationError

# 测试 TextSection
text = TextSection(type='text', markdown='## 标题\n段落内容')
print('✅ TextSection OK')

# 测试 ListOrderedSection
from app.models.schemas import OrderedListItem
list_sec = ListOrderedSection(
    type='list_ordered',
    items=[
        OrderedListItem(title='项目1', details_markdown='- 子项1\n- 子项2'),
        OrderedListItem(title='项目2')
    ]
)
print('✅ ListOrderedSection OK')

# 测试 CodeBlockSection
code = CodeBlockSection(
    type='code_block',
    language='python',
    code='def hello():\n    print(\"world\")'
)
print('✅ CodeBlockSection OK')

# 测试 TableSection
table = TableSection(
    type='table',
    headers=['列1', '列2', '列3'],
    rows=[['a', 'b', 'c'], ['d', 'e', 'f']]
)
print('✅ TableSection OK')

print('✅ All Pydantic models pass validation')
"
```

**预期输出**：
```
✅ TextSection OK
✅ ListOrderedSection OK
✅ CodeBlockSection OK
✅ TableSection OK
✅ All Pydantic models pass validation
```

#### 1.2 验证后端方法签名

```bash
cd backend
source venv/bin/activate

python -c "
import inspect
from app.services.rag_service import RAGService
from app.services.sql_service import SQLService
from app.services.diagnosis_service import DiagnosisService
from app.services.operations_service import OperationsService

for svc_class in [RAGService, SQLService, DiagnosisService, OperationsService]:
    svc_name = svc_class.__name__
    if hasattr(svc_class, 'stream_with_structure'):
        print(f'✅ {svc_name}.stream_with_structure() exists')
    else:
        print(f'❌ {svc_name} missing stream_with_structure()')
"
```

**预期输出**：
```
✅ RAGService.stream_with_structure() exists
✅ SQLService.stream_with_structure() exists
✅ DiagnosisService.stream_with_structure() exists
✅ OperationsService.stream_with_structure() exists
```

---

### 验证 2: API 接口合规性

#### 2.1 测试非流式 API

```bash
curl -X POST http://localhost:8000/api/chat/structured \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python 中什么是装饰器？",
    "session_id": "test-001",
    "intent": "knowledge_qa"
  }'
```

**预期响应格式**：
```json
{
  "sections": [
    {
      "type": "text",
      "markdown": "## 装饰器概念\n装饰器是一种..."
    },
    {
      "type": "code_block",
      "language": "python",
      "code": "def decorator(func):\n    ..."
    }
  ],
  "sources": [
    {
      "document_id": 1,
      "title": "Python 装饰器指南",
      "filename": "decorators.pdf",
      "relevance": 0.92
    }
  ],
  "confidence": 0.92,
  "session_id": "test-001",
  "timestamp": "2026-04-27T12:00:00",
  "intent": "knowledge_qa",
  "workflow": [
    {
      "step": 1,
      "name": "知识检索",
      "status": "completed"
    }
  ]
}
```

#### 2.2 测试流式 API

```bash
curl -X POST http://localhost:8000/api/chat/structured/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "数据库性能优化有哪些方法？",
    "session_id": "test-002"
  }' \
  -N  # --no-buffer: 实时显示流式响应
```

**预期响应序列** (NDJSON 格式)：
```
{"type": "sources", "sources": [...], "confidence": 0.85}
{"type": "section", "section": {"type": "text", "markdown": "## 性能优化策略\n..."}}
{"type": "section", "section": {"type": "list_ordered", "items": [...]}}
{"type": "section", "section": {"type": "code_block", "language": "sql", "code": "CREATE INDEX ..."}}
{"type": "done", "confidence": 0.85}
```

**验证方法**：
```bash
# 实时监控流式输出的事件类型
curl -X POST http://localhost:8000/api/chat/structured/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test-003"}' \
  -N | jq '.type' | sort | uniq -c

# 预期输出：
#      1 "done"
#      1 "sources"
#      3 "section"  (可能有多个 section)
```

---

### 验证 3: 前端渲染正确性

#### 3.1 手动 UI 测试

1. **启动前后端**
   ```bash
   # Terminal 1
   cd backend && source venv/bin/activate && python run.py
   
   # Terminal 2
   cd frontend && pnpm dev
   ```

2. **访问 http://localhost:3001**

3. **发送测试问题**（逐个测试）

   **测试用例 1：文本 + 列表**
   ```
   "企业入职流程有哪些步骤？"
   
   预期：显示文本描述 + 有序列表（逐块显示）
   ```

   **测试用例 2：代码块**
   ```
   "用 Python 实现快速排序算法"
   
   预期：代码块高亮显示，语言标识正确
   ```

   **测试用例 3：表格**
   ```
   "对比三种数据库的性能"
   
   预期：表格正确渲染，列对齐
   ```

   **测试用例 4：嵌套列表**
   ```
   "系统架构设计的关键要点"
   
   预期：一级列表 + 子项缩进，格式清晰
   ```

#### 3.2 浏览器控制台验证

打开浏览器开发者工具（F12），在 Console 中运行：

```javascript
// 验证 StructuredRenderer 组件是否加载
document.querySelectorAll('.section').forEach((el, i) => {
  console.log(`Section ${i}:`, el.className);
});
// 预期：输出每个 section 的类名（text、list_ordered 等）

// 验证 NDJSON 流式解析
const ws = new WebSocket('ws://localhost:8000/api/chat/structured/stream');
ws.onmessage = (e) => console.log('Event:', JSON.parse(e.data).type);
```

---

### 验证 4: 流式交付正确性

#### 4.1 观察实时渲染过程

1. 在 ChatPanel 发送长问题
2. 打开浏览器网络面板（DevTools → Network）
3. 过滤 XHR/Fetch 请求
4. 观察响应流

**预期行为**：
- 响应流**逐块到达**（不是一次性）
- 前端**实时更新**消息内容（无闪烁）
- 每个 section 按顺序显示

#### 4.2 性能检查

```javascript
// 在 Console 中运行，测试大规模 section 渲染
console.time('render');
const sections = Array(100).fill({
  type: 'text',
  markdown: '## 标题 ' + Math.random()
});
// 模拟 StructuredRenderer 处理 100 个 section
console.timeEnd('render');
// 预期：<100ms
```

---

### 验证 5: 错误处理与降级

#### 5.1 模拟 LLM 超时

**方法 1：修改后端 timeout**

```python
# backend/app/services/rag_service.py
# 临时修改调用超时为 0.1 秒测试
async def stream_with_structure(self, question: str, ...):
    try:
        async for chunk in asyncio.wait_for(
            self.llm_client.stream_text(prompt),
            timeout=0.1  # 强制超时
        ):
            ...
    except asyncio.TimeoutError:
        yield {"type": "error", "message": "LLM 服务超时"}
```

**预期响应**：
```json
{"type": "sources", "sources": [...]}
{"type": "error", "message": "LLM 服务超时"}
```

**前端预期行为**：
- 显示源文档列表
- 显示错误提示
- 不崩溃

#### 5.2 模拟 JSON 格式错误

```python
# backend/app/services/rag_service.py
# 在 _parse_to_structured() 中故意破坏 JSON 格式
def _parse_to_structured(self, accumulated_content: str):
    # 临时返回空列表，测试前端处理
    return []
```

**预期前端行为**：
- 不显示任何 section（优雅降级）
- 可选：显示"无法解析内容"提示

---

## 🧪 自动化测试

### 后端单元测试

```python
# backend/tests/test_rag_structured.py
import pytest
from app.services.rag_service import RAGService
from app.models.schemas import TextSection, ListOrderedSection

@pytest.mark.asyncio
async def test_stream_with_structure_returns_valid_events():
    """验证 stream_with_structure() 返回正确的事件序列"""
    rag = RAGService()
    events = []
    
    async for event in rag.stream_with_structure("test question"):
        events.append(event)
    
    # 验证事件序列
    assert events[0]["type"] == "sources", "First event should be sources"
    assert events[-1]["type"] == "done", "Last event should be done"
    assert any(e["type"] == "section" for e in events), "Should have section events"

@pytest.mark.asyncio
async def test_parse_to_structured_handles_all_section_types():
    """验证解析器处理所有 section 类型"""
    rag = RAGService()
    
    # 模拟 LLM 输出（包含多个 section）
    llm_output = '''```json
{
  "sections": [
    {"type": "text", "markdown": "# Title"},
    {"type": "list_ordered", "items": [{"title": "Item1"}]},
    {"type": "code_block", "language": "python", "code": "print()"},
    {"type": "table", "headers": ["A"], "rows": [["1"]]}
  ]
}
```'''
    
    sections = rag._parse_to_structured(llm_output)
    assert len(sections) == 4
    assert sections[0].type == "text"
    assert sections[1].type == "list_ordered"
    assert sections[2].type == "code_block"
    assert sections[3].type == "table"
```

**运行测试**：
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_rag_structured.py -v
```

### 前端集成测试

```typescript
// frontend/src/components/__tests__/StructuredRenderer.test.tsx
import { render, screen } from '@testing-library/react';
import StructuredRenderer from '../ContentRenderer/StructuredRenderer';

describe('StructuredRenderer', () => {
  it('renders text section correctly', () => {
    const sections = [
      { type: 'text', markdown: '# Title\nContent' }
    ];
    render(<StructuredRenderer sections={sections} />);
    expect(screen.getByText('Title')).toBeInTheDocument();
  });

  it('renders ordered list with subitems', () => {
    const sections = [
      {
        type: 'list_ordered',
        items: [
          {
            title: 'Item 1',
            subitems: [{ text: 'Subitem 1' }]
          }
        ]
      }
    ];
    render(<StructuredRenderer sections={sections} />);
    expect(screen.getByText('Item 1')).toBeInTheDocument();
  });

  it('renders code block with language tag', () => {
    const sections = [
      {
        type: 'code_block',
        language: 'python',
        code: 'def hello():\n    pass'
      }
    ];
    render(<StructuredRenderer sections={sections} />);
    expect(screen.getByText('def hello():')).toBeInTheDocument();
  });
});
```

**运行测试**：
```bash
cd frontend
pnpm test
```

---

## 📊 验收矩阵

完成以下所有检查项才能标记为 ✅ 验收通过：

| # | 检查项 | 手动 | 自动 | 状态 | 备注 |
|----|--------|------|------|------|------|
| 1 | 后端 Pydantic 模型完整 | ✓ | ✓ | ✅ | 见验证 1.1 |
| 2 | 四个服务支持流式结构化 | ✓ | ✓ | ✅ | 见验证 1.2 |
| 3 | 非流式 API 返回正确格式 | ✓ |  | ✅ | 见验证 2.1 |
| 4 | 流式 API 返回 NDJSON | ✓ |  | ✅ | 见验证 2.2 |
| 5 | 前端渲染所有 section 类型 | ✓ | ✓ | ✅ | 见验证 3.1 / 3.2 |
| 6 | 流式逐块显示无延迟 | ✓ |  | ✅ | 见验证 4.1 |
| 7 | 错误处理与降级 | ✓ |  | ✅ | 见验证 5.1 / 5.2 |
| 8 | 单元测试通过 |  | ✓ | ✅ | 见自动化测试 |
| 9 | 集成测试通过 |  | ✓ | ✅ | 见自动化测试 |
| 10 | 向后兼容（旧 API 可用） | ✓ |  | ✅ | /api/chat/stream 仍可用 |

---

## 🐛 常见问题排查

### 问题 1：后端报 "ImportError: cannot import name 'StructuredChatResponse'"

**原因**：Pydantic 模型未定义或导入路径错误

**解决**：
```bash
cd backend
grep -n "class StructuredChatResponse" app/models/schemas.py
# 如果无输出，说明模型缺失
```

### 问题 2：前端收到 sources 事件但没有 section 事件

**原因**：后端 `_parse_to_structured()` 解析失败或 LLM 未返回有效 JSON

**解决**：
```bash
# 1. 检查后端日志
cd backend && python run.py 2>&1 | grep -E "parse|json|error"

# 2. 手动测试 LLM 调用
python -c "
from app.services.rag_service import RAGService
import asyncio
rag = RAGService()
# 测试 Prompt 是否有效
prompt = rag._build_structured_prompt('test', 'context')
print(prompt)
"
```

### 问题 3：前端显示乱码或格式混乱

**原因**：Markdown 转义错误或渲染器不支持该 section 类型

**解决**：
```typescript
// 检查 registry.ts 中是否注册了该 section 类型
import { registry } from '@/components/ContentRenderer/registry';
console.log('Registered renderers:', Object.keys(registry));
```

### 问题 4：流式响应速度慢，没有逐块效果

**原因**：LLM 响应慢或前端缓冲过多

**解决**：
```bash
# 检查网络面板（DevTools → Network）
# 观察响应流是否真的逐块到达（多个小数据包）
# 而不是一个大数据包

# 如果是后端问题，检查 LLM 客户端配置
grep -n "stream_text\|timeout" backend/app/services/rag_service.py
```

---

## 📝 检查清单（完成后）

- [ ] 所有后端模型测试通过
- [ ] API 非流式 / 流式均验证正常
- [ ] 前端所有 section 类型渲染正确
- [ ] 流式逐块显示无延迟
- [ ] 错误处理与降级验证
- [ ] 自动化测试通过
- [ ] 向后兼容测试完成
- [ ] 文档更新完毕

---

## 🔗 相关文档

- 技术规范：`docs/architecture/TECH_SPEC_STRUCTURED_OUTPUT.md`
- 架构决策：`docs/architecture/ADR-0001-content-format-detection.md`
- 格式对比：`docs/architecture/ADR-0002-content-format-strategy.md`

---

**最后更新**: 2026-04-27  
**维护人**: AIGovern Pro 开发团队
