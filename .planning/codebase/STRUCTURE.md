# Codebase Structure

**Analysis Date:** 2026-04-16

## Directory Layout

```
AIGovern_Pro/
├── frontend/                          # React 18 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── pages/                     # Feature pages (lazy-loaded)
│   │   ├── components/                # Reusable React components
│   │   ├── services/                  # API client
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── App.tsx                    # Router root component
│   │   └── main.tsx                   # React entry point
│   ├── vite.config.ts                 # Vite build config with aliases
│   ├── package.json                   # pnpm dependencies
│   └── dist/                          # Production build output (committed by Vercel)
│
├── backend/                           # FastAPI + Python backend
│   ├── app/
│   │   ├── main.py                    # FastAPI app definition, routes, CORS, static file serving
│   │   ├── api/                       # HTTP route handlers
│   │   │   ├── documents.py           # Document upload, list, retrieval testing
│   │   │   ├── chat.py                # Unified chat endpoint (agent router)
│   │   │   ├── query.py               # Natural language → SQL
│   │   │   ├── operations.py          # Operation templates & execution
│   │   │   ├── diagnosis.py           # Business metrics & diagnostics
│   │   │   └── products.py            # Product management (stub)
│   │   ├── services/                  # Business logic
│   │   │   ├── agent_service.py       # Intent recognition + routing
│   │   │   ├── rag_service.py         # pgvector retrieval + LLM answer generation
│   │   │   ├── sql_service.py         # NL→SQL generation + execution
│   │   │   ├── operation_service.py   # Operation templates & execution
│   │   │   └── diagnosis_service.py   # Metric analysis
│   │   ├── models/
│   │   │   ├── db_models.py           # SQLAlchemy ORM models (Document, Order, Product, etc.)
│   │   │   └── schemas.py             # Pydantic request/response schemas
│   │   ├── core/
│   │   │   ├── config.py              # Settings (env vars, database URL, LLM keys)
│   │   │   ├── database.py            # SQLAlchemy engine & session factory
│   │   │   └── llm.py                 # LLM client (DuBao, Qwen), embedding generation
│   │   ├── middleware/                # Placeholder for auth/logging middleware
│   │   └── tools/                     # Placeholder for tool implementations
│   ├── run.py                         # Server launcher (auto-init DB)
│   └── requirements.txt               # pip dependencies
│
├── docs/                              # Documentation
│   ├── architecture/
│   ├── guides/
│   └── DESIGN_SYSTEM.md
│
├── .env                               # Local development env vars (git-ignored)
├── .env.example                       # Template for .env
├── vite.json                          # Vercel config (backend deployment)
├── package.json                       # Root package (monorepo coordination)
├── CLAUDE.md                          # Project-specific guidelines
└── README.md                          # Project overview

```

## Directory Purposes

**`frontend/src/pages/`** (6 pages):
- Purpose: Core feature pages for each business capability
- Contains: 
  - `Dashboard.tsx` - KPI cards, trend charts, anomaly alerts, AI recommendations
  - `Documents.tsx` - Document upload (via drag-drop), RAG chunk visualization, retrieval testing
  - `DataQuery.tsx` - Natural language query input, SQL display, results table/chart, CSV export
  - `SmartOps.tsx` - Operation template selection, execution, timeline of logs
  - `Diagnosis.tsx` - Metric display, anomaly analysis, business diagnostics
  - `Products.tsx` - Product management stub
- Key files: Each page is ~200-400 lines, imports from `../components/Layout` for consistent header/sidebar

**`frontend/src/components/`**:
- Purpose: Shared UI components
- Contains:
  - `Layout/AppLayout.tsx` - Master layout with header (user menu, notifications), sidebar (navigation menu), content area
  - `AGUI/ChatPanel.tsx` - Floating chat panel with message virtualization (react-window), source tags, confidence bar
- Pattern: Functional components with `React.memo` for optimization

**`frontend/src/services/api.ts`**:
- Purpose: Centralized API client with retry logic
- Contains: Type-safe fetch wrapper (`callAPI<T>`), exponential backoff retry, timeout handling (30s default)
- Pattern: Async functions for each endpoint (checkHealth, chatWithKnowledge, queryData, etc.)
- Key: Environment-aware URL (`VITE_API_URL` env var, relative path in prod, localhost:8000 in dev)

