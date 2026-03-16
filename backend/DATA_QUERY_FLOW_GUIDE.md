# 📊 数据查询系统工作流程指南

> **NL2SQL** = Natural Language to SQL（自然语言转 SQL）

## 🎯 一句话理解数据查询

**用户用自然语言提问 → AI 理解意图并生成 SQL → 执行查询获取真实数据 → 用图表或文字展示结果**

---

## 📖 通俗类比

想象你在餐厅点餐：

1. **用户提问**："最近7天每天有多少订单？"
   - 就像你对服务员说："我想知道最近一周每天卖出多少份菜"

2. **AI 理解意图**（意图识别）
   - 服务员理解你要查"订单数量"，时间范围是"最近7天"，还要"按天分组"
   - 系统识别出这是**数据查询**意图，不是知识问答或智能操作

3. **生成 SQL**（自然语言转 SQL）
   - 服务员在后厨系统中输入精确的查询指令
   - 系统生成：`SELECT DATE(created_at), COUNT(*) FROM orders WHERE ...`

4. **执行查询**
   - 后厨系统查询数据库，返回真实数据
   - 系统连接 PostgreSQL 执行 SQL，获取结果

5. **展示结果**
   - 服务员用图表展示：第1天50单，第2天80单...
   - 系统显示折线图或表格，让用户一目了然

---

## 🔄 完整流程（6 个步骤）

### 第 1️⃣ 步：用户在前端提问

```
【前端对话面板】
用户输入：[最近7天订单趋势如何？] → 点击发送
          ↓
发送 HTTP 请求到后端
```

**实际网络请求：**
```http
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "question": "最近7天订单趋势如何？",
  "session_id": "session_123456"
}
```

---

### 第 2️⃣ 步：意图识别

**问题：** 用户的话可能是在问知识、查数据、或者执行操作，系统怎么区分？

**解决方案：** 用大模型（LLM）分析用户意图

```
用户输入："最近7天订单趋势如何？"
  ↓
【调用 LLM 进行意图识别】
  ↓
分析关键词：
- "最近7天" → 时间范围
- "订单" → 数据实体
- "趋势" → 分析型查询
  ↓
判断结果：data_query（数据查询）✅
```

**与其他意图的区别：**

| 用户输入 | 识别意图 | 处理方式 |
|---------|---------|---------|
| "公司请假流程是什么？" | knowledge_qa | 查知识库文档 |
| "最近7天订单趋势如何？" | data_query | 生成 SQL 查数据库 |
| "批准所有待审订单" | smart_operation | 执行审批操作 |
| "订单量是否正常？" | business_diagnosis | 诊断分析 |

---

### 第 3️⃣ 步：生成 SQL 查询

**问题：** 自然语言怎么转换成数据库能理解的 SQL？

**解决方案：** 使用 Few-shot Prompting + Schema 信息生成 SQL

```
用户提问："最近7天订单趋势如何？"
  ↓
【构建 Prompt】

你是一位 SQL 专家。根据以下数据库 Schema 生成 SQL：

Schema：
- orders 表：id, user_id, product_id, quantity, amount, status, created_at

自然语言查询：最近7天订单趋势如何？

要求：
1. 使用 PostgreSQL 语法
2. 时间筛选：created_at >= CURRENT_DATE - INTERVAL '7 days'
3. 按天分组：GROUP BY DATE(created_at)
4. 只返回 SQL，不要解释

  ↓
【LLM 生成】
  ↓
生成的 SQL：

SELECT DATE(created_at) as date, 
       COUNT(*) as order_count
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date
```

**生成的 SQL 示例：**

| 用户提问 | 生成的 SQL |
|---------|-----------|
| "有多少用户？" | `SELECT COUNT(*) FROM users` |
| "订单总金额是多少？" | `SELECT SUM(amount) FROM orders` |
| "每个状态的订单数量？" | `SELECT status, COUNT(*) FROM orders GROUP BY status` |
| "库存不足的商品？" | `SELECT name, stock FROM products WHERE stock < 10` |

