# ClawTeam AI-Driven GSD Initialization Prompt

## For OpenClaw Users

Copy this prompt into OpenClaw to automatically initialize AIGovern Pro via GSD + ClawTeam multi-agent orchestration:

---

## 📌 Prompt Template

```
You are the Leader Agent for AIGovern Pro project initialization.

Use ClawTeam to coordinate a team of specialist agents through the GSD workflow.

## Your Mission

Initialize AIGovern Pro (an AI-native enterprise B2B management system) through:
1. Deep questioning phase (you lead this)
2. Parallel research by 3 specialist agents
3. Requirements integration
4. Roadmap generation

## Environment Setup

Working directory: /Users/wclu/AIGovern_Pro
Team name: aigov-gsd
Available tools: clawteam (CLI), openclaw (current process), git

## Phase 1: Questioning (You Lead)

Ask and answer these questions about AIGovern Pro:

1. **Core Business Value**
   - What is the single most important thing AIGovern Pro must do?
   - Current thinking: "10x faster RAG-based knowledge Q&A for enterprise operations"
   - Validate: Is this still the north star?

2. **User Segment & Pain Points**
   - Who are the primary users? (Operations, Finance, Engineering, Leadership?)
   - What specific problems does AIGovern Pro solve?
   - What's the success metric? (time saved? decisions improved?)

3. **Technical Constraints**
   - Existing tech stack: React 18 + FastAPI + PostgreSQL + Redis + Milvus
   - Are there hard constraints? (migration timeline, vendor lock-in, performance SLA?)
   - What can't we change?

4. **MVP Scope**
   - Which of the "Four Core Capabilities" should Phase 1 deliver?
     (Knowledge Q&A, Data Query, Smart Operations, Business Diagnosis)
   - What's the minimum viable product that proves value?

Record your reasoning and answers to: .planning/PROJECT.md (Context section)

## Phase 2: Spawn Research Agents (Parallel)

Run these commands to spawn 3 parallel specialist agents:

### Agent 1: Tech Stack Researcher
\`\`\`bash
clawteam spawn --team aigov-gsd \
  --agent-name "researcher-tech" \
  --task "Research AIGovern Pro technical foundation:

  1. Analyze existing codebase in /Users/wclu/AIGovern_Pro:
     - backend/ (FastAPI, SQLAlchemy, PostgreSQL)
     - frontend/ (React 18, Vite, Ant Design)
     - docs/ (architecture, design system)

  2. Document current tech stack:
     - Languages, frameworks, key dependencies
     - External integrations (LLMs, databases, APIs)

  3. Map architectural patterns:
     - Entry points, data flow, abstractions
     - Known technical debt

  4. Generate: .planning/research/tech-stack.md

  When done, report to leader:
  clawteam inbox send aigov-gsd leader 'status:complete|phase:research-tech'
"
\`\`\`

### Agent 2: Market Researcher
\`\`\`bash
clawteam spawn --team aigov-gsd \
  --agent-name "researcher-market" \
  --task "Research AIGovern Pro market positioning:

  1. Define target user segment:
     - Which functional area? (Operations, Finance, Engineering, etc.)
     - Company size? (mid-market, enterprise, startup?)
     - Geography/industry?

  2. Competitive landscape:
     - Who are existing players in enterprise AI management?
     - What's AIGovern Pro's differentiation?

  3. Success criteria:
     - How will we measure adoption? (users, time saved, accuracy)
     - What's the adoption curve timeline?

  4. Generate: .planning/research/market-analysis.md

  When done, report:
  clawteam inbox send aigov-gsd leader 'status:complete|phase:research-market'
"
\`\`\`

### Agent 3: Implementation Researcher
\`\`\`bash
clawteam spawn --team aigov-gsd \
  --agent-name "researcher-impl" \
  --task "Research AIGovern Pro implementation strategy:

  1. Break down 'Four Core Capabilities' into components:
     - Knowledge Q&A: RAG engine, embeddings, retrieval
     - Data Query: SQL generation, validation, execution
     - Smart Operations: workflow automation, approval flows
     - Business Diagnosis: analytics, aggregation, dashboards

  2. Estimate scope for each capability:
     - Small (2 weeks), Medium (4 weeks), Large (8+ weeks)
     - Dependencies between capabilities

  3. Risk analysis:
     - Technical risks (LLM reliability, data quality)
     - Product risks (user adoption, business fit)
     - Mitigation strategies

  4. Suggest phased approach:
     - Phase 1 (MVP): Which capabilities?
     - Phase 2+: Extended capabilities

  5. Generate: .planning/research/implementation-path.md

  When done, report:
  clawteam inbox send aigov-gsd leader 'status:complete|phase:research-impl'
"
\`\`\`

## Phase 3: Wait for Research & Monitor

Monitor research progress:
\`\`\`bash
clawteam board attach aigov-gsd
# Or in another terminal:
clawteam inbox list aigov-gsd leader
\`\`\`

Wait until you see all 3 agents report \`status:complete\`.

## Phase 4: Requirements Engineering

Spawn Requirements Agent:
\`\`\`bash
clawteam spawn --team aigov-gsd \
  --agent-name "requirements-engineer" \
  --task "Integrate research and questioning into project requirements:

  1. Read source documents:
     - .planning/PROJECT.md (your questioning results)
     - .planning/research/*.md (all 3 research outputs)

  2. Structure requirements:
     - Validated: What AIGovern Pro already does (from code analysis)
     - Active: What we're building now (this initiative)
     - Out of Scope: What we explicitly won't build (with reasoning)

  3. Populate template .planning/REQUIREMENTS.md:
     - Each requirement must be measurable
     - Link to success criteria
     - Identify dependencies

  4. When complete:
     clawteam inbox send aigov-gsd leader 'status:complete|phase:requirements'
"
\`\`\`

## Phase 5: Roadmap Generation

Spawn Roadmap Agent:
\`\`\`bash
clawteam spawn --team aigov-gsd \
  --agent-name "roadmap-planner" \
  --task "Create phased roadmap for AIGovern Pro:

  1. Read: .planning/REQUIREMENTS.md

  2. Design roadmap:
     - Phase 1 (Foundation): Infrastructure, core APIs, MVP capability
     - Phase 2 (Expansion): Secondary capabilities
     - Phase 3+ (Scale): Advanced features, optimization

  3. For each phase, define:
     - Deliverables (features, docs, tests)
     - Success criteria (what 'done' looks like)
     - Timeline estimate
     - Risk mitigation

  4. Generate: .planning/ROADMAP.md

  5. Ensure roadmap:
     - Aligns with Core Value (from PROJECT.md)
     - Has clear completion criteria
     - Identifies integration points

  When complete:
    clawteam inbox send aigov-gsd leader 'status:complete|phase:roadmap'
"
\`\`\`

## Phase 6: Collect & Finalize

After all agents complete:

1. ✅ Verify all output files exist
2. ✅ Run: \`git add .planning/ && git commit -m "docs: GSD initialization complete"\`
3. ✅ Create .planning/STATE.md with status summary
4. 🚀 Next: Run \`/gsd-plan-phase 1\` to start Phase 1 execution

## Commands Cheat Sheet

\`\`\`bash
# List team members
clawteam team list aigov-gsd

# Check inbox messages
clawteam inbox list aigov-gsd leader

# View specific agent task
clawteam task show aigov-gsd researcher-tech

# Attach to tmux board (real-time monitoring)
clawteam board attach aigov-gsd

# Start web dashboard
clawteam board serve --port 3030

# If an agent fails, restart it:
clawteam spawn --team aigov-gsd --agent-name researcher-tech --task "..."

# Clean up (if needed):
clawteam team delete aigov-gsd
```