**`frontend/src/hooks/useApiCall.ts`**:
- Purpose: Custom hook for API calls with loading/error state
- Pattern: Generic hook for data fetching, encapsulates axios + state management

**`backend/app/api/`** (6 routes):
- Purpose: HTTP request handlers for each capability
- Pattern: Each route file exports FastAPI `APIRouter`, registered in `main.py`
- Dependencies: Each handler receives `db: Session = Depends(get_db)` for database access
- Response models: All validated via Pydantic schemas

**`backend/app/services/`** (5 services):
- Purpose: Encapsulate business logic, independent of HTTP layer
- Pattern: Classes with async methods, stateless (session_id passed as parameter)
- Key: All services interact with LLM client (`llm_client`) for AI capabilities

**`backend/app/models/db_models.py`** (9 tables):
- ORM models with SQLAlchemy:
  - `Document`, `DocumentChunk` - RAG knowledge base
  - `Order`, `Product`, `User` - Business data
  - `OperationLog` - Audit trail for smart operations
  - `Metric`, `QueryCache`, `ProductPriceHistory` - Analytics & history

**`backend/app/models/schemas.py`** (Pydantic):
- Request/response contracts for all endpoints
- Pattern: Separate classes for input validation (Request) and output (Response)
- Key: `SourceReference` tracks document origin, includes `relevance_percentage` for frontend display

**`backend/app/core/config.py`**:
- Purpose: Centralized settings from environment
- Contains:
  - Database URL (SQLite for dev, PostgreSQL for prod)
  - LLM provider choice (DuBao/Qwen) + API keys
  - Embedding model config (separate from LLM)
  - File upload limits (50MB)
  - Vector dimensions (1536 raw from Qwen, truncated to 768 for pgvector)

**`backend/app/core/llm.py`**:
- Purpose: Multi-provider LLM abstraction
- Contains: Provider detection, async HTTP clients for text generation + embeddings
- Key: Embedding truncation from 1536 to 768 dims for pgvector storage

**`backend/app/core/database.py`**:
- Purpose: SQLAlchemy engine setup and session factory
- Pattern: Conditional setup (SQLite for dev, PostgreSQL for prod)
- Key: `get_db()` generator for dependency injection

## Key File Locations

**Entry Points:**
- Frontend: `frontend/src/main.tsx` - React root, theme config, Web Vitals
- Backend: `backend/app/main.py` - FastAPI app, route registration, static file serving
- Server launcher: `backend/run.py` - Database initialization, uvicorn startup

**Configuration:**
- Environment: `.env` (git-ignored), template in `.env.example`
- Frontend build: `frontend/vite.config.ts` (port 3000, /api proxy, code splitting)
- Backend config: `backend/app/core/config.py` (reads .env)

**Core Logic:**
- RAG flow: `backend/app/services/rag_service.py` (embedding → pgvector → LLM answer)
- SQL generation: `backend/app/services/sql_service.py` (NL → SQL → execute)
- Intent routing: `backend/app/services/agent_service.py` (LLM intent classification)
- Document ingestion: `backend/app/api/documents.py` (upload → chunk → embed → store)

**Testing:**
- Frontend: No test files in source (testing infrastructure TBD)
- Backend: No test files in source (testing infrastructure TBD)

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `rag_service.py`, `db_models.py`)
- TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utilities
  - Example: `ChatPanel.tsx`, `api.ts`, `useApiCall.ts`
- CSS: Component-scoped `ComponentName.module.css`

**Directories:**
- Feature pages: lowercase plural (`pages/`), individual files PascalCase
- Services: `services/` (backend), `services/` (frontend API client)
- Components: lowercase plural (`components/`), subdirectories for feature groups (`Layout/`, `AGUI/`)

**Functions:**
- Backend: `snake_case` (async prefixed where async)
  - Example: `retrieve_documents()`, `generate_sql()`, `execute_operation()`
