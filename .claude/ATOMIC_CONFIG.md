# AIGovern Pro - Atomic Integration Config

## 项目概览

**AIGovern Pro** (智管通 AI) 是一款 AI 原生企业级 B 端管理系统

### 核心定位
- 知识问答：RAG + 多轮交互
- 数据查询：自然语言 → SQL/API
- 智能操作：AI 自动执行系统操作
- 经营诊断：指标监控 + 异常预警 + 根因分析

### 技术栈
- **前端**：React 18 + TypeScript + Ant Design Pro + AGUI + A2UI
- **后端**：Java/Go/Python + SpringBoot/Gin/FastAPI + RAG/Vector DB
- **数据库**：PostgreSQL / MongoDB + Supabase
- **AI模型**：Claude API + 向量数据库 + Function Calling

---

## Atomic 工作流程

### 1️⃣ 初始化 (Init)
```bash
./atomic.sh
# 在chat中输入 /init
```

生成：
- `.claude/CLAUDE.md` - 编码规范
- `.claude/AGENTS.md` - 可用agents

### 2️⃣ 研究 (Research)
```
/research-codebase "需求描述"
```

输出到 `research/docs/`

### 3️⃣ 规范 (Spec)
```
/create-spec research/docs/xxx.md
```

输出到 `specs/`

### 4️⃣ 实现 (Implement)
```
/ralph specs/xxx-spec.md
```

自主完成：修改代码、运行测试、生成commit

### 5️⃣ PR (Publish)
```
/gh-create-pr
```

自动生成PR + 描述

---

## 编码规范

### Frontend (React)
- 使用 **TypeScript**（strict mode）
- 组件采用 **函数式 + Hooks**（禁用class）
- 使用 **Ant Design 组件库**
- 状态管理：**Redux Toolkit** / Context API
- 样式：**CSS-in-JS** (styled-components) 或 Tailwind
- API 调用：**TanStack Query** (react-query)

### Backend (Java/Go/Python)
- Java: SpringBoot 3.x + Maven/Gradle
- Go: Gin框架 + GORM
- Python: FastAPI + Pydantic
- 数据库ORM：**Hibernate/Spring Data / GORM / SQLAlchemy**

### 通用规范
- 类型注解强制（TypeScript + Python type hints）
- 函数式编程优先（避免过度设计）
- 早return原则（嵌套≤3层）
- 单元测试覆盖率 ≥ 80%
- 代码审查必须通过 linter/formatter

---

## Sub-Agents 声明

| Agent | 用途 | 触发时机 |
|-------|------|---------|
| codebase-analyzer | 分析代码实现细节 | `/research-codebase` |
| codebase-locator | 定位文件/组件 | `/research-codebase` |
| codebase-pattern-finder | 查找类似实现 | `/research-codebase` |
| codebase-research-analyzer | 深度研究专题 | `/research-codebase` |
| debugger | 调试错误 | `/research-codebase` |

---

## 关键目录

| 目录 | 说明 |
|------|------|
| `frontend/` | React前端应用 |
| `backend/` | 后端服务 |
| `research/docs/` | Atomic生成的研究文档 |
| `specs/` | 技术规范文档 |
| `.claude/` | Claude Code配置 |
| `.atomic/` | Atomic运行时数据 |

---

## 快速命令

### 启动Atomic
```bash
./atomic.sh
```

### 非交互模式
```bash
# 一行命令研究
/Users/wclu/.bun/bin/bun run /Users/wclu/Atomic_Workspace/src/cli.ts \
  chat -a claude -- /research-codebase "某个功能"

# 一行命令实现
/Users/wclu/.bun/bin/bun run /Users/wclu/Atomic_Workspace/src/cli.ts \
  chat -a claude -- /ralph "specs/xxx.md"
```

---

## 最佳实践

### ✅ 做这些
- 使用 `/research-codebase` 分析现有架构
- 在 `/ralph` 前充分review spec
- 为大型重构使用并行研究（多个Terminal）
- 定期 `/gh-create-pr` 提交PR

### ❌ 避免这些
- 不要跳过 `/research-codebase` 直接改代码
- 不要在spec不清晰的情况下运行 `/ralph`
- 不要修改 `.claude/` 配置（由Atomic管理）
- 不要删除 `research/` 和 `specs/` 目录

---

## 常见场景

### 场景1：新增模块（如智能操作引擎v2）
```
1. /research-codebase "研究现有smart-operation模块的架构，设计v2版本"
2. Review research
3. /create-spec research/docs/xxx
4. Review spec
5. /ralph specs/xxx-spec.md
6. /gh-create-pr
```

### 场景2：紧急bug修复
```
1. /research-codebase "DEBUG: [症状]. 找出根因"
2. /create-spec research/docs/bug-xxx
3. /ralph specs/bug-xxx-spec.md
4. /gh-create-pr
```

### 场景3：性能优化
```
1. /research-codebase "性能分析: 列举性能瓶颈和优化方向"
2. 在多个Terminal并行运行 /research-codebase
3. 对比方案后 /create-spec
4. /ralph 最优方案
```

---

## 联系与支持

- **Atomic官方**: https://github.com/flora131/atomic
- **本地文档**: `/Users/wclu/Atomic_Workspace/README.md`
- **设计规范**: `/Users/wclu/Atomic_Workspace/research/docs/v1/`
