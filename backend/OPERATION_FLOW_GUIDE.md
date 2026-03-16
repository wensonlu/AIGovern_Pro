# 🤖 智能操作系统工作流程指南

> **A2UI** = AI to UI（AI驱动的用户界面操作）

## 🎯 一句话理解智能操作

**用户用自然语言下达指令 → AI 理解意图并解析参数 → 执行具体操作 → 记录操作日志 → 反馈执行结果**

---

## 📖 通俗类比

想象你有一个智能秘书：

1. **用户下达指令**："批准所有金额小于1000的报销单"
   - 就像你对秘书说："帮我把小额报销都批了"

2. **AI 理解意图**（意图识别）
   - 秘书理解你要执行"审批"操作
   - 识别出条件：金额 < 1000
   - 系统识别出这是**智能操作**意图，不是查询或问答

3. **解析操作参数**（参数提取）
   - 秘书明确：操作类型=批量审批，条件=金额<1000
   - 系统解析：operation_type="approve_order", parameters={"amount_limit": 1000}

4. **执行操作**（真实数据库操作）
   - 秘书在系统中执行审批，修改订单状态
   - 系统执行 UPDATE orders SET status='approved' WHERE amount < 1000

5. **记录日志**（操作审计）
   - 秘书记录：谁、什么时候、做了什么操作
   - 系统写入 operation_logs 表，包含操作详情和结果

6. **反馈结果**
   - 秘书汇报："已批准15张报销单"
   - 系统返回："✅ 操作成功，批准15个订单"

---

## 🔄 完整流程（6 个步骤）

### 第 1️⃣ 步：用户在前端下达指令

```
【前端对话面板】
用户输入：[批准所有待处理的订单] → 点击发送
          ↓
发送 HTTP 请求到后端
```

**实际网络请求：**
```http
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "question": "批准所有待处理的订单",
  "session_id": "session_123456"
}
```

---

### 第 2️⃣ 步：意图识别

**问题：** 用户的话可能是在询问、查询、或者下达操作指令，系统怎么区分？

**解决方案：** 用大模型（LLM）分析用户意图，识别操作类关键词

```
用户输入："批准所有待处理的订单"
  ↓
【调用 LLM 进行意图识别】
  ↓
分析关键词：
- "批准" → 操作动词
- "待处理" → 操作对象状态
- "订单" → 操作对象
  ↓
判断结果：smart_operation（智能操作）✅
```

**与其他意图的区别：**

| 用户输入 | 识别意图 | 处理方式 |
|---------|---------|---------|
| "待处理订单有哪些？" | data_query | 查询待处理订单列表 |
| "批准所有待处理的订单" | smart_operation | 执行审批操作 |
| "审批流程是什么？" | knowledge_qa | 查知识库文档 |
| "订单量是否正常？" | business_diagnosis | 诊断分析 |

**操作类关键词库：**
```python
operation_keywords = [
    "批准", "审批", "同意", "通过",      # 审批类
    "导出", "下载", "生成",             # 导出类
    "退款", "退货", "取消",             # 退款类
    "更新", "修改", "调整", "改变",     # 更新类
    "补货", "库存", "进货",             # 库存类
    "删除", "移除", "清空",             # 删除类（受限制）
]
```

---

### 第 3️⃣ 步：解析操作类型和参数

**问题：** 自然语言包含操作意图和具体参数，怎么提取？

**解决方案：** 基于规则 + 正则表达式的参数解析器

```
用户输入："批准所有待处理的订单"
  ↓
【参数解析】
  ↓
1. 匹配操作类型：
   - 包含"批准"或"审批" → operation_type = "approve_order"

2. 提取参数：
   - 正则匹配数字：无
   - 识别条件："待处理" → status = "pending"
   - 默认：批准所有 pending 状态的订单
  ↓
解析结果：
{
  "operation_type": "approve_order",
  "parameters": {
    "order_ids": []  # 空数组表示批量处理所有符合条件的
  }
}
```

**更多解析示例：**

| 用户输入 | 解析结果 |
|---------|---------|
| "导出用户列表" | `operation_type: "export_users", format: "csv"` |
| "处理订单 123 的退款" | `operation_type: "process_refund", order_id: 123` |
| "修改笔记本电脑价格为 99 元" | `operation_type: "update_product_price", product_name: "笔记本电脑", new_price: 99` |
| "补充库存" | `operation_type: "batch_update_stock"` |

---

### 第 4️⃣ 步：执行操作

**问题：** 怎么确保操作安全、可追溯？

**解决方案：** 操作模板 + 日志记录 + 事务处理

