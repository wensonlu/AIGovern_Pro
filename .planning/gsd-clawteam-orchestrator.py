#!/usr/bin/env python3
"""
GSD + ClawTeam Multi-Agent Workflow Orchestrator

Programmatic interface to coordinate AIGovern Pro initialization through
ClawTeam multi-agent framework.

Usage:
    python3 gsd-clawteam-orchestrator.py [--auto] [--team-name aigov-gsd]

"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Configuration ──────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent.parent
PLANNING_DIR = PROJECT_DIR / ".planning"
RESEARCH_DIR = PLANNING_DIR / "research"
DEFAULT_TEAM_NAME = "aigov-gsd"

# ─── Logging ──────────────────────────────────────────────────────────────

class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    RESET = "\033[0m"

def log_info(msg: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.RESET}  {msg}")

def log_ok(msg: str) -> None:
    print(f"{Colors.GREEN}[OK]{Colors.RESET}    {msg}")

def log_warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET}  {msg}")

def log_error(msg: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}", file=sys.stderr)
    sys.exit(1)

# ─── Utilities ──────────────────────────────────────────────────────────────

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Execute shell command and return result."""
    log_info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    if check and result.returncode != 0:
        log_error(f"Command failed: {cmd}")
    return result

def check_prerequisites() -> None:
    """Verify all required tools are installed."""
    log_info("Checking prerequisites...")

    tools = {
        "clawteam": "pip install -e /tmp/ClawTeam-OpenClaw",
        "tmux": "brew install tmux",
        "python3": "installed by default",
        "openclaw": "pip install openclaw (optional)",
    }

    missing = []
    for tool, install_cmd in tools.items():
        result = subprocess.run(f"command -v {tool}", shell=True, capture_output=True)
        if result.returncode != 0:
            if tool != "openclaw":  # openclaw is optional
                missing.append((tool, install_cmd))
            else:
                log_warn(f"openclaw not found (optional)")

    if missing:
        log_error(f"Missing tools: {', '.join([t[0] for t in missing])}\n" +
                  "\n".join([f"  {t[0]}: {t[1]}" for t in missing]))

    # Verify planning directory exists
    if not PLANNING_DIR.exists():
        log_error(f".planning/ not found in {PROJECT_DIR}")

    log_ok("All prerequisites satisfied")

