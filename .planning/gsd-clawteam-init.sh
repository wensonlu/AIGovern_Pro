#!/bin/bash
set -euo pipefail

# ─── GSD + ClawTeam Multi-Agent Workflow Initialization ──────────────────────
#
# Orchestrates AIGovern Pro project initialization through:
# 1. Leader deep questioning phase
# 2. Parallel research by 3 specialist agents
# 3. Requirements aggregation
# 4. Roadmap generation
#
# Usage: bash gsd-clawteam-init.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEAM_NAME="aigov-gsd"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { printf "${BLUE}[INFO]${NC}  %s\n" "$*"; }
log_ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$*"; }
log_warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$*"; exit 1; }

# ─── Pre-flight checks ──────────────────────────────────────────────────────
log_info "Pre-flight checks..."

command -v clawteam >/dev/null 2>&1 || log_error "clawteam not found. Run: pip install -e /tmp/ClawTeam-OpenClaw"
command -v tmux >/dev/null 2>&1 || log_error "tmux not found. Run: brew install tmux"
command -v openclaw >/dev/null 2>&1 || log_warn "openclaw not found (optional if using claude or codex)"
command -v python3 >/dev/null 2>&1 || log_error "python3 not found"

[[ -d "$PROJECT_DIR/.planning" ]] || log_error ".planning/ not found in $PROJECT_DIR"

log_ok "All pre-flight checks passed"

# ─── Phase 1: Initialize ClawTeam ──────────────────────────────────────────
log_info "Phase 1: Creating ClawTeam..."

# Clean up any existing team
if clawteam team list 2>/dev/null | grep -q "$TEAM_NAME"; then
    log_warn "Team $TEAM_NAME already exists, deleting..."
    clawteam team delete "$TEAM_NAME" || true
    sleep 2
fi

# Create team
clawteam team spawn-team "$TEAM_NAME" \
    -d "Initialize AIGovern Pro via GSD + ClawTeam" \
    -n leader

log_ok "Team created: $TEAM_NAME"

# ─── Phase 2: Questioning (Leader) ────────────────────────────────────────
log_info "Phase 2: Leader questioning phase (manual interaction required)..."
log_info "Please answer the following in your OpenClaw/Claude session:"
log_info ""
log_info "  1. What is the core business value of AIGovern Pro?"
log_info "  2. Who are the primary users and what pain points does it solve?"
log_info "  3. What are the non-negotiable technical constraints?"
log_info "  4. What is the 'must work' MVP scope?"
log_info ""
log_warn "Save responses to: $PROJECT_DIR/.planning/PROJECT.md (section: Context)"
log_info ""
read -p "Press ENTER after questioning phase is complete (or Ctrl+C to abort)..."

log_ok "Questioning phase saved"

# ─── Phase 3: Spawn Research Agents (Parallel) ───────────────────────────
log_info "Phase 3: Spawning 3 parallel research agents..."

# Research 1: Tech Stack & Architecture
clawteam spawn --team "$TEAM_NAME" \
    --agent-name "researcher-tech" \
    --task "Research AIGovern Pro technical foundation:

    1. Analyze existing codebase structure (backend/, frontend/, docs/)
    2. Document current tech stack: languages, frameworks, dependencies
    3. Identify external APIs and service integrations
    4. Map current architecture patterns and abstractions
    5. List known technical debt or limitations
    6. Generate output: .planning/research/tech-stack.md

    When complete, send inbox message to leader:
    clawteam inbox send $TEAM_NAME leader 'status:complete phase:research-tech'
    "

log_ok "Spawned: researcher-tech"

# Research 2: Market & Product
clawteam spawn --team "$TEAM_NAME" \
    --agent-name "researcher-market" \
    --task "Research AIGovern Pro product positioning:

    1. Define target user segment (Operations? Finance? Engineering?)
    2. Identify competitor landscape and differentiation
    3. Document success metrics and KPIs
    4. Map current user feedback or pain points
    5. Analyze market trends in enterprise AI adoption
    6. Generate output: .planning/research/market-analysis.md

    When complete, send inbox message to leader:
    clawteam inbox send $TEAM_NAME leader 'status:complete phase:research-market'
    "

