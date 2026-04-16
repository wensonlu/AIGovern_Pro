# External Integrations

**Analysis Date:** 2026-04-16

## APIs & External Services

**LLM (Large Language Model):**
- **Doubao (豆包)** - ByteDance LLM service
  - SDK/Client: Custom HTTP client via `httpx` (`backend/app/core/llm.py`)
  - Auth: `LLM_API_KEY` (env var from `backend/.env`)
  - Base URL: `https://ark.cn-beijing.volces.com/api/v3`
  - Default Model: `doubao-pro` (configured via `LLM_MODEL_NAME`)
  - Used for: Text generation in chat, SQL query generation (`backend/app/services/sql_service.py`, `backend/app/services/agent_service.py`)

- **Qwen (通义千问)** - Alibaba LLM service (alternative)
  - SDK/Client: DashScope SDK (`dashscope` package, `backend/app/core/llm.py`)
  - Auth: `LLM_API_KEY` (env var)
  - Base URL: `https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation`
  - Default Model: `qwen-plus` or `qwen-turbo`
  - Configuration: Via `LLM_PROVIDER=qwen` in env
  - Used for: Alternative LLM provider for text generation

**Embedding Models:**
- **Doubao Embedding** - ByteDance embedding service for RAG
  - SDK/Client: Custom HTTP client via `httpx` (`backend/app/core/llm.py`, line 115)
  - Auth: `EMBEDDING_API_KEY` (fallback to `LLM_API_KEY` if not set)
  - Base URL: `EMBEDDING_API_BASE` (defaults to `https://ark.cn-beijing.volces.com/api/v3`)
  - Model: `doubao-embedding-text-240715` (768-dimensional)
  - Used for: Vector embeddings for document chunks (`backend/app/services/rag_service.py`, line 21)

- **Qwen Embedding** - Alibaba embedding service for RAG (alternative)
  - SDK/Client: DashScope SDK (`dashscope.TextEmbedding`)
  - Auth: `EMBEDDING_API_KEY`
  - Sync API (wrapped in async via thread pool)
  - Used for: Alternative embedding provider when `EMBEDDING_PROVIDER=qwen`

## Data Storage

**Databases:**
- **PostgreSQL** (Production)
  - Connection: `DATABASE_URL` env var (e.g., `postgresql://user:pass@host:5432/db`)
  - Client: SQLAlchemy ORM (`sqlalchemy>=2.0.30`, `backend/app/models/`)
  - Connection pooling: Pool size 10, max overflow 20 (for non-SQLite)
  - Specific to AIGovern Pro:
    - **Supabase PostgreSQL** with pgvector extension (recommended for production)
    - Tables: `documents`, `document_chunks_with_vectors`, `chat_sessions`, `operations`, `products`
    - Vector column: `embedding` (type: `vector(768)` in pgvector)

- **SQLite** (Development default)
  - Connection: `sqlite:///./aigovern.db` (local file)
  - Usage: Default for `DATABASE_URL` if not set
  - Path: `backend/app/core/database.py` creates local database

**File Storage:**
- **Local Filesystem Only** - No cloud storage configured
  - Upload directory: `UPLOAD_DIR` env var (default: `./uploads`)
  - Supported formats: pdf, docx, txt, md (configured in `backend/app/core/config.py`, line 51)
  - Max size: `MAX_UPLOAD_SIZE=52428800` (50MB)
  - Processing: PyPDF2, python-docx libraries parse files (`backend/requirements.txt`)

**Caching:**
- **Redis** (Optional)
  - Connection: `REDIS_URL` env var (default: `redis://localhost:6379/0`)
  - Status: Configured but not actively used in current codebase
  - Potential use: Chat session caching, embedding cache

**Vector Database:**
- **pgvector** (PostgreSQL extension)
  - Integration: `pgvector>=0.3.0` library
  - Vector dimensions: 768 (configurable via `VECTOR_DIMENSIONS` env var)
  - Similarity metric: Cosine distance (default, configured via `VECTOR_SIMILARITY_METRIC`)
  - Used in: `backend/app/services/rag_service.py` (line 38-42) for document similarity search
  - Query type: Cosine similarity (`<=>` operator in pgvector SQL)

## Authentication & Identity

**Auth Provider:**
- **Custom JWT** (In-house implementation)
  - Implementation: Token generation in `backend/app/core/auth.py` (assumed)
  - Secret: `SECRET_KEY` env var (required, default placeholder in code)
  - Algorithm: HS256
  - Token lifetime: `ACCESS_TOKEN_EXPIRE_MINUTES` env var (default: 30 minutes)
  - Status: Partially implemented (JWT config in `backend/app/core/config.py` but not fully integrated in API endpoints)

**Currently:**
- No authentication enforcement on API endpoints (CORS allows public access)
- Internal use assumed (enterprise B2B context)

## Monitoring & Observability

**Error Tracking:**
- None detected - No Sentry, DataDog, or similar integration

