# Codebase Concerns

**Analysis Date:** 2026-04-16

## Tech Debt

**Frontend API Communication Pattern:**
- Issue: Scattered API_BASE extraction duplicated across multiple page components (`src/pages/DataQuery.tsx:29`, `src/pages/Products.tsx:40`, `src/pages/SmartOps.tsx:33`)
- Files: `frontend/src/pages/DataQuery.tsx`, `frontend/src/pages/Products.tsx`, `frontend/src/pages/SmartOps.tsx`
- Impact: Difficult to maintain centralized API configuration; environment variable changes require updates in multiple files
- Fix approach: Create centralized API client utility with configurable base URL, import and use in all page components

**Untyped `any` in Frontend:**
- Issue: Heavy use of `any` type casting (`src/pages/DataQuery.tsx:12`, `Products.tsx:47`, `SmartOps.tsx:49`)
- Files: `frontend/src/pages/DataQuery.tsx`, `frontend/src/pages/Products.tsx`, `frontend/src/pages/SmartOps.tsx`
- Impact: Loss of TypeScript type safety; difficult to catch bugs at compile time
- Fix approach: Define proper TypeScript interfaces for API responses (QueryResponse, OperationResponse, etc.)

**Mock Error Handling with Silent Fallbacks:**
- Issue: Embedding API failures silently fall back to mock implementation without user awareness (`backend/app/core/llm.py:98-101`)
- Files: `backend/app/core/llm.py`
- Impact: Data quality degradation invisible to users; vector search quality silently degrades to deterministic mocks
- Fix approach: Log warnings to user-facing service, add telemetry tracking, implement fallback notification mechanism

**Raw Database Access via `text()` SQL:**
- Issue: Direct SQL string execution without prepared statements in batch operations (`backend/app/services/operation_service.py:171-178`)
- Files: `backend/app/services/operation_service.py`
- Impact: Potential SQL injection vulnerability; bypasses ORM protections
- Fix approach: Replace `text()` queries with SQLAlchemy ORM bulk_update_mappings or parameterized queries

**Incomplete Authentication:**
- Issue: No JWT/token validation on any endpoints; default user_id=1 hardcoded (`backend/app/services/operation_service.py:23`, `backend/app/api/operations.py:18-27`)
- Files: `backend/app/services/operation_service.py`, `backend/app/api/operations.py`, `backend/app/main.py`
- Impact: No access control; any user can execute operations as user_id=1; audit trails cannot identify actual user
- Fix approach: Implement FastAPI security with JWT tokens, extract user_id from token in all operation endpoints

## Known Bugs

**Query History API Not Implemented:**
- Symptoms: Returns hardcoded empty response
- Files: `backend/app/api/query.py:43-52`
- Trigger: Calling `GET /api/query/history`
- Impact: Users cannot view past queries; feature appears to work but provides no data
- Workaround: Query retrieval must be built before production use

**Chat History Not Persisted:**
- Symptoms: Returns hardcoded empty messages
- Files: `backend/app/api/chat.py:28-37`
- Trigger: Calling `GET /api/chat/history/{session_id}`
- Impact: Users lose conversation context on page refresh; no audit trail of conversations
- Workaround: None; conversation history must be persisted

**Operation Rollback/Delete Buttons Non-Functional:**
- Symptoms: Buttons render but have no `onClick` handlers or are unimplemented
- Files: `frontend/src/pages/SmartOps.tsx:169-174`
- Trigger: Clicking "回滚" or "删除" buttons
- Impact: Users expect to undo/delete operations but UI is non-functional
- Workaround: None; backend endpoints do not exist

**Export Query Result API Not Implemented:**
- Symptoms: Returns hardcoded response with placeholder URL
- Files: `backend/app/api/query.py:55-66`
- Trigger: Calling `POST /api/query/{query_id}/export`
- Impact: Export feature appears to work but generates no actual files
- Workaround: Frontend CSV/JSON export in `DataQuery.tsx` works client-side; API export ignored

