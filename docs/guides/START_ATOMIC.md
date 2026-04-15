# 🚀 Atomic + AIGovern_Pro 快速开始

## ⚡ 30秒启动

```bash
# 1. 进入项目目录
cd ~/AIGovern_Pro

# 2. 启动Atomic chat
./atomic.sh

# 在chat中使用命令：
/init                                    # 生成项目context
/research-codebase "你的需求"             # 并行研究
/create-spec research/docs/xxx.md         # 生成规范
/ralph "specs/xxx-spec.md"                # 自主实现
/gh-create-pr                             # 提交PR
```

---

## 📋 核心命令速查

| 命令 | 作用 | 输出 |
|------|------|------|
| `/init` | 生成CLAUDE.md + AGENTS.md | context files |
| `/research-codebase "..."` | 并行研究（5个sub-agents） | research/docs/ |
| `/create-spec path` | 转化为技术规范 | specs/ |
| `/ralph "..."` | 自主实现代码 | commits + changes |
| `/gh-create-pr` | 生成PR | GitHub |
| `/clear` | 清空消息 | — |
| `/help` | 查看所有命令 | — |

---

## 🎯 典型工作流

### 新功能开发
```
研究 → 规范 → 实现 → PR

步骤1: 理解现有架构
  /research-codebase "分析前端中的知识问答模块，研究如何扩展"

步骤2: 写规范
  /create-spec research/docs/xxx

  ⚠️  仔细review spec，这是和AI的合同

步骤3: 执行
  /ralph specs/xxx-spec.md

  等待agent自主：
  - 修改代码
  - 运行测试
  - 生成commit

步骤4: 提交
  /gh-create-pr
```

### Bug 修复
```
/research-codebase "DEBUG: [症状]. 找根因和修复方案"
/create-spec research/docs/bug
/ralph specs/bug-spec.md
/gh-create-pr
```

### 性能优化
```
# 并行研究3个方案
Terminal 1: /research-codebase "前端性能：React.memo优化方案"
Terminal 2: /research-codebase "前端性能：虚拟滚动列表方案"
Terminal 3: /research-codebase "前端性能：增量加载方案"

# 对比后择优
/create-spec research/docs/optimal
/ralph specs/optimal-spec.md
```

---

## 🛠️ 环境检查

```bash
# 检查所有依赖
bun --version          # ✓ 1.3.11+
claude --version       # ✓ Claude Code CLI
git --version          # ✓ Git

# 检查Atomic
ls -la ~/Atomic_Workspace/src/cli.ts
```

---

## 📁 项目结构

```
AIGovern_Pro/
├── frontend/                    # React应用
├── backend/                     # 后端服务
├── research/docs/               # Atomic研究（自动生成）
├── specs/                       # 技术规范（自动生成）
├── .claude/
│   ├── CLAUDE.md               # 编码规范
│   ├── AGENTS.md               # agents声明
│   └── ATOMIC_CONFIG.md        # Atomic配置
├── atomic.sh                   # 启动脚本 ✨
├── run-atomic.sh               # 交互式启动
└── ATOMIC_SETUP.md             # 详细指南
```

---

## ⚠️ 常见问题

### Q: Bun找不到？
```bash
export PATH="/Users/wclu/.bun/bin:$PATH"
source ~/.zshrc
```

### Q: Claude Code CLI找不到？
```bash
# 检查安装
claude --version

# 如果失败，登录
claude
```

### Q: 运行太慢？
- Atomic使用Claude Opus 4.6（功能强大但较耗时）
- 在spec中指定`--model claude-haiku-4-5`使用轻量版本
- 或使用OpenCode/Copilot agent（在./atomic.sh中选择）

### Q: 生成的代码质量差？
- ✅ spec需要详细（不能模糊）
- ✅ 最好指定"参考file1.ts和file2.ts中的模式"
- ✅ 在/ralph前review spec

---

## 🎓 进阶用法

### 自定义Agent
在`.claude/AGENTS.md`中声明新agent：
```yaml
name: data-migration-expert
description: 数据迁移和ETL专家
capabilities: [database, migration, etl]
```

### 配置Vercel部署
在spec中指定：`部署到vercel，配置环境变量xxx`

### MCP Server集成
编辑`.claude/AGENTS.md`配置MCP servers

---

## 🚀 下一步

1. **立即启动**：
   ```bash
   cd ~/AIGovern_Pro
   ./atomic.sh
   ```

2. **生成项目context**：
   在chat中输入 `/init`

3. **研究第一个功能**：
   ```
   /research-codebase "需求"
   ```

4. **查看详细指南**：
   ```bash
   cat ATOMIC_SETUP.md
   cat .claude/ATOMIC_CONFIG.md
   ```

---

## 📚 参考资源

| 资源 | 位置 |
|------|------|
| Atomic官方文档 | `~/Atomic_Workspace/README.md` |
| 编码规范 | `~/Atomic_Workspace/CLAUDE.md` |
| 架构设计（V2重构） | `~/Atomic_Workspace/research/docs/v1/` |
| 本项目指南 | `./ATOMIC_SETUP.md` |
| Atomic配置 | `./.claude/ATOMIC_CONFIG.md` |

---

**🎉 You're all set! Happy coding!**

有问题？在chat中使用 `/help` 查看命令列表。
