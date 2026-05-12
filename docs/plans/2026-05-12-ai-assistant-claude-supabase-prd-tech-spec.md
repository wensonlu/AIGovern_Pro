# AIGovern Pro AI 助手能力升级方案（需求 + 技术）

- 文档日期：2026-05-12
- 版本：v1.0
- 状态：待评审
- 适用阶段：MVP（2 周）

## 1. 背景与问题定义

当前 AI 助手具备问答与基础业务支持能力，但在“可执行、可追踪、可审计”方面仍有明显缺口：

1. 只停留在建议层，缺少端到端任务闭环。
2. 工具调用过程不可视，用户无法理解助手“为什么这样做”。
3. 写操作缺少统一审批闸门，存在误执行和合规风险。
4. 多租户场景下，缺乏统一的会话与审计事件模型。

本方案目标是在保持现有架构稳定的前提下，构建一个可控的 Agent 工具执行框架：

- Supabase 提供数据存储与审计能力。
- 大模型负责推理、规划和工具编排。
- Tool 层负责受控执行和结果标准化。
- 前端提供可观测时间线与审批交互。

## 2. 需求方案（PRD）

## 2.1 产品目标

在 2 周内实现“查数 -> 图表 -> 跟进任务”的最小闭环，验证 AI 助手从对话到执行的业务价值。

## 2.2 业务价值

1. 运营效率：减少人工跨系统查数和手工建任务。
2. 决策质量：提供可追溯的执行链路与上下文证据。
3. 风险可控：高风险操作必须审批，支持审计回放。

## 2.3 目标用户

1. 一线业务运营：快速查询指标并生成行动事项。
2. 团队负责人：审阅关键动作审批，管理执行质量。
3. 管理员/合规角色：按租户审计 AI 行为与工具调用。

## 2.4 MVP 范围（In Scope）

1. 三个工具：`read_sql`、`generate_chart_data`、`create_followup_task`。
2. 对话中的工具自动调用与结果回填。
3. 右侧执行时间线（工具名、输入摘要、输出摘要、耗时、状态）。
4. 写操作审批流（pending -> approved/rejected）。
5. 全链路审计事件落库（可按 session 重放）。
6. 多租户隔离（tenant_id + RLS）。

## 2.5 非目标（Out of Scope）

1. 多模型路由与自动降本策略（后续迭代）。
2. 复杂多 Agent 编排（先单 Agent）。
3. 跨系统审批中心集成（先内置审批弹窗）。
4. 全量 BI 图表体系（仅支持常见 line/bar/pie/area）。

## 2.6 用户故事

1. 作为运营，我希望用自然语言查询核心指标，并马上看到结构化结果。
2. 作为运营，我希望把查询结果一键转图表，方便团队沟通。
3. 作为负责人，我希望写操作先审批，避免 AI 误操作。
4. 作为管理员，我希望查看任意会话的完整工具调用和审计事件。

## 2.7 核心流程

1. 用户提问。
2. 模型生成计划并发起 `read_sql`。
3. 查询成功后按需求触发 `generate_chart_data`。
4. 若需后续跟进，模型提议 `create_followup_task`。
5. 系统进入审批态，用户确认后执行。
6. 结果回填对话，并写入审计事件。

## 2.8 验收标准（P0）

1. 单轮可完成“查数 -> 图表 -> 建跟进任务”。
2. 任意写操作未经审批不得执行。
3. 工具调用错误能给出可读错误码与提示。
4. 审计日志可按 `tenant_id + session_id` 完整回放。
5. 前端时间线可展示每步状态变化。

## 2.9 里程碑

1. Week 1：数据模型/RLS + `read_sql` + 时间线基础展示。
2. Week 2：`generate_chart_data` + 审批流 + `create_followup_task` + 审计回放。

## 3. 技术方案（Tech Spec）

## 3.1 总体架构

```text
Frontend (React + AGUI)
  -> Assistant API (FastAPI)
    -> Planner (LLM 推理)
    -> Tool Router (白名单 + 参数校验)
      -> read_sql (只读查询)
      -> generate_chart_data (数据映射)
      -> create_followup_task (审批后写入)
    -> Audit Logger
  -> Supabase Postgres (session/message/tool_call/approval/audit)
```

设计原则：

1. 推理与执行解耦：模型不直连数据库高危接口。
2. 先约束后放开：白名单工具 + schema 校验。
3. 可观测优先：每个状态变化都可追踪。
4. 租户隔离前置：所有核心表默认 RLS。

## 3.2 组件设计

1. Planner（模型编排）
- 输入：用户问题、历史消息、可用工具描述。
- 输出：工具调用意图（tool_name + arguments）或直接答案。
- 约束：禁止输出未注册工具。

