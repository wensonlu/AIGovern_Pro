# Coding Conventions

**Analysis Date:** 2026-04-16

## Naming Patterns

**Files:**
- React components: PascalCase with .tsx extension (e.g., `DataQuery.tsx`, `ChatPanel.tsx`)
- Python modules: snake_case with .py extension (e.g., `sql_service.py`, `rag_service.py`)
- CSS modules: ComponentName.module.css (e.g., `DataQuery.module.css`, `AppLayout.module.css`)
- Index/barrel files: `index.ts` for exports in `frontend/src/components/Layout/index.ts`

**Functions:**
- TypeScript: camelCase for all functions (e.g., `handleQuery()`, `exportToCSV()`, `fetchWithRetry()`)
- Python: snake_case for functions (e.g., `generate_sql()`, `execute_query()`, `_get_default_schema()`)
- Private/internal functions: Python uses leading underscore convention `_method_name()` (e.g., `_infer_chart_type()`, `_get_example_sql()`)

**Variables:**
- TypeScript: camelCase (e.g., `const [query, setQuery]`, `let results`, `const loading`)
- Python: snake_case (e.g., `natural_query`, `chart_type`, `top_k`)
- Constants: ALL_CAPS (e.g., `MAX_RETRIES = 3`, `API_TIMEOUT`)

**Types:**
- TypeScript interfaces: PascalCase with prefix (e.g., `AppLayoutProps`, `UseApiCallOptions`, `SourceReference`, `ChatResponse`)
- Python type hints: Full annotations on functions (e.g., `async def generate_sql(self, natural_query: str, schema_context: Optional[str] = None) -> tuple[str, str]`)
- Generic types: Use Python 3.9+ style (e.g., `list[dict]`, `dict[str, Any]` instead of `List[Dict]`)

## Code Style

**Formatting:**

Frontend:
- Tool: Prettier
- Config file: `frontend/.prettierrc.json`
- Settings:
  - `semi: true` (semicolons required)
  - `singleQuote: true` (single quotes for JS/TS)
  - `printWidth: 100` (line width limit)
  - `tabWidth: 2` (2-space indentation)
  - `trailingComma: 'es5'` (trailing commas in ES5 objects/arrays)
  - `jsxSingleQuote: false` (double quotes for JSX attributes)
  - `endOfLine: 'lf'` (Unix line endings)

Backend:
- Python follows PEP 8 style
- Black formatter recommended (configured in project setup)
- 4-space indentation (Python standard)

**Linting:**

Frontend:
- Tool: ESLint
- Config file: `frontend/.eslintrc.json`
- Key rules:
  - `react/react-in-jsx-scope: off` (not needed in React 18+)
  - `@typescript-eslint/no-explicit-any: warn` (discourage use of `any`, but allow with warning)
  - `@typescript-eslint/no-unused-vars: warn` (warn on unused, but allow unused parameters starting with `_`)
  - `react-refresh/only-export-components: warn` (for Fast Refresh compatibility)
  - Extends: `eslint:recommended`, `plugin:react/recommended`, `plugin:react-hooks/recommended`, `plugin:@typescript-eslint/recommended`

Backend:
- Python linting: `isort`, `black`, `mypy` (pre-commit ready)
- Configuration: Handled by pre-commit hooks

## Import Organization

**Order:**

TypeScript (Frontend):
```typescript
// 1. React and framework imports
import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

// 2. UI library imports
import { Input, Button, Card, Table, Empty } from 'antd'
import { SendOutlined, CopyOutlined } from '@ant-design/icons'

// 3. Third-party library imports
import axios from 'axios'
import { LineChart, Line } from 'recharts'

// 4. Local component imports (relative)
import AppLayout from '../components/Layout'

// 5. Local services/hooks imports (relative or path aliases)
import { chatWithKnowledge } from '@services/api'
import { useApiCall } from '@hooks/useApiCall'

// 6. Style imports
import styles from './DataQuery.module.css'
```

Python (Backend):
```python
# 1. Standard library imports
from typing import Optional, Any
from datetime import datetime

# 2. Third-party imports (frameworks, libraries)
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. Local app imports
from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import QueryRequest, QueryResponse
from app.services.sql_service import sql_service
```

**Path Aliases:**

Frontend (configured in `tsconfig.json`):
- `@/*` → `src/*`
- `@components/*` → `src/components/*`
- `@pages/*` → `src/pages/*`
- `@hooks/*` → `src/hooks/*`
- `@services/*` → `src/services/*`
- `@utils/*` → `src/utils/*`
- `@types/*` → `src/types/*`

Use full path aliases in imports, not relative paths:
```typescript
// ✅ Correct
import { useApiCall } from '@hooks/useApiCall'
import ChatPanel from '@components/AGUI/ChatPanel'

// ❌ Avoid
import { useApiCall } from '../../hooks/useApiCall'
import ChatPanel from '../components/AGUI/ChatPanel'
```

## Error Handling

**TypeScript/Frontend Patterns:**

1. Try-catch with explicit type narrowing:
```typescript
try {
  const response = await axios.post(`${API_BASE}/api/query`, {
    natural_language_query: query,
  });
  setResults(response.data.result || []);
  message.success('Success message');
} catch (error: any) {
  message.error('Query failed: ' + (error.response?.data?.detail || error.message));
}
```

2. Error type checking in hooks:
```typescript
const error = err instanceof Error ? err : new Error(String(err));
setError(error);
if (options.showMessage !== false && error.message !== 'aborted') {
  const errorMsg = options.errorMessage || error.message || 'Default error';
  message.error(errorMsg);
}
```

3. Network error retry logic:
```typescript
function shouldRetry(error: any): boolean {
  if (error instanceof TypeError) return true; // Network error
  if (error.name === 'AbortError') return true; // Timeout
  return false;
}
```

