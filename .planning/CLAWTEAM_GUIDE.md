# ClawTeam + GSD 多代理协调工作流

## 快速开始

### 方式 1：完全自动化（推荐 OpenClaw 用户）

在 OpenClaw 中执行：

```
Use ClawTeam to initialize AIGovern Pro via GSD workflow.

[Copy from .planning/clawteam-gsd-prompt.md]
```

OpenClaw 会自动：
1. ✅ 执行深度质疑阶段
2. ✅ 生成 3 个并行研究代理
3. ✅ 整合需求
4. ✅ 创建路线图
5. ✅ 提交所有结果

### 方式 2：手动驱动（交互式）

```bash
cd /Users/wclu/AIGovern_Pro
bash .planning/gsd-clawteam-init.sh
```

脚本会引导你完成每个阶段，包括：
- 深度质疑的交互提示
- 研究代理生成
- 进度监控
- 结果收集

### 方式 3：编程化执行（Python）

```bash
python3 .planning/gsd-clawteam-orchestrator.py [--auto] [--timeout 600]
```

选项：
- `--auto` — 完全自动运行，无交互提示
- `--timeout 600` — 等待代理完成的超时（秒）

---

## 文件说明

### 📄 核心文档

| 文件 | 用途 |
|------|------|
| `gsd-clawteam-workflow.md` | 完整架构设计和工作原理说明 |
| `clawteam-gsd-prompt.md` | OpenClaw 友好的提示词模板 |
| `gsd-clawteam-init.sh` | 手动执行脚本（bash） |
| `gsd-clawteam-orchestrator.py` | 编程化执行脚本（Python） |

### 📊 生成的工件

执行后，`.planning/` 目录会包含：

```
.planning/
├── PROJECT.md              # 项目定义（Core Value、约束、背景）
├── REQUIREMENTS.md         # 需求范围（验证、活跃、排除）
├── ROADMAP.md             # 阶段路线图（Phase 1, 2, 3+）
├── STATE.md               # 项目状态总结
├── config.json            # GSD 工作流配置
├── research/
│   ├── tech-stack.md      # 技术栈研究
│   ├── market-analysis.md # 市场定位研究
│   └── implementation-path.md # 实现路径研究
└── git commits
    └── docs: GSD initialization complete
```

---

## 工作流程详解

### Phase 1：质疑（Leader 驱动）

Leader Agent（OpenClaw 主进程）回答关键问题：

```
1. Core Business Value: AIGovern Pro 最重要的事情是什么？
2. User Segment: 主要用户是谁？他们的痛点是什么？
3. Technical Constraints: 有哪些硬约束？
4. MVP Scope: Phase 1 应该交付什么？
```

结果存储在 `.planning/PROJECT.md` 的 "Context" 部分。

### Phase 2：并行研究（3 个研究代理）

**Researcher-Tech Agent**
- 分析现有代码库结构
- 记录技术栈、依赖关系
- 输出：`.planning/research/tech-stack.md`

**Researcher-Market Agent**
- 定义目标用户和竞争力
- 分析市场趋势
- 输出：`.planning/research/market-analysis.md`

**Researcher-Impl Agent**
- 分解"四大核心能力"为技术组件
- 评估风险和里程碑
- 输出：`.planning/research/implementation-path.md`

所有 3 个代理**并行运行**，通过独立的 Git worktree 隔离。

### Phase 3：需求整合（Requirements Agent）

Requirements-Engineer Agent：
- 读取所有研究结果
- 整合质疑阶段的输出
- 结构化为：Validated / Active / Out of Scope
- 输出：`.planning/REQUIREMENTS.md`

### Phase 4：路线图规划（Roadmap Agent）

Roadmap-Planner Agent：
- 基于需求设计分阶段计划
- 定义 Phase 1、2、3+ 的交付物
- 为每个阶段设定成功标准
- 输出：`.planning/ROADMAP.md`

### Phase 5：结果汇聚（Leader 负责）

Leader：
- ✅ 验证所有输出文件
- ✅ 创建 `.planning/STATE.md` 状态总结
- ✅ `git add .planning/ && git commit`
- ✅ 准备进入 Phase 1 执行

---

## 与 GSD 标准流程的关系

### ✅ 保留的 GSD 特性

```
GSD 标准流程          ClawTeam 集成后
─────────────────────────────────────────
Questioning    →  Leader Agent 执行
Research       →  3 个并行代理执行
Requirements   →  Requirements Agent 整合
Roadmap        →  Roadmap Agent 规划
State & Commit →  Leader 负责最终化
```

所有生成的工件（PROJECT.md、REQUIREMENTS.md、ROADMAP.md）与标准 GSD 兼容。

### 🚀 增强的特性

| 增强 | 说明 |
|-----|------|
| **真正并行** | 研究阶段 3 个代理同时执行，而非顺序 |
| **工作隔离** | 每个代理在独立 Git worktree，无冲突 |
| **异步协调** | 通过 inbox 消息而非同步 RPC 调用 |
| **可观测性** | tmux board 实时监控所有代理进度 |
| **容错性** | 单个代理失败不影响其他代理 |

---

## 监控与调试

### 实时监控

启动 tmux 面板查看所有代理：

```bash
clawteam board attach aigov-gsd

# 或启动 Web 仪表板
clawteam board serve --port 3030
```

