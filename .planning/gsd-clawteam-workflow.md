# GSD + ClawTeam 多代理协调工作流

## 概述

集成 **GSD 工作流**（Get Shit Done）与 **ClawTeam 多代理协调框架**，实现 AIGovern Pro 项目初始化的智能并行化执行。

## 核心理念

GSD 工作流的多个阶段可以通过 ClawTeam 的多代理编排进行并行化：

```
GSD 阶段              → ClawTeam 代理映射
─────────────────────────────────────────
质疑/验证 (Questioning)  → Leader Agent (OpenClaw 主进程)
并行研究 (Research)      → Research Agent 1, 2, 3 (并行)
需求定义 (Requirements)  → Requirements Agent (顺序)
路线图创建 (Roadmap)     → Roadmap Agent (顺序)
```

## 部署架构

### 第1阶段：初始化团队（Leader 驱动）

```bash
# Leader（OpenClaw 主进程）启动 ClawTeam 团队
clawteam team spawn-team aigov-gsd -d "Initialize AIGovern Pro via GSD" -n leader

# Leader 进行深度质疑（questioning 阶段）
# - 收集业务需求、技术约束、用户目标
# - 保存到 .planning/PROJECT.md 临时版本
```

### 第2阶段：并行研究（3 个研究代理）

```bash
# Leader 生成 3 个并行研究代理
clawteam spawn --team aigov-gsd \
  --agent-name "researcher-tech" \
  --task "研究 AIGovern Pro 技术栈：现有代码库架构、依赖、工具链"

clawteam spawn --team aigov-gsd \
  --agent-name "researcher-market" \
  --task "研究 AIGovern Pro 市场定位：竞品、用户段、差异化"

clawteam spawn --team aigov-gsd \
  --agent-name "researcher-roadmap" \
  --task "研究 AIGovern Pro 实现路径：技术分解、里程碑、风险"
```

每个研究代理：
- 在独立的 Git worktree + tmux 窗口中运行
- 生成研究文档到 `.planning/research/`
- 通过 inbox 向 Leader 汇报完成状态

### 第3阶段：需求整合（Requirements Agent）

```bash
clawteam spawn --team aigov-gsd \
  --agent-name "requirements-engineer" \
  --task "整合 Leader 质疑 + 3 个研究代理结果 → 生成 .planning/REQUIREMENTS.md"
```

### 第4阶段：路线图创建（Roadmap Agent）

```bash
clawteam spawn --team aigov-gsd \
  --agent-name "roadmap-planner" \
  --task "基于需求定义 → 生成 .planning/ROADMAP.md，包含分阶段目标和执行计划"
```

### 监控面板

```bash
# 实时监控所有代理工作进度
clawteam board attach aigov-gsd

# 或启动 Web 仪表板
clawteam board serve --port 3030
```

## 代理间通信协议

### Inbox 消息格式

代理通过 `clawteam inbox` 发送结构化消息：

```bash
clawteam inbox send aigov-gsd leader \
  "status:complete
   phase:research-tech
   output:.planning/research/tech-stack.md
   summary:Found 18 dependencies, 3 external APIs"
```

### Leader 的协调逻辑

1. **接收** 所有研究代理的完成消息
2. **验证** 输出文件和内容质量
3. **聚合** 多个研究结果
4. **分配** Requirements Agent 任务
5. **等待** Requirements Agent 完成
6. **分配** Roadmap Agent 任务
7. **合并** 所有工件到 `.planning/` 
8. **提交** 最终 Git 提交

## 工作目录隔离

每个代理在独立的 worktree 中运行，确保：

```
.
├── .git                    # Main branch
├── .git/worktrees/
│   ├── aigov-gsd-researcher-tech/
│   │   ├── .planning/
│   │   └── src/
│   ├── aigov-gsd-researcher-market/
│   │   ├── .planning/
│   │   └── src/
│   └── aigov-gsd-requirements-engineer/
│       ├── .planning/
│       └── src/
└── main worktree
    ├── .planning/
    └── src/
```

- 每个 worktree 是完整的代码库副本
- 代理可在不干扰他人的情况下修改文件
- Leader 负责合并结果回 main 分支

## 与 OpenClaw 集成

### 方式 1：自动驱动（推荐）

向 OpenClaw 发起提示：