**SmartOps Execute Without Parameters:**
- Symptoms: Operations execute with empty `parameters: {}` dictionary
- Files: `frontend/src/pages/SmartOps.tsx:75-78`
- Trigger: Clicking any operation template button
- Impact: Operations execute with no user-provided parameters; relies on sensible backend defaults
- Workaround: Backend implements auto-mode for operations (e.g., `batch_update_stock` auto-restocks items < 10)

## Security Considerations

**CORS Wildcard Pattern:**
- Risk: `allow_origins: ["https://*.vercel.app"]` is overly permissive
- Files: `backend/app/main.py:21-30`
- Current mitigation: None (pattern allows any Vercel subdomain)
- Recommendations: 
  - Replace with explicit list of allowed origins
  - Use environment variable for CORS origins in production
  - Remove wildcard pattern; explicitly whitelist deployed frontend URL

**No Rate Limiting:**
- Risk: Any client can spam endpoints with unlimited requests
- Files: All API endpoints in `backend/app/api/`
- Current mitigation: None
- Recommendations:
  - Implement FastAPI rate limiting middleware
  - Add per-IP request throttling
  - Implement operation cost limits (e.g., max 10 batch updates/min)

**No Input Validation on SQL Queries:**
- Risk: LLM-generated SQL may be incorrect or malicious
- Files: `backend/app/services/sql_service.py:44-48`
- Current mitigation: Basic check for SELECT-only prefix
- Recommendations:
  - Implement SQL AST parsing to validate query safety
  - Add query timeout to prevent infinite loops
  - Implement result size limits (max 10k rows returned)
  - Log all executed queries with user ID

**Embedded Credentials Risk:**
- Risk: `.env.production` file exists in git history (modified: `frontend/.env.production`)
- Files: `frontend/.env.production`
- Current mitigation: VITE_API_URL is empty string (relative URL); no secrets stored
- Recommendations:
  - Remove `.env.production` from git; add to `.gitignore`
  - Use environment variables injected at deployment time
  - Add pre-commit hook to prevent secrets in committed files

**No Encryption for Sensitive Data:**
- Risk: Product prices and order amounts stored in plaintext; price history not encrypted
- Files: `backend/app/models/db_models.py:50`, `ProductPriceHistory` model
- Current mitigation: None
- Recommendations:
  - Encrypt sensitive fields at application layer for regulated data
  - Implement audit logging for all price/amount modifications
  - Add database-level encryption for financial data

**Operation Execution Without Approval Workflow:**
- Risk: Any user can approve orders, modify prices, process refunds via chat
- Files: `backend/app/services/agent_service.py:408-463`, `backend/app/services/operation_service.py:92-277`
- Current mitigation: Operations logged but no approval required
- Recommendations:
  - Implement role-based access control (RBAC)
  - Require human approval for sensitive operations (price > 20%, refunds, batch updates)
  - Add notification system for pending approvals
  - Implement operation confirmation workflow

## Performance Bottlenecks

**RAG Vector Search Inefficiency:**
- Problem: Full table scan for every query with no indexing on embeddings
- Files: `backend/app/services/rag_service.py:49-52`
- Cause: pgvector index not created on `document_chunks_with_vectors.embedding` column
- Improvement path:
  - Add pgvector HNSW index: `CREATE INDEX ON document_chunks_with_vectors USING hnsw (embedding vector_cosine_ops)`
  - Add query result caching with TTL
  - Implement batched embedding generation for bulk uploads

**SQL Generation + Execution Per Query:**
- Problem: Every query triggers LLM API call (30s+ latency) even for repeated questions
- Files: `backend/app/api/query.py:12-39`, `backend/app/services/sql_service.py:52-80`
- Cause: No query caching; all queries routed through LLM
- Improvement path:
  - Implement query cache on `QueryCache` table with hash-based lookup
  - Cache generated SQL for 24 hours
  - Add query similarity detection to reuse cached SQL for similar questions

**N+1 Product Queries in Operations:**
- Problem: `_update_product_price` performs multiple queries to find product by SKU/name
- Files: `backend/app/services/operation_service.py:213-247`
- Cause: Sequential queries with regex matching
- Improvement path:
  - Implement full-text search on product name + SKU
  - Pre-load product lookup cache
  - Batch product updates to single query