**Logs:**
- **Console/stdout** approach
  - Logger level: `LOG_LEVEL` env var (default: INFO)
  - Backend: Print statements and exception handlers in `backend/app/main.py` (line 106)
  - Frontend: Browser console via `console.log`, `console.error` in `frontend/src/services/api.ts`
  - Deployment: Logs handled by Vercel runtime

**Health Checks:**
- **Health endpoint:** `GET /health` and `HEAD /health` in `backend/app/main.py`
- Returns: `{"status": "ok", "version": "0.1.0", "database": "pgvector"}`
- Frontend health check: `checkHealth()` in `frontend/src/services/api.ts` (line 156)

## CI/CD & Deployment

**Hosting:**
- **Vercel** (Serverless platform)
  - Backend: Serverless function deployment via Mangum adapter (`backend/vercel.json`)
  - Frontend: Static site deployment
  - Build command: `tsc && vite build` (frontend), `pip install -r requirements.txt` (backend)
  - Env vars: Set in Vercel project settings (not version controlled)

**CI Pipeline:**
- None detected - No GitHub Actions, GitLab CI, or other CI service configured
- Manual deployment via `git push` to Vercel (connected repo)

**Deployment File Locations:**
- `backend/vercel.json` - Backend serverless configuration
- `frontend/vercel.json` - (Not explicitly shown but implied)
- `backend/docker-compose.yml` - Local development compose file (Milvus vector DB, but not used in current deployment)

## Environment Configuration

**Required env vars (Backend):**
- `LLM_API_KEY` - API key for Doubao or Qwen
- `DATABASE_URL` - PostgreSQL connection string (production)
- `EMBEDDING_API_KEY` - (Optional if using LLM_API_KEY for embedding)
- `SECRET_KEY` - JWT signing key (production must change from default)

**Optional env vars (Backend):**
- `REDIS_URL` - Redis connection string
- `LLM_PROVIDER` - `doubao` or `qwen` (default: doubao)
- `EMBEDDING_PROVIDER` - `doubao` or `qwen` (default: falls back to LLM_PROVIDER)
- `PORT`, `HOST` - Server binding (default: 0.0.0.0:8000)
- `DEBUG` - Debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

**Required env vars (Frontend):**
- `VITE_API_URL` - Backend API base URL
  - Development: `http://localhost:8000` (default)
  - Production: `` (empty string, relative path for same-domain deployment)
- `VITE_API_TIMEOUT` - Request timeout in ms (default: 30000)

**Secrets location:**
- Backend: `.env` file in `backend/` directory (git-ignored)
- Frontend: `.env.production` in `frontend/` directory (git-ignored)
- Vercel: Environment variables set in Vercel project dashboard
- Template: `backend/.env.example` and `frontend/.env.example` provided

## Webhooks & Callbacks

**Incoming:**
- None detected - No webhook endpoints defined

**Outgoing:**
- None detected - No external webhooks called

## CORS Configuration

**Allowed Origins** (`backend/app/main.py`, line 21-27):
- `http://localhost:3000` - Frontend dev server (default React)
- `http://localhost:3001` - Frontend dev server (custom port)
- `http://localhost:5173` - Vite dev server
- `https://ai-govern-pro.vercel.app` - Production Vercel domain (hardcoded)
- `https://*.vercel.app` - All Vercel preview deployments

**Credentials:** Allowed
**Methods:** All (`*`)
**Headers:** All (`*`)

## Frontend API Communication

**HTTP Client:**
- **Fetch API** (native, not Axios as package.json suggests)
  - Implementation: `frontend/src/services/api.ts` (line 86-117)
  - Timeout: `API_TIMEOUT` from env (default 30s)
  - Retry logic: Up to 3 exponential backoff retries for network errors
  - Error handling: Comprehensive error logging and recovery

**Endpoints Used:**
- `POST /api/chat` - Chat/RAG queries
- `POST /api/query` - Data queries (SQL generation)
- `GET /api/operations/templates` - Operation templates
- `POST /api/operations/{type}/execute` - Execute operations
- `GET /api/diagnosis/summary` - Diagnostics summary
- `GET /api/diagnosis/metrics` - Diagnostics metrics
- `GET /api/diagnosis/analyze/{metric}` - Metric analysis
- `GET /health` - Health check

## Deployment Architecture

**Production Topology:**
```
Client Browser
  ↓
Vercel CDN (Static Frontend)
  ↓ /api/* requests
Vercel Serverless (Backend - Mangum)
  ↓
PostgreSQL (Supabase with pgvector)
  ↓ Vector queries
  LLM API (Doubao or Qwen via HTTPS)
  ↓
Response
```

**Local Development Topology:**
```
Frontend Dev Server (Vite :3000)
  ↓ /api/* (proxied)
Backend Dev Server (Uvicorn :8000)
  ↓ (optional Redis :6379)
SQLite DB | PostgreSQL
  ↓
LLM API (Doubao/Qwen)
```

---

*Integration audit: 2026-04-16*