log_ok "Spawned: researcher-market"

# Research 3: Implementation Path
clawteam spawn --team "$TEAM_NAME" \
    --agent-name "researcher-impl" \
    --task "Research AIGovern Pro implementation strategy:

    1. Break down 'Four Core Capabilities' into technical components
    2. Identify dependencies and sequencing constraints
    3. Estimate scope for each capability (L/M/S)
    4. Map risk areas and mitigation strategies
    5. Suggest phased delivery approach (MVP → Extended)
    6. Generate output: .planning/research/implementation-path.md

    When complete, send inbox message to leader:
    clawteam inbox send $TEAM_NAME leader 'status:complete phase:research-impl'
    "

log_ok "Spawned: researcher-impl"

echo ""
log_info "All 3 research agents spawned and running in parallel"
log_info "Attach to monitoring board to watch progress:"
log_info "  clawteam board attach $TEAM_NAME"
log_info ""
read -p "Press ENTER when all research agents report 'status:complete'..."

# ─── Phase 4: Wait for Research Completion ─────────────────────────────────
log_info "Phase 4: Collecting research results..."

MAX_WAIT=600  # 10 minutes
ELAPSED=0

while [[ $ELAPSED -lt $MAX_WAIT ]]; do
    COMPLETED=$(clawteam inbox list "$TEAM_NAME" leader 2>/dev/null | grep -c "status:complete" || echo 0)

    if [[ $COMPLETED -ge 3 ]]; then
        log_ok "All 3 research agents completed"
        break
    fi

    log_info "Waiting for research agents... ($COMPLETED/3 complete, elapsed: ${ELAPSED}s)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [[ $ELAPSED -ge $MAX_WAIT ]]; then
    log_warn "Timeout waiting for research completion. Manual intervention needed:"
    log_warn "  clawteam inbox list $TEAM_NAME leader"
    log_warn "  clawteam task list $TEAM_NAME"
fi

# ─── Phase 5: Spawn Requirements Agent ──────────────────────────────────────
log_info "Phase 5: Spawning requirements engineer agent..."

clawteam spawn --team "$TEAM_NAME" \
    --agent-name "requirements-engineer" \
    --task "Integrate all research results into project requirements:

    1. Read all research files from .planning/research/:
       - tech-stack.md
       - market-analysis.md
       - implementation-path.md

    2. Re-read questioning results from .planning/PROJECT.md

    3. Define requirements structure:
       - Validated (from existing code analysis)
       - Active (for this initiative)
       - Out of Scope (with reasoning)

    4. Generate .planning/REQUIREMENTS.md following template

    5. Ensure requirements are:
       - Measurable (KPIs, success metrics)
       - Sequenced (dependencies clear)
       - Scoped (MVP vs. extended phases)

    When complete, send inbox message:
    clawteam inbox send $TEAM_NAME leader 'status:complete phase:requirements'
    "

log_ok "Spawned: requirements-engineer"

read -p "Press ENTER when requirements-engineer completes..."

# ─── Phase 6: Spawn Roadmap Agent ──────────────────────────────────────────
log_info "Phase 6: Spawning roadmap planner agent..."

clawteam spawn --team "$TEAM_NAME" \
    --agent-name "roadmap-planner" \
    --task "Create project roadmap based on requirements:

    1. Read .planning/REQUIREMENTS.md

    2. Design roadmap structure:
       - Phase 1: Foundation (core infrastructure)
       - Phase 2: MVP (knowledge Q&A)
       - Phase 3+: Extended capabilities

    3. For each phase define:
       - Deliverables (features, docs, tests)
       - Success criteria
       - Timeline estimate
       - Risk mitigation

    4. Generate .planning/ROADMAP.md

    5. Ensure roadmap:
       - Aligns with Core Value (from PROJECT.md)
       - Is testable (clear completion criteria)
       - Has contingency plans

    When complete, send inbox message:
    clawteam inbox send $TEAM_NAME leader 'status:complete phase:roadmap'
    "