```
Use ClawTeam to initialize AIGovern Pro project via GSD workflow:

1. 作为 Leader Agent，进行深度质疑阶段（questioning）
   - 收集业务需求、技术约束、用户目标
   - 保存临时数据

2. 生成 3 个并行研究代理（Research Agents）
   - 研究技术栈和架构
   - 研究市场定位和竞品
   - 研究实现路径和风险

3. 生成需求整合代理（Requirements Agent）
   - 收集所有研究结果
   - 生成 .planning/REQUIREMENTS.md

4. 生成路线图规划代理（Roadmap Agent）
   - 基于需求创建 .planning/ROADMAP.md
   - 定义分阶段执行计划

5. 监控所有代理进度，必要时干预

Use clawteam commands for spawning and monitoring. Each agent should report progress via inbox.
```

OpenClaw 会：
- 自动创建 ClawTeam 团队
- 根据提示自主生成和管理代理
- 通过 `clawteam inbox` 进行agent间通信
- 汇聚所有结果

### 方式 2：手动驱动

执行 [gsd-clawteam-init.sh](./gsd-clawteam-init.sh) 脚本，逐步启动团队。

## 与标准 GSD 流程的适配

### 保留的 GSD 特性

✅ **Questioning Phase** — Leader Agent 负责深度质疑  
✅ **Research Phase** — 3 个并行 Research Agents  
✅ **Requirements Definition** — Requirements Agent 整合  
✅ **Roadmap Generation** — Roadmap Agent 创建分阶段计划  
✅ **State Management** — 最终生成 `.planning/STATE.md`  
✅ **Git Commits** — Leader 负责原子化提交  

### 增强的特性

✨ **真正的并行化** — 研究阶段 3 个代理同时运行  
✨ **异步协调** — 通过 inbox 而非同步 RPC  
✨ **工作隔离** — 每个代理独立 worktree（无冲突）  
✨ **可观测性** — tmux board 实时监控  
✨ **可扩展性** — 轻易添加更多专项研究代理  

## 成功标志

工作流完成后，产生：

```
.planning/
├── PROJECT.md                # 项目定义（Leader 整合）
├── REQUIREMENTS.md          # 需求文档（Requirements Agent）
├── ROADMAP.md              # 路线图（Roadmap Agent）
├── STATE.md                # 项目状态
├── config.json             # 工作流配置
├── research/
│   ├── tech-stack.md       # Research Agent 1 输出
│   ├── market-analysis.md  # Research Agent 2 输出
│   └── implementation-path.md # Research Agent 3 输出
└── git commits
    ├── "docs: GSD questioning phase complete"
    ├── "docs: research phase results aggregated"
    ├── "docs: requirements defined"
    └── "docs: roadmap created"
```

## 运行命令参考

### 启动完整工作流

```bash
# 方式 A：通过 OpenClaw（自动）
openclaw "use clawteam to initialize AIGovern Pro via GSD..."

# 方式 B：运行初始化脚本（手动）
cd /Users/wclu/AIGovern_Pro
bash .planning/gsd-clawteam-init.sh
```

### 监控进度

```bash
# 实时 tmux 面板
clawteam board attach aigov-gsd

# Web 仪表板
clawteam board serve --port 3030

# 查看 inbox 消息
clawteam inbox list aigov-gsd leader
```

### 查看代理工作

```bash
# 列出所有代理
clawteam team list aigov-gsd

# 进入特定代理的 tmux 窗口
tmux select-window -t aigov-gsd:researcher-tech

# 查看代理日志
clawteam task list aigov-gsd --owner researcher-tech
```

## 故障恢复

### 代理失败

```bash
# 检查失败原因
clawteam task show aigov-gsd researcher-tech

# 重新启动代理
clawteam spawn --team aigov-gsd \
  --agent-name "researcher-tech" \
  --task "..."
```

### 重置工作流

```bash
# 清理整个团队（包括所有 worktrees）
clawteam team delete aigov-gsd

# 重新开始
cd /Users/wclu/AIGovern_Pro
bash .planning/gsd-clawteam-init.sh
```

## 下一步

1. ✅ 运行 `gsd-clawteam-init.sh` 启动多代理团队
2. ⏳ 监控 3 个研究代理的进度
3. ✅ 等待需求整合完成
4. ✅ 等待路线图规划完成
5. 🚀 进入 Phase 1 执行（基于生成的 ROADMAP.md）

---

**Last Updated**: 2026-04-17  
**Status**: Ready to deploy  
**Integration**: GSD + ClawTeam + OpenClaw