---

### 第 4️⃣ 步：安全检查和执行

**问题：** 生成的 SQL 安全吗？会不会误删数据？

**解决方案：** 多层安全防护

```
生成的 SQL：
SELECT DATE(created_at), COUNT(*) 
FROM orders 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' 
GROUP BY DATE(created_at)
  ↓
【安全检查】
  ↓
✅ 检查1：SQL 以 SELECT 开头（只允许查询）
✅ 检查2：不包含 DELETE/DROP/UPDATE 等危险关键字
✅ 检查3：语法正确
  ↓
【执行查询】
  ↓
连接 PostgreSQL 数据库
  ↓
执行 SQL，获取结果
```

**安全策略：**
- ✅ **只允许 SELECT**：其他操作（INSERT/UPDATE/DELETE）被拒绝
- ✅ **只读权限**：数据库用户只有查询权限
- ✅ **SQL 注入防护**：使用参数化查询
- ✅ **超时限制**：查询超过 30 秒自动终止

---

### 第 5️⃣ 步：数据处理和格式化

**问题：** 数据库返回的是原始数据，怎么展示给用户？

**解决方案：** 根据查询类型选择合适的展示方式

```
查询结果：
[
  {"date": "2024-03-10", "order_count": 45},
  {"date": "2024-03-11", "order_count": 52},
  {"date": "2024-03-12", "order_count": 38},
  {"date": "2024-03-13", "order_count": 65}
]
  ↓
【推断图表类型】
  ↓
关键词"趋势" → 折线图 (line)
  ↓
【生成自然语言回答】
  ↓
"最近7天的订单趋势如下：
- 3月10日：45单
- 3月11日：52单  
- 3月12日：38单
- 3月13日：65单（最高）

整体呈上升趋势，建议继续保持当前运营策略。"
```

**图表类型推断规则：**

| 关键词 | 图表类型 | 适用场景 |
|-------|---------|---------|
| "趋势"、"时间"、"变化" | 折线图 (line) | 时间序列数据 |
| "对比"、"比较"、"排名" | 柱状图 (bar) | 类别对比 |
| "占比"、"比例"、"分布" | 饼图 (pie) | 占比分析 |
| "分布"、"散点" | 散点图 (scatter) | 相关性分析 |
| 其他 | 表格 (table) | 明细数据 |

---

### 第 6️⃣ 步：返回结果给前端

**后端返回：**
```json
{
  "answer": "最近7天的订单趋势如下：\n- 3月10日：45单\n- 3月11日：52单\n...",
  "sources": [
    {
      "document_id": 0,
      "title": "数据查询",
      "filename": "database",
      "text_preview": "SQL: SELECT DATE(created_at), COUNT(*) FROM orders..."
    }
  ],
  "confidence": 0.95,
  "session_id": "session_123456",
  "timestamp": "2024-03-13T10:30:00",
  "chart_type": "line",
  "chart_data": [
    {"date": "2024-03-10", "order_count": 45},
    {"date": "2024-03-11", "order_count": 52},
    {"date": "2024-03-12", "order_count": 38},
    {"date": "2024-03-13", "order_count": 65}
  ]
}
```

**前端展示：**
```
┌─────────────────────────────────────────┐
│  🤖 AI 助手                              │
├─────────────────────────────────────────┤
│  最近7天的订单趋势如下：                   │
│  • 3月10日：45单                         │
│  • 3月11日：52单                         │
│  • 3月12日：38单                         │
│  • 3月13日：65单（最高）                  │
│                                         │
│  📈 订单趋势图                            │
│     ┌─────────────────────────┐         │
│  70 │                    ●    │         │
│  60 │         ●          │    │         │
│  50 │    ●    │          │    │         │
│  40 │ ●  │    │    ●     │    │         │
│  30 └─────────────────────────┘         │
│       10日 11日 12日 13日               │
│                                         │
│  💡 数据来源于数据库查询                   │
└─────────────────────────────────────────┘
```

