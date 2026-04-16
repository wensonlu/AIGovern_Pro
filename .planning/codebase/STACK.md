# Technology Stack

**Analysis Date:** 2026-04-16

## Languages

**Primary:**
- **TypeScript 5.2.2** - Frontend application (`frontend/src/**/*.ts`, `frontend/src/**/*.tsx`)
- **Python 3.9+** - Backend API and services (`backend/app/**/*.py`)

**Secondary:**
- JavaScript/JSX - Build configuration and tooling
- JSON - Configuration and schema definitions

## Runtime

**Environment:**
- **Node.js 18.0.0+** - Frontend development and build
- **Python 3.9+** - Backend runtime (FastAPI application)

**Package Manager:**
- **pnpm** - Frontend dependency management (`frontend/package.json`)
- **pip** - Python dependency management (`backend/requirements.txt`)
- Lockfile: `frontend/pnpm-lock.yaml` (present), `backend/requirements.txt` (pinned versions)

## Frameworks

**Core:**
- **React 18.3.1** - Frontend UI framework (`frontend/src/`, components in `frontend/src/components/`)
- **FastAPI 0.110.0+** - Backend REST API framework (`backend/app/main.py`, `backend/app/api/`)
- **React Router DOM 6.20.0** - Frontend client-side routing (`frontend/src/pages/`)

**UI & Styling:**
- **Ant Design 5.11.0** - Component library with pro configuration (`frontend/src/components/`, `frontend/src/pages/`)
- **Ant Design Icons 5.2.6** - Icon library for Ant Design
- **Recharts 2.10.3** - Data visualization and charting (`frontend/src/pages/DataQuery.tsx`)
- **React Window 1.8.10** - Virtual scrolling for large lists

**Testing:**
- **Vitest 0.34.6** - Unit/integration test runner (`frontend/package.json`, run via `pnpm test`)
- **pytest 7.4.4** - Python test framework (`backend/requirements.txt`)
- **pytest-asyncio 0.23.0** - Async test support for Python

**Build/Dev:**
- **Vite 5.0.0** - Frontend build tool (`frontend/vite.config.ts`)
- **@vitejs/plugin-react 4.2.0** - React Fast Refresh plugin
- **TypeScript 5.2.2** - Type checking and compilation
- **Terser 5.46.0** - JavaScript minification
- **Uvicorn 0.27.0+** - ASGI server for FastAPI (`backend/requirements.txt`)

**Code Quality:**
- **ESLint 8.51.0** - Frontend linting (`frontend/.eslintrc*`)
- **@typescript-eslint/eslint-plugin 6.13.0** - TypeScript linting rules
- **Prettier 3.1.0** - Code formatter (`frontend/.prettierrc`)
- **babel-plugin-import 1.13.8** - Ant Design on-demand component importing

## Key Dependencies

**Frontend - HTTP & Network:**
- **axios 1.6.2** - HTTP client for API calls
- **web-vitals 4.2.1** - Web performance metrics

**Backend - Core:**
- **SQLAlchemy 2.0.30** - ORM for database operations (`backend/app/models/db_models.py`)
- **python-dotenv 1.0.0** - Environment variable loading
- **pydantic 2.10.0** - Data validation and serialization (`backend/app/models/schemas.py`)
- **python-multipart 0.0.7** - Form data parsing
- **aiofiles 24.0.0** - Async file operations

**Backend - Database:**
- **psycopg2-binary 2.9.0** - PostgreSQL database adapter
- **pgvector 0.3.0** - PostgreSQL vector type support for embeddings (`backend/app/services/rag_service.py`)

**Backend - HTTP:**
- **httpx 0.26.0** - Async HTTP client for LLM APIs (`backend/app/core/llm.py`)
- **requests 2.32.0** - Synchronous HTTP client (fallback)

**Backend - Document Processing:**
- **PyPDF2 3.0.0** - PDF extraction (`backend/app/services/` document processing)
- **python-docx 1.0.0** - Word document parsing

**Backend - Deployment:**
- **mangum 0.19.0** - ASGI to Lambda adapter for Vercel serverless (`backend/requirements.txt`)

**Backend - LLM/Embedding:**
- **dashscope** - Alibaba DashScope SDK for text embedding and generation (通义千问/豆包 models)

## Configuration

**Environment:**
- Frontend: `.env`, `.env.development`, `.env.production` in `frontend/`
- Backend: `.env` in `backend/` root (load from `backend/app/core/config.py`)
- Key configs: `VITE_API_URL` (frontend), `DATABASE_URL`, `LLM_API_KEY` (backend)

**Build:**
- `frontend/vite.config.ts` - Vite bundler configuration with React plugin, path aliases, proxy setup
- `frontend/tsconfig.json` - TypeScript compiler options (target ES2020, strict mode, path mapping)
- `backend/vercel.json` - Vercel deployment routing configuration
- `frontend/vercel.json` - Frontend Vercel deployment configuration

**Database:**
- SQLite (default dev): `sqlite:///./aigovern.db` in `backend/app/core/database.py`
- PostgreSQL (production): Supabase or self-hosted via `DATABASE_URL` env var
- Migrations: Not using Alembic; schema managed via SQLAlchemy models

## Platform Requirements

**Development:**
- Node.js 18.0.0+ with npm 9.0.0+
- Python 3.9+
- Redis (optional, for caching - `REDIS_URL` in config)
- PostgreSQL 12+ (for production; SQLite used in dev by default)

**Production:**
- **Hosting:** Vercel (serverless)
- **Backend:** Deployed as serverless function via `backend/vercel.json` + Mangum adapter
- **Frontend:** Deployed as static site to Vercel
- **Database:** Supabase PostgreSQL with pgvector extension
- **LLM Provider:** Doubao (ByteDance) or Qwen (Alibaba) via API

## Architecture Overview

**Frontend (React + Vite):**
- Entry: `frontend/src/main.tsx`
- Pages: `frontend/src/pages/` (Dashboard, Documents, DataQuery, SmartOps, Products)
- Components: `frontend/src/components/` (Ant Design based, AGUI ChatPanel)
- Services: `frontend/src/services/api.ts` (HTTP layer with retry logic, timeout handling)
- Build output: `frontend/dist/` (mounted via FastAPI static files)

**Backend (FastAPI + Python):**
- Entry: `backend/app/main.py` (FastAPI app, includes CORS, API routers, static file serving)
- API Routes: `backend/app/api/` (chat, query, operations, diagnosis, documents, products)
- Services: `backend/app/services/` (RAG, SQL generation, operations, diagnostics, agent)
- Core: `backend/app/core/` (config, database, LLM client, auth)
- Database: SQLAlchemy ORM with pgvector for embeddings

## Vercel Deployment Config

**Backend Serverless:**
- Build: `pip install -r backend/requirements.txt`
- Entry: `/backend/api/index.py` (generated by Mangum)
- CORS: Allows `https://*.vercel.app`, `localhost:3000/3001`, specific domains
- Env: `PYTHONPATH=/var/task/backend` configured in `backend/vercel.json`

**Frontend Static:**
- Build: `tsc && vite build`
- Output: `frontend/dist/`
- Deployment: Vercel static hosting

---

*Stack analysis: 2026-04-16*
