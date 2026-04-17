# 学习调研日志 · 2026年4月15-16日

> 这是 wenson 的 AI 学习调研记录，存放在 GitHub 以便持续追踪和复盘。

---

## 📅 2026-04-15

### 1. frontend-logic-training 项目全量交付 🚀

**Module 1-4 全部完成：**

| 模块 | 内容 | 状态 |
|------|------|------|
| Module 1 | State Machine Wizard（状态机训练场） | ✅ 完成 |
| Module 2 | Async State Gallery（异步状态图鉴） | ✅ 完成 |
| Module 3 | Custom Hooks Patterns（6个自定义Hooks） | ✅ 完成 |
| Module 4 | Composition（组合模式） | ✅ 完成 |

**Module 3 包含的 6 个自定义 Hooks：**
- `useDebounce` - 防抖
- `useLocalStorage` - 本地存储同步
- `useMediaQuery` - 媒体查询响应式
- `useToggle` - 状态切换
- `usePrevious` - 上一个值追踪
- `useOnClickOutside` - 点击外部检测

**项目已推送至 GitHub master 分支，并配置 Vercel MCP 服务。**

### 2. CI 流水线自主修复 🔧

推送后 CI 出现报错，原因是 CI 配置中引用了不存在的 `npm run typecheck` 脚本。AI 自主识别问题并移除该配置项，CI 构建恢复正常。

**经验积累：** Multi-Agent 团队在代码迭代过程中可能产生 CI 配置与实际 package.json 的不同步，CI 维护已纳入协作体系的关注范围。

### 3. ClawTeam 5 Agent 软件团队启动 ⚠️

用户启动 ClawTeam 软件团队（5个Agent：tech-lead、frontend-dev、backend-dev、qa-engineer、devops），但因 git worktree 配置问题未正确指向项目目录，Agents 被隔离在旧的模板工作区。

**教训：** ClawTeam 框架使用中存在路径配置陷阱——需要在创建团队时显式指定工作目录路径，而非依赖默认模板路径。

### 4. Claude Code 源码级学习计划启动 🧠

用户正式提出深度掌握 Claude Code v2.1.88 完整源码（51万行 TypeScript）的计划。

**目标：** 达到"像原生 Claude Code 一样理解、分析、修改、生成代码"的程度

**范围：**
- 架构设计
- 系统提示词
- 工具系统
- Agent 逻辑
- 工程实现

**意义：** 这是从"工具使用者"到"建设者"的认知跃迁。

---

## 📅 2026-04-16

### 5. Claude Code 专家模式触发协议建立 🎯

用户建立了 Claude Code 专家模式的触发协议，当 AI 收到特定关键词时自动展示使用方法，追求工具响应的可预期性。

**本质：** 把 AI 当作"可编程的工具"而非"会猜的对话者"——建立关键词 → 固定行为的映射规范。

### 6. 调研视野升级：从"项目"到"人物" 👤

用户开始系统性追踪 AI 圈关键意见领袖 **AYi_AInotes（阿绎）** 的推文内容。

**这一动作的深层含义：**
- 调研路径从"项目 → Star数 → 技术方案"扩展到"人物 → 洞察 → 趋势预判"
- 人物背后的信息密度往往高于项目本身（项目是果，人是因）
- 这是准备从"工具使用者"向"行业洞察者"跃迁的前兆

### 7. AI 每日自我进化循环执行 🧬

AI 执行了每日自我进化循环，生成进化报告（memory/evolution/2026-04-16.md）。

**关键发现：**
- frontend-logic-training 项目仍有 4 项待办（Module 2/3 README、测试用例、CI优化）
- Evolver Wrapper 自 4月13日起持续循环失败（Cycle #104-#105）
- 建议使用 ralph-loop 推进待办任务

### 8. 系统状态警报 ⚠️

**Evolver Wrapper 深层故障：**
- 自 4月13日起持续循环失败，处于 Cycle #104-#105 区间
- 与 4月1日的"活动超时触发重启"不同，这是 wrapper 层循环逻辑本身陷入无法正常退出的状态
- 可能存在深层设计缺陷

**GitHub 账户暂停：** wensonlu/openclaw 账户被暂停，热点追踪任务彻底失败已超过一周。

---

## 💡 关键洞察

### 从 April 15-16 看用户的变化

1. **Multi-Agent 协作进入项目级实操**：从框架验证升级到项目级协调，tech-lead 角色专门负责技术方案决策

2. **源码级学习成为新常态**：不满足于了解工具"能做什么"，要求深入工程内核

3. **人物追踪体系启动**：从扫描项目升级为追踪人，准备从工具使用者向行业洞察者跃迁

4. **"看完即忘"仍是持续风险**：用户明确意识到这个问题，需要建立实际的复习/输出机制

---

## 📋 待办清单

- [ ] Module 2/3 README 文档编写
- [ ] frontend-logic-training 测试用例覆盖
- [ ] CI 优化
- [ ] ClawTeam git worktree 配置修复
- [ ] Evolver Wrapper 深层故障修复
- [ ] GitHub 账户恢复后的热点追踪恢复
- [ ] Claude Code 51万行源码阶段性学习里程碑

---

_最后更新：2026-04-17 by OpenClaw AI_