- Frontend: `camelCase` for hooks, `PascalCase` for component functions
  - Example: `useApiCall()`, `ChatPanel()`, `KPICard()`

**Types/Interfaces:**
- Backend: Pydantic `BaseModel` subclasses, PascalCase
  - Example: `ChatRequest`, `SourceReference`, `QueryResponse`
- Frontend: TypeScript interfaces, PascalCase
  - Example: `Message`, `DocumentItem`, `KPIItem`

**Database:**
- Tables: `snake_case`, plural (e.g., `documents`, `document_chunks_with_vectors`, `orders`)
- Columns: `snake_case` (e.g., `document_id`, `chunk_index`, `embedding_status`)
- Foreign keys: `{table}_id` (e.g., `document_id` references `documents.id`)

**API Routes:**
- Path pattern: `/api/{capability}/{resource}/{action}?params`
- Example: `/api/documents/upload`, `/api/query`, `/api/operations/{id}/execute`
- Request body: camelCase in frontend, snake_case in Python (converted by Pydantic)

## Where to Add New Code

**New Feature Page:**
1. Create `frontend/src/pages/NewFeature.tsx` (lazy-imported in `App.tsx`)
2. Import shared layout: `import AppLayout from '../components/Layout'`
3. Use page structure: header, content, optional modals
4. Call API service: `import { newFeatureApi } from '../services/api'`
5. Add route: `<Route path="/newfeature" element={<NewFeature />} />`
6. Add sidebar menu item in `AppLayout.tsx`

**New API Endpoint:**
1. Create `backend/app/api/newfeature.py` with `router = APIRouter(prefix="/api/newfeature")`
2. Define Pydantic schemas in `backend/app/models/schemas.py` (Request/Response)
3. Define handler function with `@router.post("")` decorator
4. Import dependency: `db: Session = Depends(get_db)`
5. Register router in `backend/app/main.py`: `app.include_router(newfeature.router)`

**New Service:**
1. Create `backend/app/services/newfeature_service.py`
2. Define class: `class NewFeatureService: def __init__(self): self.llm = llm_client`
3. Implement async methods for business logic
4. Import in API handler: `from app.services.newfeature_service import service`
5. Call from route handler

**New Database Model:**
1. Add SQLAlchemy class to `backend/app/models/db_models.py`
2. Extend `Base` class, define `__tablename__` and columns
3. Add relationships if needed (e.g., `relationship("OtherModel", back_populates="...")`)
4. Create/update migration (or delete `aigovern.db` to auto-recreate on next run)

**New Component:**
1. Create `frontend/src/components/Feature/NewComponent.tsx`
2. Export as React.FC with TypeScript interface for props
3. Use `React.memo()` if frequently re-rendered
4. Create corresponding `NewComponent.module.css` for styles
5. Import and use in pages: `import NewComponent from '../components/Feature/NewComponent'`

**New Hook:**
1. Create `frontend/src/hooks/useNewHook.ts`
2. Pattern: `export const useNewHook = (deps) => { ... return state }`
3. Use inside components: `const { state, loading, error } = useNewHook()`

## Special Directories

**`frontend/dist/`**:
- Purpose: Production build output from Vite
- Generated: Yes (via `pnpm build`)
- Committed: Yes (Vercel deployment requirement)
- Contents: Minified JS/CSS chunks, assets, index.html

**`backend/uploads/`**:
- Purpose: Temporary storage for uploaded documents
- Generated: Yes (auto-created by `documents.py`)
- Committed: No (.gitignore)
- Cleanup: Not implemented (manual delete needed)

**`.planning/codebase/`**:
- Purpose: GSD codebase analysis documents
- Generated: Yes (by `/gsd-map-codebase` command)
- Committed: Yes
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md

**`.env`**:
- Purpose: Local development configuration
- Generated: No (must copy from `.env.example`)
- Committed: No (.gitignore)
- Required: Yes, for local development

**`docs/`**:
- Purpose: User-facing and developer documentation
- Generated: No (manually written)
- Committed: Yes
- Contains: Design system, architecture guides, deployment guides

---

*Structure analysis: 2026-04-16*
