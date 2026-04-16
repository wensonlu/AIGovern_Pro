# Architecture

**Analysis Date:** 2026-04-16

## Pattern Overview

**Overall:** Modular multi-tier client-server architecture with AI-native capabilities, structured as a FastAPI backend exposing REST APIs and React 18 frontend consuming them. Core pattern is service-oriented architecture with functional programming in both layers.

**Key Characteristics:**
- **Agent-based routing** - Single chat endpoint routes to RAG, SQL, operations, or diagnostics based on intent recognition
- **Service layer separation** - Business logic isolated in services (RAG, SQL, Operations, Diagnosis), decoupled from HTTP routes
- **Vector-database integration** - pgvector for semantic search via PostgreSQL, supporting RAG retrieval
- **Intent-driven dispatch** - LLM-based intent recognition determines which tool chain executes
- **Functional frontend** - React components use hooks exclusively (no classes), with lazy-loaded pages for code splitting

## Layers

**API Layer (Request/Response):**
- Purpose: HTTP endpoints that accept user requests and return typed responses
- Location: `backend/app/api/` (documents.py, chat.py, query.py, operations.py, diagnosis.py, products.py)
- Contains: Route handlers using FastAPI decorator pattern, request/response validation via Pydantic schemas
- Depends on: Service layer, database layer
- Used by: Frontend SPA

**Service Layer (Business Logic):**
- Purpose: Implement core AI workflows (RAG retrieval, SQL generation, operation execution, diagnosis)
- Location: `backend/app/services/`
- Contains: 
  - `agent_service.py` - Intent recognition and multi-tool routing
  - `rag_service.py` - Document retrieval with pgvector similarity search
  - `sql_service.py` - NL-to-SQL generation and query execution
  - `operation_service.py` - Template-based operation execution and logging
  - `diagnosis_service.py` - Metric analysis and diagnostics
- Depends on: LLM client, database models, database sessions
- Used by: API layer

**Database Layer:**
- Purpose: Data persistence and vector storage
- Location: `backend/app/core/database.py` (engine/session management), `backend/app/models/db_models.py` (ORM models)
- Contains: SQLAlchemy ORM models for documents, chunks, orders, products, users, operations, metrics, caching
- Depends on: PostgreSQL/SQLite engine configured via SQLAlchemy
- Used by: Services that query/persist data

**Frontend Layer:**
- Purpose: User interface for all four capabilities (Dashboard, Documents/RAG, DataQuery, SmartOps, Diagnosis, Products)
- Location: `frontend/src/` (pages, components, services, hooks)
- Contains: React components organized by feature, API client, hooks for state management
- Depends on: Backend API via `/api/*` endpoints
- Used by: End users via browser

**LLM Integration Layer:**
- Purpose: Abstraction over LLM providers (DuBao, Qwen) and embedding generation
- Location: `backend/app/core/llm.py`
- Contains: Async HTTP clients for text generation and embeddings, provider-agnostic interface
- Depends on: External LLM API (configured via env vars)
- Used by: Agent service, RAG service, SQL service

## Data Flow

**Knowledge Q&A (RAG) Flow:**

1. User submits question in ChatPanel (`frontend/src/components/AGUI/ChatPanel.tsx`)
2. POST `/api/chat` with question and optional session_id
3. Agent service recognizes intent as "knowledge_qa" 
4. RAG service generates embedding for question via LLM
5. pgvector performs cosine similarity search on `document_chunks_with_vectors` table
6. Retrieved chunks (top-k=5) joined with document metadata
7. LLM generates answer based on retrieved context
8. Response includes answer, source references (title/filename/relevance %), confidence score
9. Frontend renders answer with source tags and confidence indicator

**Data Query (SQL) Flow:**

1. User enters natural language query in DataQuery page (`frontend/src/pages/DataQuery.tsx`)
2. POST `/api/query` with natural_language_query
3. SQL service generates SQL via LLM (with schema context)
4. Safety check: only SELECT allowed
5. Query executed via SQLAlchemy on configured database
6. Chart type inferred from query (line, bar, pie, table)
7. Results returned as JSON array of records + execution time
8. Frontend renders appropriate Recharts visualization

**Smart Operations (Execution) Flow:**

1. SmartOps page loads templates via GET `/api/operations/templates`
2. User selects template and clicks execute
3. POST `/api/operations/execute` with operation_type and parameters
4. Operation service executes operation (delegates to specific handler)
5. Result logged to `operations_log` table
6. Response includes status (success/failed) and result details
7. Logs fetched via GET `/api/operations/logs` and displayed in timeline

**State Management:**
- Frontend: Local component state via `useState`, API calls via `axios` or custom `useApiCall` hook
- Backend: No persistent sessions; stateless design via session_id parameter
- Database: SQLAlchemy manages connections via dependency injection (`Depends(get_db)`)
- Vector search: pgvector handles similarity calculations in PostgreSQL