**Embedding Dimension Mismatch Truncation:**
- Problem: Qwen embeddings (1536D) truncated to 768D causes loss of information
- Files: `backend/app/api/documents.py:132`, `backend/app/services/rag_service.py:24`
- Cause: pgvector database schema hardcoded to 768D
- Improvement path:
  - Upgrade database schema to support 1536D or match model output
  - Profile quality difference between 768D and 1536D vectors
  - Consider implementing dimensionality reduction via PCA instead of truncation

**Frontend Pagination All-in-Memory:**
- Problem: Ant Design Table loads all results in memory; no server-side pagination
- Files: `frontend/src/pages/DataQuery.tsx:239-254`, `frontend/src/pages/Products.tsx:176-182`
- Cause: Results from `sql_service.execute_query()` not paginated
- Improvement path:
  - Implement server-side pagination with limit/offset
  - Add cursor-based pagination for better performance
  - Stream large result sets to frontend

## Fragile Areas

**Chart Type Detection via Keyword Matching:**
- Files: `backend/app/services/sql_service.py:82-95`
- Why fragile: Brittle Chinese keyword matching; fails for synonyms, variations, or English queries
- Safe modification: Implement chart type detection via LLM or data analysis (check result column count/types)
- Test coverage: No tests for edge cases (English queries, domain-specific terms)

**Operation Parameter Parsing via Regex:**
- Files: `backend/app/services/agent_service.py:408-463`
- Why fragile: Regex patterns hardcoded for specific formats; fails for varied user input
- Safe modification: Use LLM for structured extraction of operation parameters; add validation layer
- Test coverage: No tests for natural language variations

**Mock Embedding Fallback:**
- Files: `backend/app/core/llm.py:103-113`
- Why fragile: Deterministic hash-based mock produces consistent but meaningless vectors; degrades RAG quality silently
- Safe modification: Add explicit user notification; implement graceful degradation warning
- Test coverage: No tests validating mock vector quality impact

**Frontend State Management with useState:**
- Files: `frontend/src/pages/DataQuery.tsx`, `frontend/src/pages/Products.tsx`, `frontend/src/pages/SmartOps.tsx`
- Why fragile: No centralized state; complex async flows with multiple setters; race conditions possible between API calls
- Safe modification: Migrate to Context API or state management library (e.g., Redux); add request cancellation for stale responses
- Test coverage: No unit tests for async state flows

**Database Connection Pool for SQLite:**
- Files: `backend/app/core/database.py:7-13`
- Why fragile: SQLite connection string uses `check_same_thread=False` which is unsafe for concurrent writes
- Safe modification: Switch to PostgreSQL for production; implement proper connection pooling
- Test coverage: No load tests for concurrent operations

## Scaling Limits

**File Storage on Filesystem:**
- Current capacity: Depends on available disk space; default `./uploads` directory
- Limit: Local filesystem storage doesn't scale across multiple servers; no cloud sync
- Scaling path:
  - Implement S3-compatible object storage (Vercel Blob, AWS S3)
  - Migrate file references to object storage keys
  - Remove local filesystem uploads in production

**Embedding API Rate Limits:**
- Current capacity: Batch embedding generation limited by Dashscope/Qwen API quotas
- Limit: Document upload slowed by sequential embedding calls; bulk import blocks
- Scaling path:
  - Implement batch embedding API calls (if provider supports)
  - Add embedding queue with background workers
  - Implement prioritized queue for user uploads vs. admin bulk operations

**Database Concurrent Write Contention:**
- Current capacity: SQLite supports 1 writer at a time
- Limit: Multiple simultaneous price updates or order approvals will block
- Scaling path:
  - Migrate to PostgreSQL with row-level locking
  - Implement optimistic concurrency control with version columns
  - Add conflict resolution strategy for concurrent edits

**Session Storage Not Persistent:**
- Current capacity: Chat sessions exist only in memory; lost on server restart
- Limit: Cannot scale across multiple backend instances
- Scaling path:
  - Implement Redis-backed session storage
  - Add session table to database for persistence
  - Implement session recovery on server restart