---

## Execution Steps

1. **Copy the template above**
2. **Paste into OpenClaw**: `openclaw "paste your prompt here"`
3. **Monitor**: `clawteam board attach aigov-gsd`
4. **Wait for completion**: All agents will report via inbox
5. **Verify**: Check that `.planning/` contains all expected artifacts
6. **Proceed**: Run `/gsd-plan-phase 1` to start Phase 1

## Alternative: Manual Execution

If you prefer step-by-step control (without full agent autonomy):

```bash
cd /Users/wclu/AIGovern_Pro
bash .planning/gsd-clawteam-init.sh
```

This script guides you through each phase manually with interactive prompts.

---

## Expected Outputs

After completion, your `.planning/` directory will contain:

```
.planning/
├── PROJECT.md                 ← Project definition (Core Value, Context, Constraints)
├── REQUIREMENTS.md            ← Scoped requirements (Validated, Active, Out of Scope)
├── ROADMAP.md                 ← Phased roadmap (Phase 1, 2, 3+)
├── STATE.md                   ← Project status summary
├── config.json                ← GSD workflow config
├── codebase/                  ← (if /gsd-map-codebase already run)
│   └── *.md
├── research/
│   ├── tech-stack.md
│   ├── market-analysis.md
│   └── implementation-path.md
└── git commits
    ├── "docs: GSD initialization complete"
    ├── "docs: research phase results aggregated"
    ├── "docs: requirements defined"
    └── "docs: roadmap created"
```

## Troubleshooting

**"clawteam: command not found"**
- Ensure: `source ~/.zshrc` or open new terminal
- Verify: `~/bin/clawteam --version`

**Agent doesn't start**
- Check OpenClaw is running: `openclaw --version`
- Verify permissions: `openclaw approvals allowlist add --agent "*" "$(which clawteam)"`
- Check tmux: `tmux ls`

**Lost work in progress**
- All agent workspaces are in git worktrees: `.git/worktrees/aigov-gsd-*/`
- Results should be committed back to main via `.planning/` merge

---

**Next**: After GSD initialization completes, run:
```bash
/gsd-plan-phase 1    # Plan Phase 1 in detail
```
