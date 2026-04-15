# Atomic CLI 集成指南

## 快速开始

### 1. 启动 Atomic CLI
```bash
# 设置bun路径
export PATH="/Users/wclu/.bun/bin:$PATH"

# 进入项目目录
cd ~/AIGovern_Pro

# 启动Claude Code agent chat
bun run ~/Atomic_Workspace/src/cli.ts chat -a claude

# 或者用OpenCode
bun run ~/Atomic_Workspace/src/cli.ts chat -a opencode

# 或者用GitHub Copilot
bun run ~/Atomic_Workspace/src/cli.ts chat -a copilot
```

### 2. 核心命令

在Atomic chat会话中使用以下命令：

| 命令 | 说明 |
|------|------|
| `/init` | 生成 CLAUDE.md 和 AGENTS.md（codebase context） |
| `/research-codebase "需求描述"` | 使用sub-agents并行研究codebase |
| `/create-spec path/to/research` | 将研究转化为技术规范 |
| `/ralph "prompt或spec路径"` | 自主实现（可pause/resume） |
| `/gh-create-pr` | 自动commit + push + 创建PR |
| `/help` | 查看所有可用命令 |

### 3. AIGovern_Pro 开发工作流

#### 步骤1：初始化项目上下文
```
进入chat → /init → 等待sub-agents分析codebase
```
这会生成：
- `.claude/CLAUDE.md` - 项目规范与编码指南
- `.claude/AGENTS.md` - 可用的sub-agents声明

#### 步骤2：研究新功能需求
```
/research-codebase "需要在AIGovern_Pro中实现的功能"

例如：
/research-codebase "研究如何在前端集成新的知识问答模块，需要支持流式回复"
```

输出：
- `research/docs/` - 多个研究文档

#### 步骤3：创建技术规范
```
/create-spec research/docs/2026-03-31-knowledge-qa-research.md

输出：specs/knowledge-qa-spec.md
```

#### 步骤4：执行实现
```
/ralph specs/knowledge-qa-spec.md

等待agent自主完成：
- 修改代码
- 运行测试
- 生成commit message
```

#### 步骤5：提交PR
```
/gh-create-pr

生成：
- Git commit + push
- GitHub PR（自动生成PR描述）
```

---

## AIGovern_Pro 项目结构

```
AIGovern_Pro/
├── frontend/               # React + Ant Design 前端
│   ├── src/
│   │   ├── components/     # UI组件
│   │   ├── pages/          # 页面
│   │   ├── services/       # API调用
│   │   └── types/          # TypeScript类型
│   └── package.json
│
├── backend/                # Java/Go/Python 后端
│   ├── api/
│   ├── services/
│   ├── models/
│   └── ...
│
├── research/               # Atomic研究文档（自动生成）
├── specs/                  # 技术规范（自动生成）
├── .claude/                # Claude Code 配置
├── .atomic/                # Atomic运行时数据
├── CLAUDE.md               # 编码规范和上下文
├── AGENTS.md               # 可用agents声明
└── README.md
```

---

## 典型场景

### 场景1：添加新的数据查询模块

```
1. /research-codebase "分析现有的data-query模块架构，研究如何扩展支持图表可视化"

2. /clear
   /create-spec research/docs/xxx-data-query-research.md

3. Review spec → /clear
   /ralph "使用spec实现可视化图表支持"

4. /gh-create-pr
```

### 场景2：修复已知Bug

```
/research-codebase "Debug: [bug description]. 查找根因并提出修复方案"

/create-spec research/docs/xxx-debug.md

/ralph specs/xxx-debug-spec.md

/gh-create-pr
```

### 场景3：大规模重构（如认证系统升级）

```
# 并行研究多个方案
Terminal 1: /research-codebase "Research: 迁移到OAuth 2.0的架构方案"
Terminal 2: /research-codebase "Research: 迁移到JWT的架构方案"
Terminal 3: /research-codebase "Research: 保持现状的增强方案"

# 创建多个spec并在不同分支实现
git checkout -b auth-oauth && /ralph specs/oauth-spec.md
git checkout -b auth-jwt && /ralph specs/jwt-spec.md
git checkout -b auth-enhance && /ralph specs/enhance-spec.md

# Review后择优merge
```

---

## 快捷命令别名

在 `~/.zshrc` 中添加：

```bash
# Atomic CLI快捷方式
alias atomic-aigovern='bun run ~/Atomic_Workspace/src/cli.ts chat -a claude'
alias atomic-research='bun run ~/Atomic_Workspace/src/cli.ts chat -a claude -- /research-codebase'
alias atomic-spec='bun run ~/Atomic_Workspace/src/cli.ts chat -a claude -- /create-spec'
alias atomic-impl='bun run ~/Atomic_Workspace/src/cli.ts chat -a claude -- /ralph'
```

然后可以用：
```bash
atomic-aigovern
# 在chat中输入 /research-codebase "..."
```

---

## Troubleshooting

### 问题1：Bun命令找不到
```bash
# 方案1：添加PATH
export PATH="/Users/wclu/.bun/bin:$PATH"

# 方案2：使用完整路径
/Users/wclu/.bun/bin/bun run ...
```

### 问题2：Atomic找不到Claude Code
确保Claude Code已安装并认证：
```bash
claude --version
# 如果失败，运行 claude 进行登录
```

### 问题3：GPU内存不足
Atomic子agents使用Claude Opus 4.6，可能很耗内存。
- 启用操作系统交换空间
- 或在spec中指定`--model claude-haiku-4-5` 使用较小模型

---

## 下一步

1. **启动Atomic chat**：
   ```bash
   /Users/wclu/.bun/bin/bun run ~/Atomic_Workspace/src/cli.ts chat -a claude
   ```

2. **生成项目context**：
   在chat中输入：`/init`

3. **开始第一个功能开发**：
   ```
   /research-codebase "在AIGovern_Pro中实现XXX功能"
   ```

---

## 参考资源

- Atomic官方README: `/Users/wclu/Atomic_Workspace/README.md`
- CLAUDE.md规范: `/Users/wclu/Atomic_Workspace/CLAUDE.md`
- 研究文档集: `/Users/wclu/Atomic_Workspace/research/docs/`
- 架构规范集: `/Users/wclu/Atomic_Workspace/research/docs/v1/`（V2重构设计）