## Dependencies at Risk

**Dashscope SDK:**
- Risk: Heavy reliance on single proprietary LLM provider (Doubao/Qwen); no abstraction layer
- Files: `backend/app/core/llm.py:6`, `backend/requirements.txt:16`
- Impact: If Dashscope API becomes unavailable or pricing changes, entire system breaks
- Migration plan:
  - Implement LLM provider abstraction (factory pattern)
  - Add support for OpenAI, Anthropic as fallbacks
  - Add circuit breaker for provider failures

**PyPDF2:**
- Risk: Outdated PDF parsing library; known issues with complex PDFs
- Files: `backend/app/api/documents.py:12`, `backend/requirements.txt:14`
- Impact: Document extraction fails silently for embedded fonts, scanned PDFs
- Migration plan:
  - Evaluate `pdfplumber` or `pypdfium2` for better PDF support
  - Add PDF validation before processing
  - Implement fallback to OCR for scanned PDFs

**pgvector:**
- Risk: Requires PostgreSQL extension; not all hosting providers support it
- Files: `backend/requirements.txt:10`
- Impact: Cannot use managed PostgreSQL without extension support (e.g., some MySQL hosts)
- Migration plan:
  - Document PostgreSQL version requirements (13.0+)
  - Add migration guide for extension installation
  - Evaluate vector DB alternatives (Milvus, Weaviate, Pinecone)

## Missing Critical Features

**No Audit Logging:**
- Problem: Operations execute without recording WHO changed WHAT and WHEN
- Blocks: Compliance, security investigation, accountability
- Priority: HIGH - Regulatory requirement for financial operations

**No Approval Workflow:**
- Problem: Any user can approve orders, modify prices, process refunds
- Blocks: Risk management; cannot enforce separation of duties
- Priority: HIGH - Critical for enterprise approval processes

**No Data Backup/Recovery:**
- Problem: No backup strategy documented; database data at risk
- Blocks: Disaster recovery; regulatory compliance
- Priority: HIGH - Data loss would be catastrophic

**No Webhook Support for External Systems:**
- Problem: Order updates, price changes not visible to external systems
- Blocks: Integration with accounting, inventory management systems
- Priority: MEDIUM - Limits ecosystem connectivity

**No API Documentation:**
- Problem: No OpenAPI/Swagger docs for custom endpoints
- Blocks: Third-party integration; developer onboarding
- Priority: MEDIUM - Already available via FastAPI auto-docs at `/docs`

## Test Coverage Gaps

**SQL Generation Not Tested:**
- What's not tested: LLM-generated SQL correctness; fallback SQL examples
- Files: `backend/app/services/sql_service.py:13-50`
- Risk: Incorrect SQL silently returns empty results; no schema validation
- Priority: HIGH - Core feature

**Operation Execution Not Tested:**
- What's not tested: Price history recording; stock update logic; edge cases (duplicate executions)
- Files: `backend/app/services/operation_service.py:92-277`
- Risk: Undetected bugs in price updates affect financial data
- Priority: HIGH - Financial impact

**Frontend API Error Handling Not Tested:**
- What's not tested: Network errors, timeout handling, retry logic
- Files: `frontend/src/pages/DataQuery.tsx:25-48`, `frontend/src/pages/Products.tsx:42-51`
- Risk: Silent failures; users don't know if request succeeded
- Priority: MEDIUM - UX impact

**RAG Retrieval Quality Not Validated:**
- What's not tested: Vector search relevance; mock embedding quality impact
- Files: `backend/app/services/rag_service.py:17-76`
- Risk: Mock embeddings degrade search quality; no metrics to detect
- Priority: MEDIUM - Silent degradation

**Authentication Not Tested:**
- What's not tested: JWT token validation, unauthorized access rejection
- Files: None (authentication not implemented)
- Risk: Security bypass not caught until production incident
- Priority: CRITICAL - Security gap

---

*Concerns audit: 2026-04-16*