```
操作参数：
{
  "operation_type": "approve_order",
  "parameters": {"order_ids": []}
}
  ↓
【查找操作模板】
  ↓
operation_templates = {
    "approve_order": self._approve_order,      → 找到！
    "export_users": self._export_users,
    "process_refund": self._process_refund,
    "batch_update_stock": self._batch_update_stock,
    "update_product_price": self._update_product_price,
}
  ↓
【创建操作日志（pending状态）】
  ↓
INSERT INTO operation_logs (
    user_id, operation_type, operation_target, 
    operation_detail, status, created_at
) VALUES (
    1, 'approve_order', 'orders',
    '{"parameters": {"order_ids": []}}',
    'pending', NOW()
)
  ↓
【执行具体操作】
  ↓
async def _approve_order(parameters, db):
    # 查询所有 pending 订单
    pending_orders = db.query(Order).filter(Order.status == "pending").all()
    
    # 批量更新状态
    for order in pending_orders:
        order.status = "approved"
    
    db.commit()
    return {"approved_count": len(pending_orders)}
  ↓
【更新日志为 success】
  ↓
UPDATE operation_logs 
SET status = 'success', 
    operation_detail = '{"parameters": {}, "result": {"approved_count": 15}}'
WHERE id = 123
```

**支持的操作类型：**

| 操作类型 | 功能 | 适用场景 |
|---------|------|---------|
| `approve_order` | 批量审批订单 | "批准待审订单" |
| `export_users` | 导出用户数据 | "导出用户列表" |
| `process_refund` | 处理退款 | "订单 123 退款" |
| `batch_update_stock` | 批量更新库存 | "补充库存" |
| `update_product_price` | 修改商品价格 | "修改XX价格为99元" |

---

### 第 5️⃣ 步：权限检查与安全控制

**问题：** 怎么防止误操作或越权操作？

**解决方案：** 多层次安全策略

```
【安全策略层】

1. 操作模板白名单
   ✅ 只允许预定义的操作类型
   ❌ 未知操作直接拒绝

2. 参数校验
   ✅ 检查必填参数
   ✅ 数据类型校验
   ✅ 范围限制（如金额不能为负数）

3. 权限控制（扩展中）
   - 普通用户：只能操作自己的数据
   - 管理员：可操作全部数据
   - 系统级操作：需要二次确认

4. 操作日志审计
   - 记录谁在什么时间做了什么
   - 记录操作参数和结果
   - 支持事后追溯

5. 数据库事务
   - 操作失败自动回滚
   - 保证数据一致性
```

**安全示例：**

```python
# 危险操作拦截
if operation_type not in operation_templates:
    raise ValueError(f"不支持的操作类型: {operation_type}")

# 参数校验
if new_price < 0:
    raise ValueError("价格不能为负数")

# 数据库事务保护
try:
    result = await handler(parameters, db)
    db.commit()  # 成功提交
except Exception as e:
    db.rollback()  # 失败回滚
    raise e
```

---

### 第 6️⃣ 步：返回结果给前端

**后端返回：**
```json
{
  "status": "success",
  "operation_id": 42,
  "operation_type": "approve_order",
  "result": {
    "approved_count": 15,
    "order_ids": [101, 102, 103, ...]
  },
  "timestamp": "2024-03-13T14:30:00"
}
```

**前端展示：**
```
┌─────────────────────────────────────────┐
│  🤖 AI 助手                              │
├─────────────────────────────────────────┤
│                                         │
│   ✅ 操作执行成功！                       │
│                                         │
│   操作类型：approve_order                │
│   - approved_count: 15                   │
│   - order_ids: [101, 102, 103, ...]      │
│                                         │
│   操作已记录，操作ID: 42                  │
│                                         │
└─────────────────────────────────────────┘
```

**失败时展示：**
```
┌─────────────────────────────────────────┐
│  🤖 AI 助手                              │
├─────────────────────────────────────────┤
│                                         │
│   ❌ 操作执行失败：商品不存在              │
│                                         │
│   操作类型：update_product_price         │
│   操作ID: 43                             │
│                                         │
│   💡 建议：请检查商品名称是否正确          │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🗄️ 操作日志数据结构

### operation_logs 表结构

```sql
CREATE TABLE operation_logs (
    id INT PRIMARY KEY,
    user_id INT,                    -- 操作用户ID
    operation_type VARCHAR(100),    -- 操作类型
    operation_target VARCHAR(100),  -- 操作目标（表名）
    operation_detail JSON,          -- 操作详情（参数+结果）
    status VARCHAR(50),             -- 状态：pending/success/failed
    created_at TIMESTAMP            -- 操作时间
);
```

### 日志示例

**成功日志：**
```json
{
  "id": 42,
  "user_id": 1,
  "operation_type": "approve_order",
  "operation_target": "orders",
  "operation_detail": {
    "parameters": {"order_ids": []},
    "result": {
      "approved_count": 15,
      "order_ids": [101, 102, 103]
    }
  },
  "status": "success",
  "created_at": "2024-03-13T14:30:00"
}
```

**失败日志：**
```json
{
  "id": 43,
  "user_id": 1,
  "operation_type": "update_product_price",
  "operation_target": "products",
  "operation_detail": {
    "parameters": {
      "product_name": "未知商品",
      "new_price": 99
    },
    "error": "商品不存在"
  },
  "status": "failed",
  "created_at": "2024-03-13T14:35:00"
}
```

---

## 🎯 典型应用场景

### 场景1：批量审批
```
用户："批准所有金额小于1000的报销单"