log_ok "Spawned: roadmap-planner"

read -p "Press ENTER when roadmap-planner completes..."

# ─── Phase 7: Collect & Aggregate Results ──────────────────────────────────
log_info "Phase 7: Collecting aggregated results..."

# Verify all files exist
REQUIRED_FILES=(
    ".planning/PROJECT.md"
    ".planning/REQUIREMENTS.md"
    ".planning/ROADMAP.md"
    ".planning/research/tech-stack.md"
    ".planning/research/market-analysis.md"
    ".planning/research/implementation-path.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$PROJECT_DIR/$file" ]]; then
        log_warn "Missing: $file (will be generated by agent)"
    else
        log_ok "Generated: $file ($(wc -l < "$PROJECT_DIR/$file") lines)"
    fi
done

# Create STATE.md
log_info "Creating .planning/STATE.md..."

cat > "$PROJECT_DIR/.planning/STATE.md" << 'EOF'
# AIGovern Pro - Project State

## Status: Initialized via GSD + ClawTeam

**Initialization Date**: $(date)
**Lead Team**: aigov-gsd (OpenClaw + ClawTeam)
**Phases Completed**: Questioning, Research, Requirements, Roadmap

## Project Reference

See: .planning/PROJECT.md

**Core Value**: Deliver 10x faster RAG-based knowledge Q&A for enterprise operations teams

**Current Focus**: Phase 1 (Foundation & Infrastructure)

## Artifacts Generated

- `.planning/PROJECT.md` — Project definition and constraints
- `.planning/REQUIREMENTS.md` — Scoped requirements and success criteria
- `.planning/ROADMAP.md` — Phased delivery plan
- `.planning/config.json` — GSD workflow preferences
- `.planning/research/` — Supporting research documents

## Next Steps

1. Review generated artifacts for accuracy
2. Validate roadmap timeline with stakeholders
3. Run `/gsd-plan-phase 1` to begin Phase 1 planning
4. Execute Phase 1 per roadmap

## Team Structure

| Role | Agent | Status |
|------|-------|--------|
| Leader | OpenClaw (main process) | Active |
| Tech Research | researcher-tech | Completed |
| Market Research | researcher-market | Completed |
| Implementation Research | researcher-impl | Completed |
| Requirements Engineering | requirements-engineer | Completed |
| Roadmap Planning | roadmap-planner | Completed |

---

Last Updated: $(date)
EOF

log_ok "Created: .planning/STATE.md"

# ─── Phase 8: Commit Results ────────────────────────────────────────────────
log_info "Phase 8: Committing results..."

cd "$PROJECT_DIR"

git add .planning/
git commit -m "docs: GSD initialization complete (questioning, research, requirements, roadmap)" || \
    log_warn "Git commit failed (might already be staged)"

log_ok "Committed to git"

# ─── Final Report ──────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${GREEN}✓ GSD Initialization Complete${NC}\n"
echo ""
echo "📋 Generated Artifacts:"
echo "   • .planning/PROJECT.md (project definition)"
echo "   • .planning/REQUIREMENTS.md (scoped requirements)"
echo "   • .planning/ROADMAP.md (phased delivery plan)"
echo "   • .planning/STATE.md (project state)"
echo "   • .planning/research/ (supporting research)"
echo ""
echo "📊 Team Status:"
clawteam team list "$TEAM_NAME" 2>/dev/null | head -10 || echo "   (ClawTeam team details)"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "   1. Review generated artifacts:"
echo "      cat .planning/PROJECT.md"
echo "      cat .planning/REQUIREMENTS.md"
echo "      cat .planning/ROADMAP.md"
echo ""
echo "   2. If satisfied, proceed to Phase 1 planning:"
echo "      /gsd-plan-phase 1"
echo ""
echo "   3. To monitor team progress:"
echo "      clawteam board attach $TEAM_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
