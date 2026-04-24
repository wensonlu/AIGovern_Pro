# AIGovern Pro

## Overview

AI-native enterprise B2B management system with four core capabilities: knowledge Q&A (RAG), data query (SQL generation), smart operations (auto-execution), and business diagnosis (analytics). Full-stack: React 18 frontend, FastAPI backend, PostgreSQL + Redis + Milvus.

## Project Structure

| Path              | Type    | Purpose                                                    |
| ----------------- | ------- | ---------------------------------------------------------- |
| `frontend/`       | React   | React 18 + TypeScript + Vite + Ant Design Pro + AGUI panel |
| `backend/`        | Python  | FastAPI + SQLAlchemy ORM + PostgreSQL                      |
| `docs/`           | Docs    | Design system, architecture, deployment guides             |
| `src/pages/`      | React   | 5 core pages (Dashboard, Documents, DataQuery, SmartOps)   |
| `app/api/`        | Python  | 4 API modules (documents, chat, query, operations)         |
| `app/services/`   | Python  | RAG, SQL generation, operation execution, diagnostics      |

## Quick Reference

### Languages and Tooling

- **Languages**: TypeScript/JavaScript (frontend), Python 3.9+ (backend)
- **LSPs**: typescript-language-server, pyright (both installed ✅)
- **Package managers**: pnpm (frontend), pip (backend)

### Commands

```bash
# Frontend
cd frontend && pnpm dev              # Start dev server (http://localhost:3001)
cd frontend && pnpm build            # Production build
cd frontend && pnpm lint             # ESLint check
cd frontend && pnpm type-check       # TypeScript check
cd frontend && pnpm format           # Format with Prettier

# Backend (requires Python virtual environment)
cd backend && source venv/bin/activate  # Activate virtual environment (macOS/Linux)
cd backend && source venv/Scripts/activate  # Activate virtual environment (Windows)
cd backend && python run.py          # Start FastAPI (auto-init DB, http://localhost:8000)
cd backend && python -m pytest       # Run tests
cd backend && python -m uvicorn app.main:app --reload  # Dev mode only
```

**⚠️ IMPORTANT for Backend:** Always activate the virtual environment before running Python commands:
```bash
cd backend && source venv/bin/activate  # Linux/macOS
# OR
cd backend && source venv/Scripts/activate  # Windows
```

### Environment

- Copy `backend/.env.example` → `backend/.env` for local development
- Required vars (backend): `DASHSCOPE_API_KEY`, database URL (SQLite default for dev)
- Frontend uses `vite.config.ts` proxy: `/api/*` → `http://localhost:8000`

## Progressive Disclosure

Read before starting:

| Topic                 | Location                                     |
| --------------------- | -------------------------------------------- |
| Design System         | `docs/DESIGN_SYSTEM.md`                      |
| Architecture          | `docs/architecture/TECH_ARCHITECTURE.md`     |
| Frontend Setup        | `frontend/QUICKSTART.md`                     |
| Backend Setup         | `backend/QUICKSTART.md`                      |
| Chat Panel Integration| `docs/guides/CHATPANEL_INTEGRATION_GUIDE.md` |

## Universal Rules

1. **Before commits**, run (with backend venv activated):
   ```bash
   cd frontend && pnpm lint && pnpm type-check
   cd backend && source venv/bin/activate && python -m pytest  # macOS/Linux
   # OR
   cd backend && source venv/Scripts/activate && python -m pytest  # Windows
   ```

2. **Code style**: ESLint + Prettier (frontend auto-format), Black (backend)
3. **No classes in JS/TS** — use functions only (per CLAUDE.md global rules)
4. **Python**: Type annotations on all function signatures
5. **PRs**: Single concern per PR, link to related issues

## Code Quality

- Frontend: `pnpm lint` (ESLint) + `pnpm format` (Prettier)
- Backend: `black`, `isort`, `mypy` (pre-commit ready)
- **Run verification before commits** — both linters + tests must pass
- Do NOT manually check style — let tooling enforce it

---

**Last Updated**: 2026-04-24
**Status**: Phase 2 (LLM integration + RAG) — Active Development

## Backend Execution Notes

**🔧 AI Execution Requirement:** When executing backend commands via AI agent, ensure Python virtual environment is always activated first:

```bash
# For bash-based AI execution:
cd backend && source venv/bin/activate && python run.py
# or with compound commands:
cd backend && source venv/bin/activate && python -m pytest && python run.py
```

The venv is located at `backend/venv/` and contains all project dependencies. Failing to activate it will result in "command not found" or import errors.