---

## 🗄️ 数据库 Schema

### 当前支持的表

```sql
-- 订单表
CREATE TABLE orders (
  id INT PRIMARY KEY,
  user_id INT,           -- 用户ID
  product_id INT,        -- 商品ID
  quantity INT,          -- 数量
  amount DECIMAL(10,2),  -- 金额
  status VARCHAR(50),    -- 状态：pending/completed/refunded
  created_at TIMESTAMP   -- 创建时间
);

-- 用户表
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),     -- 姓名
  email VARCHAR(100),    -- 邮箱
  role VARCHAR(50),      -- 角色：admin/manager/user
  created_at TIMESTAMP   -- 注册时间
);

-- 商品表
CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(100),     -- 商品名
  sku VARCHAR(50),       -- SKU编码
  price DECIMAL(10,2),   -- 价格
  stock INT,             -- 库存
  category VARCHAR(50),  -- 分类
  created_at TIMESTAMP   -- 创建时间
);
```

---

## 🎯 支持的查询类型

### 1. 基础统计查询
```
用户："有多少用户？"
SQL：SELECT COUNT(*) as total_users FROM users
```

### 2. 聚合分析查询
```
用户："总交易额是多少？"
SQL：SELECT SUM(amount) as total_gmv FROM orders
```

### 3. 分组统计查询
```
用户："每个状态的订单数量？"
SQL：SELECT status, COUNT(*) as count FROM orders GROUP BY status
```

### 4. 时间趋势查询
```
用户："最近7天订单趋势？"
SQL：SELECT DATE(created_at), COUNT(*) 
     FROM orders 
     WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
     GROUP BY DATE(created_at)
```

### 5. 条件筛选查询
```
用户："库存不足的商品有哪些？"
SQL：SELECT name, stock FROM products WHERE stock < 10
```

---

## 🔧 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  对话输入框   │ → │   发送请求    │ → │  展示结果    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ POST /api/chat
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. AgentService.process_message()                    │  │
│  │     └─→ _recognize_intent() → "data_query"            │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2. _handle_data_query()                              │  │
│  │     ├─→ sql_service.generate_sql() → SQL              │  │
│  │     ├─→ sql_service.execute_query() → 数据            │  │
│  │     └─→ llm.generate_text() → 自然语言回答           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据库 (PostgreSQL)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  orders  │  │  users   │  │ products │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 关键代码文件

| 文件 | 作用 |
|-----|------|
| `app/services/agent_service.py` | 意图识别和路由 |
| `app/services/sql_service.py` | SQL 生成和执行 |
| `app/models/db_models.py` | 数据库模型定义 |
| `app/api/chat.py` | 对话 API 接口 |

---

## 🐛 常见问题

### Q1: 为什么有时候 SQL 生成错误？
**A:** 可能是：
- 用户提问太模糊，AI 无法理解意图
- 表名/字段名理解错误
- 时间语法问题（已修复 PostgreSQL INTERVAL 语法）

**解决：** 优化提问，使用更明确的表达，如：
- ❌ "最近的订单"
- ✅ "最近7天每天的订单数量"

### Q2: 能支持复杂的多表 JOIN 吗？
**A:** 目前支持基础查询，复杂 JOIN 正在优化中。建议：
- 先查询单表数据
- 通过多次查询获取关联信息

### Q3: 数据安全如何保障？
**A:** 多层防护：
- 只允许 SELECT 查询
- 数据库只读账号
- SQL 注入防护
- 敏感数据脱敏

---

## 🚀 未来优化方向

1. **智能图表推荐**：根据数据特征自动选择最佳图表
2. **查询历史学习**：记住常用查询，加速生成
3. **多表关联查询**：支持 JOIN、子查询等复杂 SQL
4. **数据权限控制**：基于用户角色限制可查询的数据范围
5. **查询缓存**：重复查询直接返回缓存结果

---

**最后更新：2026-03-16**
**版本：v1.0**
