# Agent Skills 可视化仪表盘 — 设计文档

## 1. 项目概述

**项目名称：** `@agent-skills/dashboard`

**定位：** AI Coding 工作流可视化工具包，帮助 AI Agent 理解技能关系、追踪项目阶段、推荐下一步行动。

**核心价值：** 把散落的 SKILL.md 文件转化为可查询的结构化知识图谱，AI 可以基于此做智能决策，人类可以预览技能地图和项目状态。

---

## 2. 方案选择

**选择：方案 C — Monorepo**

| 包 | 说明 |
|----|------|
| `@agent-skills/core` | TypeScript 纯数据解析层，无 UI 依赖 |
| `@agent-skills/react` | React 组件层，可选 import |

**理由：**
- AI 需要轻量数据查询接口，UI 是附加能力
- 解耦后 AI 和人类需求各自满足
- 未来扩展 Vue/Angular wrapper 方便

---

## 3. 技术栈

- **语言：** TypeScript 5.x
- **包管理：** pnpm（workspace monorepo）
- **React 版本：** 18.x（仅 react 包）
- **构建工具：** tsup（快速打包，输出 ESM + CJS + types）
- **测试：** Vitest

---

## 4. 包设计

### 4.1 `@agent-skills/core`

#### 数据结构

```typescript
// 技能节点
interface SkillNode {
  id: string;                    // e.g. "spec-driven-development"
  name: string;                  // e.g. "Spec Driven Development"
  description: string;
  phase: SkillPhase;             // define | plan | build | verify | review | ship
  triggers: string[];             // 触发关键词
  triggersStyle: 'auto' | 'manual'; // 自动触发还是手动调用
  dependsOn: string[];           // 前置技能
  relatedSkills: string[];       // 相关技能
  keywords: string[];            // 搜索关键词
  filePath: string;              // SKILL.md 路径
}

// 项目追踪
interface ProjectState {
  id: string;
  name: string;
  currentPhase: SkillPhase;
  completedSkills: string[];
  blockedBy: string[];           // 当前阻塞项
}

// 技能图谱
interface SkillGraph {
  nodes: SkillNode[];
  edges: { from: string; to: string; type: 'depends' | 'relates' }[];
}
```

#### 核心 API

```typescript
// 初始化
function createSkillGraph(skillsRoot: string): SkillGraph;

// 查询
function findForPhase(phase: SkillPhase): SkillNode[];
function findForTask(task: string): SkillNode[];
function getSequence(targetPhase: SkillPhase): SkillNode[];
function recommendNext(currentPhase: SkillPhase, context: string): SkillNode[];

// 项目追踪
function createProject(name: string): ProjectState;
function updateProjectState(state: ProjectState, completedSkill: string): ProjectState;
function getBlockedSkills(state: ProjectState): SkillNode[];
```

### 4.2 `@agent-skills/react`

#### 组件

| 组件 | 说明 |
|------|------|
| `<SkillMap />` | 技能关系图，可视化技能阶段和依赖 |
| `<ProjectTracker />` | 项目阶段追踪面板 |
| `<SkillCard />` | 单个技能详情卡片 |
| `<PhaseProgress />` | 当前阶段进度指示器 |

```tsx
// SkillMap
<SkillMap
  graph={graph}
  currentPhase="plan"
  onSkillClick={(skill) => console.log(skill)}
/>

// ProjectTracker
<ProjectTracker
  project={projectState}
  graph={graph}
  onSkillComplete={(skillId) => handleComplete(skillId)}
/>
```

---

## 5. 解析逻辑

### SKILL.md 解析

每个 SKILL.md 的 `description` 字段包含触发关键词，core 包提取并建立索引：

```
"Discovers and invokes agent skills. Use when starting a session 
or when you need to discover which skill applies to the current task."
→ triggers: ["discover", "invoke", "starting a session", "which skill applies"]
```

### 阶段判断

根据 SKILL.md 路径推断阶段：
- `skills/idea-refine` → `define`
- `skills/spec-driven-development` → `define`
- `skills/planning-and-task-breakdown` → `plan`
- `skills/incremental-implementation` → `build`
- ...以此类推

---

## 6. 输出格式

### 机器可读输出（AI 用）

```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "recommendations": [
    { "skill": "planning-and-task-breakdown", "reason": "当前处于 define 阶段，需要拆解任务" }
  ]
}
```

### 人类可读输出（React 组件预览）

- 技能地图：D3.js 力导向图，展示 20 个节点及其依赖关系
- 阶段面板：Kanban 风格，6 个阶段列，当前项目状态高亮
- 技能卡片：弹窗/侧边栏，展示技能详情和推荐用法

---

## 7. 目录结构

```
agent-skills-dashboard/
├── packages/
│   ├── core/
│   │   ├── src/
│   │   │   ├── parser.ts          # SKILL.md 解析
│   │   │   ├── graph.ts           # 图谱构建
│   │   │   ├── query.ts           # 查询 API
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── react/
│       ├── src/
│       │   ├── components/
│       │   │   ├── SkillMap.tsx
│       │   │   ├── ProjectTracker.tsx
│       │   │   ├── SkillCard.tsx
│       │   │   └── PhaseProgress.tsx
│       │   ├── hooks/
│       │   │   └── useSkillGraph.ts
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
├── pnpm-workspace.yaml
├── package.json
└── README.md
```

---

## 8. 优先级排序（实现顺序）

| 阶段 | 任务 | 理由 |
|------|------|------|
| 1 | core 包基础结构 + 解析器 | 数据层是根基 |
| 2 | core 包图谱构建 + 查询 API | 核心逻辑 |
| 3 | React 组件 SkillMap | 最直观的价值展示 |
| 4 | React 组件 ProjectTracker | 项目追踪能力 |
| 5 | 完整 README + 使用示例 | 开源必需 |
| 6 | CI/CD + npm 发布 | 发版流程 |

---

## 9. 开源准备

- **License：** MIT
- **npm scope：** `@agent-skills`
- **仓库：** GitHub（基于 `addyosmani/agent-skills` fork 或新建独立仓库）
- **CI：** GitHub Actions（测试 + 发布）
- **文档：** README.md + 在线 demo page

---

## 10. 成功标准

1. AI Agent import 后调用 `createSkillGraph()` 能在 100ms 内返回结构化图谱
2. React 组件能渲染出清晰可交互的技能关系图
3. npm 包能被 Claude Code / Cursor 等 AI Coding 工具通过 `import` 接入
4. README 有完整的 AI Agent 接入示例（5 行代码以内）

---

*文档创建时间：2026-04-22*