系统处理：
1. 识别意图：smart_operation
2. 解析参数：operation_type="approve_order", amount_limit=1000
3. 执行操作：UPDATE orders SET status='approved' WHERE amount < 1000
4. 返回结果：✅ 已批准 25 个订单
```

### 场景2：价格调整
```
用户："把笔记本电脑 LAPTOP001 价格改成99"

系统处理：
1. 识别意图：smart_operation
2. 解析参数：operation_type="update_product_price", sku="LAPTOP001", price=99
3. 执行操作：UPDATE products SET price=99 WHERE sku='LAPTOP001'
4. 记录价格历史到 product_price_history 表
5. 返回结果：✅ 价格修改成功，旧价格：5999 → 新价格：99
```

### 场景3：数据导出
```
用户："导出所有用户数据为 JSON 格式"

系统处理：
1. 识别意图：smart_operation
2. 解析参数：operation_type="export_users", format="json"
3. 执行操作：SELECT * FROM users
4. 生成 JSON 文件并提供下载链接
5. 返回结果：✅ 导出成功，共 150 条用户数据
```

---

## 🔧 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  自然语言输入 │ → │  发送请求    │ → │  结果展示    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ POST /api/chat
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. AgentService.process_message()                    │  │
│  │     └─→ _recognize_intent() → "smart_operation"       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2. _handle_smart_operation()                         │  │
│  │     ├─→ _parse_operation() → (type, params)           │  │
│  │     └─→ operation_service.execute_operation()         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  3. OperationService.execute_operation()              │  │
│  │     ├─→ 创建日志 (pending)                            │  │
│  │     ├─→ 执行具体操作函数                              │  │
│  │     ├─→ 更新日志 (success/failed)                     │  │
│  │     └─→ 返回结果                                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据库 (PostgreSQL)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │  orders  │  │ products │  │     operation_logs       │  │
│  └──────────┘  └──────────┘  └──────────────────────────┘  │
│  ┌──────────┐  ┌────────────────────────────────────────┐  │
│  │  users   │  │      product_price_history             │  │
│  └──────────┘  └────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 关键代码文件

| 文件 | 作用 |
|-----|------|
| `app/services/agent_service.py` | 意图识别和参数解析（_parse_operation） |
| `app/services/operation_service.py` | 操作执行和日志记录 |
| `app/api/operations.py` | 操作相关 API 接口 |
| `app/models/db_models.py` | OperationLog 模型定义 |

---

## 🐛 常见问题

### Q1: 为什么有些操作指令识别失败？
**A:** 可能是：
- 指令表达太模糊，缺少关键操作动词
- 参数格式不规范（如缺少单位）
- 操作类型不在白名单中

**解决：** 使用更明确的表达，如：
- ❌ "处理一下那些订单"
- ✅ "批准所有待处理的订单"

### Q2: 操作失败了能回滚吗？
**A:** 当前每个操作都有事务保护，失败后自动回滚。但已成功的操作需要手动反向操作恢复。

### Q3: 怎么查看历史操作记录？
**A:** 可以调用 API：
```http
GET http://localhost:8000/api/operations/logs
```

### Q4: 能支持自定义操作吗？
**A:** 可以扩展 operation_templates 添加新的操作类型，需要：
1. 在 operation_templates 中注册
2. 实现对应的处理方法
3. 更新参数解析规则

---

## 🚀 未来优化方向

1. **操作确认机制**：高风险操作（如批量删除）需要二次确认
2. **操作撤销功能**：支持撤销最近的操作（undo）
3. **批量操作优化**：支持更复杂的批量条件（如"金额>100且状态=pending"）
4. **操作编排**：支持多个操作串联执行（如"导出→处理→发送邮件"）
5. **权限细化**：基于角色和数据范围的细粒度权限控制
6. **操作预览**：执行前预览影响的数据范围和数量

---

## 🔄 与 RAG、数据查询的对比

| 特性 | 知识问答 (RAG) | 数据查询 (NL2SQL) | 智能操作 (A2UI) |
|-----|---------------|------------------|----------------|
| **用户输入** | "请假流程是什么？" | "有多少订单？" | "批准待审订单" |
| **核心能力** | 文档检索 + 生成 | SQL生成 + 执行 | 意图解析 + 操作执行 |
| **数据变更** | ❌ 只读 | ❌ 只读 | ✅ 可修改数据 |
| **关键技术** | Embedding + LLM | NL2SQL | 参数解析 + 事务 |
| **输出形式** | 自然语言回答 | 数据/图表 | 操作结果 + 日志 |
| **风险等级** | 低 | 低 | 中（有数据变更） |

---

**最后更新：2026-03-16**
**版本：v1.0**