2. Tool Router（执行网关）
- 统一入参：`trace_id/tenant_id/user_id/tool_name/arguments`。
- 职责：schema 校验、权限校验、审批校验、超时控制、错误映射。

3. Approval Service（审批服务）
- 写操作统一进入 `pending_approval`。
- 审批通过后进入 `executing`。
- 支持拒绝并回写对话解释。

4. Audit Service（审计服务）
- 按事件写入：`tool_requested/tool_approved/tool_executed/tool_failed/final_answer`。
- 可用于回放、风控和后续评估。

## 3.3 工具定义

1. `read_sql`
- 限制：仅允许单条 `SELECT`，默认 `LIMIT <= 200`。
- 拦截：拒绝 DDL/DML、拒绝多语句。

2. `generate_chart_data`
- 输入必须引用同 session 的 `read_sql` 输出。
- 输出统一结构：`{chartType, x, y, series}`。

3. `create_followup_task`
- 风险等级：`medium/high`。
- 执行前置条件：存在 `approved` 审批记录。

## 3.4 数据模型（Supabase）

核心表：

1. `assistant_sessions`
2. `assistant_messages`
3. `assistant_tool_calls`
4. `assistant_approvals`
5. `assistant_audit_events`

关键字段要求：

1. 所有表保留 `created_at`。
2. `assistant_tool_calls.status` 使用统一状态机。
3. `assistant_audit_events.payload_json` 保存必要上下文快照。

## 3.5 状态机

`draft -> pending_approval -> approved/rejected -> executing -> succeeded/failed`

说明：

1. `read_sql`、`generate_chart_data` 走低风险快速路径，可跳过审批。
2. `create_followup_task` 必须经过 `pending_approval`。

## 3.6 API 设计（FastAPI）

建议端点：

1. `POST /api/assistant/tools/read_sql`
2. `POST /api/assistant/tools/generate_chart_data`
3. `POST /api/assistant/tools/create_followup_task`
4. `POST /api/assistant/approvals/{tool_call_id}/approve`
5. `POST /api/assistant/approvals/{tool_call_id}/reject`
6. `GET /api/assistant/sessions/{session_id}/timeline`

错误码统一：

`VALIDATION_ERROR`、`UNAUTHORIZED`、`FORBIDDEN`、`APPROVAL_REQUIRED`、`SQL_READONLY_VIOLATION`、`SQL_LIMIT_EXCEEDED`、`TOOL_TIMEOUT`、`UPSTREAM_ERROR`、`NOT_FOUND`、`INTERNAL_ERROR`

## 3.7 安全与合规

1. RLS 强制租户隔离，禁止跨租户查询。
2. Tool 白名单机制，拒绝动态任意工具执行。
3. 高风险动作审批必经，默认拒绝策略。
4. 审计日志不可缺失，失败也需落库。

## 3.8 可观测性与稳定性

1. 指标：tool 成功率、审批通过率、平均时延、失败分布。
2. 重试：仅对幂等工具重试 1 次。
3. 超时：单次工具调用超时（如 10s）后返回 `TOOL_TIMEOUT`。

## 3.9 测试方案

1. 单元测试
- SQL 校验器（只读限制、关键字拦截）。
- 参数 schema 校验。
- 状态机合法迁移测试。

2. 集成测试
- 三工具完整链路。
- 审批通过/拒绝分支。
- RLS 隔离测试（跨租户访问应失败）。

3. 前端验收
- 时间线状态可视准确。
- 审批弹窗交互闭环。
- 工具失败有可读反馈。

## 3.10 风险与缓解

1. 风险：模型生成 SQL 不稳定。
- 缓解：SQL 审核器 + 模板化查询优先。

2. 风险：审批步骤影响效率。
- 缓解：仅对写操作审批；低风险读操作直通。

3. 风险：日志量上升带来存储压力。
- 缓解：事件分级保留策略（热数据 30 天，冷归档）。

## 4. 执行建议（评审通过后）

## 4.1 开发顺序

1. 先落库：DDL + RLS + 索引。
2. 再后端：Tool Router + `read_sql`。
3. 再前端：时间线展示。
4. 再补齐：`generate_chart_data`、审批流、`create_followup_task`。
5. 最后：审计回放与压测。

## 4.2 Definition of Done

1. 功能验收标准全部满足。
2. 前后端关键测试通过。
3. 关键指标可观测。
4. 文档与错误码对齐。

---

## 附录 A：本期边界声明

本期重点是验证“受控执行闭环”，不是追求全功能智能体。若 MVP 指标达标，再进入下一阶段：多 Agent 协作、模型分层路由、跨系统自动化编排。