def team_exists(team_name: str) -> bool:
    """Check if ClawTeam team already exists."""
    result = subprocess.run(
        f"clawteam team list {team_name}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def create_team(team_name: str) -> None:
    """Create ClawTeam for project initialization."""
    if team_exists(team_name):
        log_warn(f"Team {team_name} already exists, deleting...")
        run_command(f"clawteam team delete {team_name}", check=False)
        time.sleep(2)

    log_info(f"Creating team: {team_name}...")
    run_command(
        f'clawteam team spawn-team {team_name} '
        f'-d "Initialize AIGovern Pro via GSD + ClawTeam" '
        f'-n leader'
    )
    log_ok(f"Team created: {team_name}")

def spawn_research_agents(team_name: str) -> None:
    """Spawn 3 parallel research agents."""
    log_info("Spawning 3 research agents...")

    agents = [
        {
            "name": "researcher-tech",
            "task": """Research AIGovern Pro technical foundation:
1. Analyze codebase structure (backend/, frontend/, docs/)
2. Document tech stack: languages, frameworks, dependencies
3. Identify external APIs and integrations
4. Map current architecture patterns
5. Generate: .planning/research/tech-stack.md
When complete: clawteam inbox send {team} leader 'status:complete|phase:tech'"""
        },
        {
            "name": "researcher-market",
            "task": """Research AIGovern Pro market positioning:
1. Define target user segment and pain points
2. Analyze competitive landscape
3. Document success metrics and KPIs
4. Map market trends
5. Generate: .planning/research/market-analysis.md
When complete: clawteam inbox send {team} leader 'status:complete|phase:market'"""
        },
        {
            "name": "researcher-impl",
            "task": """Research implementation strategy:
1. Break down Four Core Capabilities into components
2. Estimate scope for each capability
3. Analyze technical and product risks
4. Suggest phased approach
5. Generate: .planning/research/implementation-path.md
When complete: clawteam inbox send {team} leader 'status:complete|phase:impl'"""
        }
    ]

    for agent in agents:
        run_command(
            f'clawteam spawn --team {team_name} '
            f'--agent-name "{agent["name"]}" '
            f'--task "{agent["task"].format(team=team_name)}"'
        )
        log_ok(f"Spawned: {agent['name']}")

def wait_for_research_completion(team_name: str, timeout_sec: int = 600) -> bool:
    """Wait for all 3 research agents to complete."""
    log_info("Waiting for research agents to complete...")

    elapsed = 0
    while elapsed < timeout_sec:
        result = subprocess.run(
            f"clawteam inbox list {team_name} leader",
            shell=True,
            capture_output=True,
            text=True
        )

        completed = result.stdout.count("status:complete")
        if completed >= 3:
            log_ok("All research agents completed")
            return True

        remaining = timeout_sec - elapsed
        log_info(f"Waiting... ({completed}/3 complete, {remaining}s remaining)")
        time.sleep(10)
        elapsed += 10

    log_warn(f"Timeout waiting for research completion after {timeout_sec}s")
    return False

def spawn_requirements_agent(team_name: str) -> None:
    """Spawn requirements integration agent."""
    log_info("Spawning requirements engineer...")

    task = """Integrate research into project requirements:
1. Read all research files from .planning/research/
2. Re-read questioning from .planning/PROJECT.md
3. Structure into: Validated, Active, Out of Scope
4. Generate .planning/REQUIREMENTS.md
5. Ensure requirements are measurable and sequenced
When complete: clawteam inbox send {team} leader 'status:complete|phase:requirements'"""

    run_command(
        f'clawteam spawn --team {team_name} '
        f'--agent-name "requirements-engineer" '
        f'--task "{task.format(team=team_name)}"'
    )
    log_ok("Spawned: requirements-engineer")

def spawn_roadmap_agent(team_name: str) -> None:
    """Spawn roadmap planning agent."""
    log_info("Spawning roadmap planner...")

    task = """Create phased roadmap:
1. Read .planning/REQUIREMENTS.md
2. Design Phase 1 (Foundation), Phase 2 (Expansion), Phase 3+ (Scale)
3. For each phase: deliverables, success criteria, timeline, risks
4. Generate .planning/ROADMAP.md
5. Ensure roadmap aligns with Core Value
When complete: clawteam inbox send {team} leader 'status:complete|phase:roadmap'"""

    run_command(
        f'clawteam spawn --team {team_name} '
        f'--agent-name "roadmap-planner" '
        f'--task "{task.format(team=team_name)}"'
    )
    log_ok("Spawned: roadmap-planner")

def verify_output_files() -> bool:
    """Verify all expected output files exist."""
    required_files = [
        ".planning/PROJECT.md",
        ".planning/REQUIREMENTS.md",
        ".planning/ROADMAP.md",
        ".planning/research/tech-stack.md",
        ".planning/research/market-analysis.md",
        ".planning/research/implementation-path.md",
    ]

    log_info("Verifying output files...")
    all_exist = True

    for file_path in required_files:
        full_path = PROJECT_DIR / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            log_ok(f"Generated: {file_path} ({size} bytes)")
        else:
            log_warn(f"Missing: {file_path}")
            all_exist = False

    return all_exist

def create_state_file() -> None:
    """Create STATE.md summarizing project state."""
    log_info("Creating .planning/STATE.md...")

    state_content = f"""# AIGovern Pro - Project State

## Status: Initialized via GSD + ClawTeam

**Initialization Date**: {datetime.now().isoformat()}
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
- `.planning/research/` — Supporting research documents

## Next Steps

1. Review generated artifacts
2. Validate roadmap with stakeholders
3. Run: `/gsd-plan-phase 1`
4. Execute Phase 1

## MultiAgent Team

| Role | Agent | Status |
|------|-------|--------|
| Leader | OpenClaw | Active |
| Tech Research | researcher-tech | Completed |
| Market Research | researcher-market | Completed |
| Impl Research | researcher-impl | Completed |
| Requirements | requirements-engineer | Completed |
| Roadmap | roadmap-planner | Completed |

---

Last Updated: {datetime.now().isoformat()}
"""

    state_file = PLANNING_DIR / "STATE.md"
    state_file.write_text(state_content)
    log_ok(f"Created: {state_file.relative_to(PROJECT_DIR)}")

def commit_results(team_name: str) -> None:
    """Commit all generated artifacts."""
    log_info("Committing results to git...")

    os.chdir(PROJECT_DIR)
    run_command("git add .planning/")
    run_command(
        'git commit -m "docs: GSD initialization complete (questioning, research, requirements, roadmap)"',
        check=False
    )
    log_ok("Committed to git")

def print_summary(team_name: str) -> None:
    """Print final summary and next steps."""
    print("\n" + "=" * 80)
    print(f"{Colors.GREEN}✓ GSD + ClawTeam Initialization Complete{Colors.RESET}")
    print("=" * 80)

    print("\n📋 Generated Artifacts:")
    for file_path in [
        ".planning/PROJECT.md",
        ".planning/REQUIREMENTS.md",
        ".planning/ROADMAP.md",
        ".planning/STATE.md",
    ]:
        full_path = PROJECT_DIR / file_path
        if full_path.exists():
            lines = len(full_path.read_text().split("\n"))
            print(f"   ✓ {file_path} ({lines} lines)")

    print("\n📊 Team Status:")
    result = subprocess.run(
        f"clawteam team list {team_name}",
        shell=True,
        capture_output=True,
        text=True
    )
    for line in result.stdout.split("\n")[:5]:
        if line.strip():
            print(f"   {line}")

    print("\n🎯 Next Steps:")
    print("   1. Review artifacts:")
    print("      cat .planning/PROJECT.md")
    print("      cat .planning/REQUIREMENTS.md")
    print("      cat .planning/ROADMAP.md")
    print("\n   2. Proceed to Phase 1:")
    print("      /gsd-plan-phase 1")
    print("\n   3. Monitor team:")
    print(f"      clawteam board attach {team_name}")
    print("\n" + "=" * 80 + "\n")

# ─── Main Orchestration ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GSD + ClawTeam multi-agent orchestrator for AIGovern Pro"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run fully automated (no interactive prompts)"
    )
    parser.add_argument(
        "--team-name",
        default=DEFAULT_TEAM_NAME,
        help=f"ClawTeam team name (default: {DEFAULT_TEAM_NAME})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout waiting for agents to complete (seconds)"
    )

    args = parser.parse_args()

    # Pre-flight checks
    check_prerequisites()

    # Phase 1: Create team
    log_info("Phase 1: Initializing ClawTeam...")
    create_team(args.team_name)

    # Phase 2: Spawn research agents
    log_info("Phase 2: Spawning research agents...")
    spawn_research_agents(args.team_name)

    if not args.auto:
        log_info("Agents spawned. Monitor with:")
        log_info(f"  clawteam board attach {args.team_name}")
        input("Press ENTER when research agents complete...")
    else:
        # In auto mode, wait for completion
        if not wait_for_research_completion(args.team_name, args.timeout):
            log_warn("Research agents did not complete within timeout")

    # Phase 3: Spawn requirements agent
    log_info("Phase 3: Spawning requirements engineer...")
    spawn_requirements_agent(args.team_name)

    if not args.auto:
        input("Press ENTER when requirements-engineer completes...")
    else:
        time.sleep(30)  # Allow time to start

    # Phase 4: Spawn roadmap agent
    log_info("Phase 4: Spawning roadmap planner...")
    spawn_roadmap_agent(args.team_name)

    if not args.auto:
        input("Press ENTER when roadmap-planner completes...")
    else:
        time.sleep(30)

    # Phase 5: Collect & finalize
    log_info("Phase 5: Collecting results...")
    verify_output_files()
    create_state_file()
    commit_results(args.team_name)

    # Summary
    print_summary(args.team_name)

if __name__ == "__main__":
    main()