**Python/Backend Patterns:**

1. Service-level validation with ValueError:
```python
async def execute_operation(
    self, operation_type: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    handler = self.operation_templates.get(operation_type)
    if not handler:
        raise ValueError(f"不支持的操作类型: {operation_type}")
```

2. SQL execution safety checks:
```python
async def execute_query(self, sql: str, db: Session) -> list[dict]:
    try:
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            raise ValueError("只允许执行 SELECT 查询")
        # Execute safely
        return processed_rows
    except Exception as e:
        raise RuntimeError(f"SQL 执行失败: {e}")
```

3. Operation execution with logging:
```python
try:
    result = await handler(parameters, db)
    log_entry.status = "success"
    log_entry.operation_detail = {"parameters": parameters, "result": result}
    return {"status": "success", "operation_id": log_entry.id, "result": result}
except Exception as e:
    log_entry.status = "failed"
    log_entry.operation_detail = {"parameters": parameters, "error": str(e)}
    return {"status": "failed", "operation_id": log_entry.id, "error": str(e)}
finally:
    db.close()
```

4. Global exception handler:
```python
# In app/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
```

## Logging

**Frontend Approach:**
- Tool: `console` (no external logger)
- Pattern: Development-only debug logging in services
```typescript
if (!import.meta.env.PROD) {
  console.log(`[API] ${method} ${endpoint}`, body ? `(payload: ...)` : '');
  console.log(`[API✓] ${method} ${endpoint} (${duration}ms)`);
  console.error(`[API✗] ${method} ${endpoint} (${duration}ms):`, error);
}
```

**Backend Approach:**
- Tool: `print()` or logging module (via settings)
- Pattern: Informational output for debugging
```python
print(f"❌ pgvector retrieval failed: {e}")
import traceback
traceback.print_exc()
```

**User Notifications:**
- Frontend: Use `message.success()`, `message.error()`, `message.warning()` from Ant Design
- Backend: Return error details in JSON response for frontend to display

## Comments

**When to Comment:**

1. Complex business logic - explain the "why":
```typescript
// 处理包含逗号或引号的值
const stringValue = value === null || value === undefined ? '' : String(value);
if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
  return `"${stringValue.replace(/"/g, '""')}"`;
}
```

2. Non-obvious algorithm decisions:
```python
# 截断到 768 维（与数据库列定义一致）
query_embedding_768 = query_embedding[:768] if len(query_embedding) > 768 else query_embedding
```

3. Workarounds or temporary solutions:
```python
# 如果没有 LLM API Key，直接使用示例 SQL
if not self.llm.api_key:
    chart_type = self._infer_chart_type(natural_query)
    example_sql = self._get_example_sql(natural_query)
    return example_sql, chart_type
```

**JSDoc/TSDoc:**

- Required for all exported functions and hooks
- Describe parameters and return types

```typescript
/**
 * 统一的 API 调用 Hook
 * 处理加载状态、错误处理、消息提示和重试
 */
export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiCallOptions<T> = {}
) { ... }

/**
 * 简化版 Hook - 仅用于简单的单次 API 调用
 */
export function useAsyncApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  _dependencies: any[] = []
) { ... }
```

Python docstrings:
```python
class SQLService:
    """SQL 生成与查询执行服务"""

    async def generate_sql(self, natural_query: str, schema_context: Optional[str] = None) -> tuple[str, str]:
        """从自然语言生成 SQL"""
```

## Function Design

**Size Guidelines:**
- Keep functions focused and under 50 lines when possible
- Large functions (>100 lines) should be broken into smaller utilities
- Example: `exportToCSV()` and `exportToJSON()` separated in `frontend/src/pages/DataQuery.tsx`

**Parameters:**
- Limit to 3-4 parameters; use objects for more:
```typescript
// ✅ Good: Options object
interface UseApiCallOptions<T = any> {
  successMessage?: string;
  errorMessage?: string;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiCallOptions<T> = {}
)
```

**Return Values:**
- Use typed returns always
- Async functions: always return `Promise<T>`
- Services: return wrapped responses with status info:
```python
# API operation response
return {
    "status": "success",
    "operation_id": log_entry.id,
    "operation_type": operation_type,
    "result": result,
    "timestamp": datetime.now().isoformat(),
}
```

## Module Design

**Exports:**

Frontend barrel files should aggregate related exports:
```typescript
// frontend/src/components/Layout/index.ts
export { default as AppLayout } from './AppLayout';
```

Backend router files use FastAPI router pattern:
```python
# backend/app/api/query.py
router = APIRouter(prefix="/api/query", tags=["query"])

@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest, db: Session = Depends(get_db)):
    ...
```

**Service Classes:**

- Create singleton instances at module level for dependency reuse
- Use dependency injection for testing:
```python
# backend/app/services/sql_service.py
class SQLService:
    def __init__(self):
        self.llm = llm_client

sql_service = SQLService()  # Singleton instance
```

- Backend services accept `Session` as parameter for transaction control:
```python
async def execute_operation(
    self, operation_type: str, parameters: dict[str, Any], user_id: int = 1
) -> dict[str, Any]:
    db = SessionLocal()  # Create session when needed
    try:
        # Work with db
        db.commit()
    finally:
        db.close()
```

**React Hooks:**

- Typed generic parameters for reusable hooks:
```typescript
export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options: UseApiCallOptions<T> = {}
) { ... }
```

- Return clear object with all state and methods:
```typescript
return {
  execute,
  retry,
  loading,
  error,
  data,
  cleanup,
  isError: error !== null,
  canRetry: canRetryState,
};
```

---

*Convention analysis: 2026-04-16*