### 查看代理状态

```bash
# 列出所有代理
clawteam team list aigov-gsd

# 查看 Leader inbox（代理汇报消息）
clawteam inbox list aigov-gsd leader

# 查看特定代理的任务
clawteam task show aigov-gsd researcher-tech
```

### 故障排查

**代理未启动**
```bash
# 检查 OpenClaw 是否运行
openclaw --version

# 检查 tmux session
tmux ls

# 手动重启代理
clawteam spawn --team aigov-gsd \
  --agent-name researcher-tech \
  --task "..."
```

**超时等待**
```bash
# 检查 inbox 消息
clawteam inbox list aigov-gsd leader

# 查看代理日志
tmux capture-pane -t aigov-gsd:researcher-tech -p
```

**重置并重新开始**
```bash
# 删除整个团队（包括所有 worktrees）
clawteam team delete aigov-gsd

# 重新初始化
bash .planning/gsd-clawteam-init.sh
```

---

## 命令参考

### ClawTeam 命令

```bash
# 团队管理
clawteam team spawn-team TEAM_NAME -d "Description" -n leader
clawteam team delete TEAM_NAME
clawteam team list TEAM_NAME

# 代理生成
clawteam spawn --team TEAM_NAME --agent-name AGENT_NAME --task "TASK_DESC"

# 通信
clawteam inbox list TEAM_NAME RECIPIENT
clawteam inbox send TEAM_NAME RECIPIENT "message"

# 任务管理
clawteam task list TEAM_NAME
clawteam task show TEAM_NAME AGENT_NAME

# 监控
clawteam board attach TEAM_NAME
clawteam board serve --port PORT
```

### GSD 后续命令

初始化完成后，继续 GSD 工作流：

```bash
# 规划 Phase 1（详细计划）
/gsd-plan-phase 1

# 执行 Phase 1（根据计划构建）
/gsd-execute-phase 1

# 验证 Phase 1 完成
/gsd-verify-phase 1
```

---

## 技术架构

### 多代理隔离

每个代理在独立的 Git worktree 中运行：

```
.git/
├── HEAD (main branch)
└── worktrees/
    ├── aigov-gsd-researcher-tech/
    │   ├── .git
    │   ├── .planning/
    │   ├── frontend/
    │   ├── backend/
    │   └── [fully independent codebase]
    ├── aigov-gsd-researcher-market/
    │   └── [fully independent codebase]
    └── aigov-gsd-requirements-engineer/
        └── [fully independent codebase]
```

好处：
- 🔒 **真正隔离** — 代理无法互相干扰
- 🔄 **无冲突合并** — 结果合并回 main 清晰
- 🚀 **并行性** — 多代理真正同时运行

### Agent 间通信

代理通过结构化 inbox 消息通信：

```bash
# 工作代理向 Leader 汇报
clawteam inbox send aigov-gsd leader \
  "status:complete|phase:research-tech|files:tech-stack.md"

# Leader 分配新任务给代理
clawteam inbox send aigov-gsd requirements-engineer \
  "task:integrate-research|sources:research/*md"
```

### 与 OpenClaw 集成

```
OpenClaw 主进程 (Leader Agent)
    ↓ 
使用 ClawTeam 生成工作代理
    ↓
每个工作代理 = 独立 OpenClaw 实例 (tmux 窗口)
    ↓
工作代理执行任务 → 写入 .planning/
    ↓
通过 inbox 向 Leader 汇报
    ↓
Leader 聚合结果 → 最终化 PROJECT.md/REQUIREMENTS.md/ROADMAP.md
```

---

## 从这里开始

### 步骤 1：选择执行方式

- **自动（推荐）** → 在 OpenClaw 中粘贴 `.planning/clawteam-gsd-prompt.md`
- **手动** → `bash .planning/gsd-clawteam-init.sh`
- **编程化** → `python3 .planning/gsd-clawteam-orchestrator.py --auto`

### 步骤 2：监控执行

```bash
clawteam board attach aigov-gsd
```

### 步骤 3：验证结果

```bash
ls -lh .planning/PROJECT.md .planning/REQUIREMENTS.md .planning/ROADMAP.md
wc -l .planning/research/*.md
```

### 步骤 4：进入 Phase 1

```bash
/gsd-plan-phase 1
```

---

## FAQ

**Q: 代理之间如何协调的？**  
A: 通过 ClawTeam 的 inbox 系统。代理发送结构化消息，Leader 根据完成状态分配下一步任务。

**Q: 研究代理是否访问同一代码库？**  
A: 是的，但在独立的 Git worktree 中，所以无文件冲突。

**Q: 如果一个代理失败了怎么办？**  
A: 其他代理继续运行。可以单独重启失败的代理而不影响整体。

**Q: 如何自定义代理数量或角色？**  
A: 编辑 `.planning/gsd-clawteam-init.sh` 或 `gsd-clawteam-orchestrator.py`，添加新的 `clawteam spawn` 命令。

**Q: 生成的文件格式与标准 GSD 兼容吗？**  
A: 完全兼容。PROJECT.md、REQUIREMENTS.md、ROADMAP.md 遵循标准 GSD 模板。

---

**Last Updated**: 2026-04-17  
**Version**: 1.0  
**Status**: Ready to deploy