## Key Abstractions

**Agent (Intent Router):**
- Purpose: Determine which tool chain (RAG, SQL, Operations, Diagnosis) should handle a user message
- Examples: `backend/app/services/agent_service.py`
- Pattern: LLM-based intent classification → switch/case routing to specialized handlers

**RAG Service (Retrieval Augmented Generation):**
- Purpose: Retrieve relevant documents and generate contextual answers
- Examples: `backend/app/services/rag_service.py`, `backend/app/api/documents.py`
- Pattern: Generate embedding → pgvector similarity search → LLM answer generation

**SQL Service (Natural Language to SQL):**
- Purpose: Convert natural language queries to executable SQL
- Examples: `backend/app/services/sql_service.py`, `backend/app/api/query.py`
- Pattern: LLM code generation → safety validation → SQLAlchemy execution

**Document Upload & Chunking:**
- Purpose: Ingest documents, extract text, split into chunks, and vectorize
- Examples: `backend/app/api/documents.py` (upload_document endpoint)
- Pattern: File parsing (PDF/DOCX/TXT) → text extraction → sliding window chunking → embedding generation → pgvector storage

**Source Reference:**
- Purpose: Track origin of RAG-retrieved information
- Examples: `backend/app/models/schemas.py` (SourceReference), frontend rendering in `ChatPanel.tsx`
- Pattern: Store document_id, chunk_index, relevance score, filename; format as percentage for UI

## Entry Points

**Backend:**
- Location: `backend/app/main.py`
- Triggers: Server startup (uvicorn or Vercel serverless)
- Responsibilities: Register API routes, configure CORS middleware, serve frontend static files (if built), health check

**Frontend:**
- Location: `frontend/src/main.tsx`
- Triggers: Browser page load
- Responsibilities: Initialize React root, apply Ant Design theme (dark mode, Chinese locale, custom token colors), initialize Web Vitals monitoring

**API Routes (Primary Entry Points for Features):**
- `POST /api/chat` - Entry for knowledge Q&A via agent routing
- `POST /api/documents/upload` - Entry for RAG ingestion
- `GET /api/documents` - List uploaded documents
- `POST /api/query` - Entry for data query
- `GET /api/operations/templates` - List available operations
- `POST /api/operations/execute` - Entry for smart operations
- `GET /api/diagnosis/summary` - Entry for business diagnosis

## Error Handling

**Strategy:** Consistent HTTP status codes + exception propagation to clients

**Patterns:**

**Backend (FastAPI):**
- Validation errors: Pydantic raises `ValidationError` → FastAPI returns 422 with detail
- Not found: Explicit `HTTPException(status_code=404, detail="..."`)`
- Authorization: JWT validation in middleware (placeholder for future)
- LLM failures: Caught in service layer, logged to stdout, fallback to example SQL or error message
- Database failures: SQLAlchemy exceptions propagated to caller, logged with traceback
- Global handler: `app.exception_handler(Exception)` catches unhandled errors → 500 + error type/message

**Frontend:**
- Network errors: `axios` interceptor catches, logged via `message.error()`
- API errors: Extract `error.response?.data?.detail` and display to user
- Retry logic: `fetchWithRetry` in `api.ts` implements exponential backoff for transient failures
- Fallback: If query/chat fails, empty results shown with error message

## Cross-Cutting Concerns

**Logging:**
- Backend: Python `print()` statements with emoji prefixes (✓, ❌, 🎯, etc.) for status visualization
- Frontend: Console logs in dev mode only (check `!import.meta.env.PROD`), no logs in production
- Example: `console.log([API] GET /health (125ms))`

**Validation:**
- Backend: Pydantic schemas enforce input types and constraints at API boundary
  - Example: `ChatRequest` enforces `question` is 1-2000 chars, `top_k` is 1-20
- Frontend: Form validation via Ant Design Form component, client-side checks before submission
- Database: SQLAlchemy column constraints (nullable, unique, foreign keys)

**Authentication:**
- Currently: No authentication implemented (open API)
- Placeholder: `settings.secret_key` + JWT settings in config
- Future: Middleware for token validation in `backend/app/middleware/`

**Rate Limiting:**
- Currently: Not implemented
- Vector DB: pgvector queries limited by default connection pool (pool_size=10, max_overflow=20)
- File upload: `settings.max_upload_size` enforced (50MB default)

**Caching:**
- Database: `QueryCache` table defined but not actively used
- Frontend: HTTP caching via Vite's asset fingerprinting (`.../dist/assets/*.js?hash`)
- LLM: No caching of embeddings/text generation (each call fresh)

---

*Architecture analysis: 2026-04-16*
