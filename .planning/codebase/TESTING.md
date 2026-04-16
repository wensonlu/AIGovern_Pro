# Testing Patterns

**Analysis Date:** 2026-04-16

## Test Framework

**Runner:**
- Frontend: Vitest 0.34.6
- Backend: pytest 7.4.4 + pytest-asyncio 0.23.0
- Config: Backend has requirements in `backend/requirements.txt`

**Assertion Library:**
- Frontend: Vitest built-in assertions
- Backend: pytest assertions and pytest fixtures

**Run Commands:**

Frontend:
```bash
cd frontend && pnpm test              # Run all tests with Vitest
cd frontend && pnpm test --watch      # Watch mode
cd frontend && pnpm test --coverage   # Coverage report
```

Backend:
```bash
cd backend && python -m pytest                    # Run all tests
cd backend && python -m pytest -v                 # Verbose output
cd backend && python -m pytest --asyncio-mode=auto  # Auto async mode
cd backend && python -m pytest -k "test_name"    # Run specific test
```

## Test File Organization

**Location:**

Frontend:
- Currently NO test files exist in the codebase
- Recommended location: Co-located with components (sibling pattern)
- Example structure: `src/pages/DataQuery.tsx` → `src/pages/DataQuery.test.tsx`

Backend:
- Currently NO test files exist in the codebase
- Recommended location: `backend/tests/` directory with mirrors of `app/` structure
- Example structure:
  ```
  backend/
  ├── app/
  │   ├── api/
  │   │   └── query.py
  │   └── services/
  │       └── sql_service.py
  └── tests/
      ├── api/
      │   └── test_query.py
      └── services/
          └── test_sql_service.py
  ```

**Naming:**
- Frontend: `ComponentName.test.tsx`
- Backend: `test_module_name.py`

**Test Directory Structure:**

Backend structure should mirror production code:
```
backend/tests/
├── conftest.py                    # Shared fixtures and configuration
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── test_chat.py
│   ├── test_documents.py
│   ├── test_operations.py
│   ├── test_query.py
│   └── test_diagnosis.py
├── services/
│   ├── __init__.py
│   ├── test_rag_service.py
│   ├── test_sql_service.py
│   ├── test_operation_service.py
│   └── test_agent_service.py
└── core/
    ├── __init__.py
    └── test_llm.py
```

## Test Structure

**Frontend Suite Organization:**

Recommended pattern (not yet implemented):
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DataQuery from './DataQuery'

describe('DataQuery Component', () => {
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    user = userEvent.setup()
  })

  describe('rendering', () => {
    it('should display loading skeleton on initial load', () => {
      render(<DataQuery />)
      expect(screen.getByTestId('skeleton-loading')).toBeInTheDocument()
    })
  })

  describe('user interactions', () => {
    it('should submit query when send button is clicked', async () => {
      render(<DataQuery />)
      const input = screen.getByPlaceholderText(/输入你的查询问题/)
      await user.type(input, 'Test query')
      await user.click(screen.getByText('查询'))
      // Assert query was sent
    })
  })

  describe('error handling', () => {
    it('should show error message on query failure', async () => {
      render(<DataQuery />)
      // Setup mock to fail
      // Trigger error scenario
      expect(screen.getByText(/查询失败/)).toBeInTheDocument()
    })
  })
})
```

**Backend Test Suite Organization:**

Recommended pattern (not yet implemented):
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

class TestQueryAPI:
    """Tests for /api/query endpoint"""

    def test_execute_query_success(self, client: TestClient, db: Session):
        """Should execute valid query and return results"""
        response = client.post('/api/query', json={
            'natural_language_query': 'recent orders'
        })
        assert response.status_code == 200
        assert 'sql' in response.json()
        assert 'result' in response.json()

    def test_execute_query_invalid_input(self, client: TestClient):
        """Should reject empty query"""
        response = client.post('/api/query', json={
            'natural_language_query': ''
        })
        assert response.status_code == 422  # Validation error
```

**Patterns:**

Frontend setup/teardown (when tests exist):
```typescript
// Setup: Create test fixtures, mock APIs before each test
beforeEach(() => {
  // Mock API responses
  vi.mock('@services/api', () => ({
    queryData: vi.fn().mockResolvedValue({
      sql: 'SELECT * FROM orders',
      result: [],
      chart_type: 'line'
    })
  }))
})

// Teardown: Clean up mocks and state after each test
afterEach(() => {
  vi.clearAllMocks()
})
```

Backend setup/teardown (recommended pattern):
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='function')
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()

@pytest.fixture(scope='function', autouse=True)
def reset_mocks():
    """Reset all mocks between tests"""
    yield
    # Cleanup code here
```

## Mocking

**Frontend Framework:**
- Tool: Vitest (built-in with `vi` object)
- Pattern examples from codebase intention:
```typescript
// Mock API service
vi.mock('@services/api', () => ({
  chatWithKnowledge: vi.fn().mockResolvedValue({
    answer: 'Test answer',
    sources: [],
    confidence: 0.95,
    session_id: 'test-session',
    timestamp: new Date().toISOString()
  })
}))

// Mock Ant Design components if needed
vi.mock('antd', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))
```

**Backend Framework:**
- Tool: unittest.mock or pytest-mock
- Pattern for mocking external services:
```python
from unittest.mock import patch, AsyncMock
import pytest

@pytest.mark.asyncio
async def test_sql_generation_with_mock_llm():
    """Should generate SQL even when LLM fails"""
    with patch('app.services.sql_service.llm_client') as mock_llm:
        mock_llm.api_key = None  # Simulate no API key
        
        service = SQLService()
        sql, chart_type = await service.generate_sql('recent orders')
        
        assert sql.upper().startswith('SELECT')
        assert chart_type in ['bar', 'line', 'pie', 'scatter', 'table']

@pytest.mark.asyncio
async def test_rag_retrieval_with_mock_db():
    """Should handle database errors gracefully"""
    with patch('app.services.rag_service.SessionLocal') as mock_session:
        mock_session.return_value.execute.side_effect = Exception('DB error')
        
        service = RAGService()
        results = await service.retrieve_documents('test query')
        
        assert results == []  # Should return empty on error
```

**What to Mock:**

✅ Mock:
- External API calls (LLM APIs, embedding services)
- Database operations (for unit tests)
- File system operations
- Time-dependent functions

❌ Don't Mock:
- Core business logic (validate the actual algorithm)
- Error handling paths (test real exception behavior)
- Type definitions and interfaces

**Pattern - Testing API endpoints with mocked services:**

Frontend (Vitest + React Testing Library):
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

it('should display results after query', async () => {
  const mockQueryData = vi.fn().mockResolvedValueOnce({
    sql: 'SELECT * FROM orders',
    result: [{ id: 1, amount: 100 }],
    chart_type: 'bar',
    rows_count: 1,
    execution_time: 0.5
  })

  vi.mock('@services/api', () => ({ queryData: mockQueryData }))
  
  render(<DataQuery />)
  const input = screen.getByPlaceholderText(/输入你的查询问题/)
  await userEvent.type(input, 'test query')
  await userEvent.click(screen.getByText('查询'))
  
  await waitFor(() => {
    expect(screen.getByText(/总数据行数/)).toBeInTheDocument()
  })
})
```

Backend (pytest + FastAPI TestClient):
```python
@pytest.mark.asyncio
def test_query_endpoint(client: TestClient):
    """Test /api/query endpoint"""
    with patch('app.services.sql_service.sql_service') as mock_service:
        mock_service.generate_sql.return_value = (
            'SELECT * FROM orders LIMIT 10',
            'table'
        )
        mock_service.execute_query.return_value = [
            {'id': 1, 'amount': 100}
        ]
        
        response = client.post('/api/query', json={
            'natural_language_query': 'recent orders'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'sql' in data
        assert 'result' in data
```

## Fixtures and Factories

**Test Data:**

Frontend fixture pattern (when implemented):
```typescript
// tests/fixtures/mockData.ts
export const mockChatResponse = {
  answer: 'Test answer about orders',
  sources: [
    {
      document_id: 1,
      title: 'Order Documentation',
      filename: 'orders.pdf',
      chunk_index: 0,
      relevance: 0.95,
      relevance_percentage: '95%',
      text_preview: 'This is a preview of the source text...'
    }
  ],
  confidence: 0.85,
  session_id: 'test-session',
  timestamp: '2026-04-16T10:00:00Z'
}

export const mockQueryResponse = {
  sql: 'SELECT DATE(created_at) as date, COUNT(*) as order_count FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL \'7 days\' GROUP BY DATE(created_at) ORDER BY date',
  result: [
    { date: '2026-04-10', order_count: 15 },
    { date: '2026-04-11', order_count: 22 },
    { date: '2026-04-12', order_count: 18 }
  ],
  chart_type: 'line',
  rows_count: 3,
  execution_time: 0.234
}
```

Backend fixture pattern (recommended):
```python
# tests/conftest.py
import pytest
from datetime import datetime
from app.models.db_models import Order, User, Product

@pytest.fixture
def sample_user_data():
    """Factory for user test data"""
    return {
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'admin',
        'created_at': datetime.now()
    }

@pytest.fixture
def sample_orders(db_session):
    """Create sample orders in database"""
    orders = [
        Order(
            user_id=1,
            product_id=1,
            quantity=2,
            amount=100.00,
            status='completed',
            created_at=datetime.now()
        ),
        Order(
            user_id=1,
            product_id=2,
            quantity=1,
            amount=50.00,
            status='pending',
            created_at=datetime.now()
        )
    ]
    for order in orders:
        db_session.add(order)
    db_session.commit()
    return orders
```

**Location:**
- Frontend: `frontend/src/__tests__/fixtures/` or `frontend/tests/fixtures/`
- Backend: `backend/tests/fixtures.py` or `backend/tests/conftest.py`

## Coverage

**Requirements:**
- Frontend: No coverage requirement currently enforced
- Backend: No coverage requirement currently enforced
- Recommended target: 70%+ for critical paths (services, API endpoints)

**View Coverage:**

Frontend (when implemented):
```bash
cd frontend && pnpm test --coverage
# Output: coverage/index.html
```

Backend (when implemented):
```bash
cd backend && python -m pytest --cov=app --cov-report=html
# Output: htmlcov/index.html
```

## Test Types

**Unit Tests:**

Scope: Individual functions and methods in isolation

Frontend unit tests (recommended pattern):
- Test hook logic: `useApiCall()`, `useAsyncApiCall()`
- Test utility functions
- Test component prop handling

Backend unit tests (recommended pattern):
- Test service methods: `SQLService.generate_sql()`, `RAGService.retrieve_documents()`
- Test schema validation: Pydantic models
- Test helper functions

Example backend unit test:
```python
@pytest.mark.asyncio
async def test_sql_service_infer_chart_type():
    """Test chart type inference from query"""
    service = SQLService()
    
    assert service._infer_chart_type('比较订单数') == 'bar'
    assert service._infer_chart_type('订单趋势') == 'line'
    assert service._infer_chart_type('占比分析') == 'pie'
    assert service._infer_chart_type('其他查询') == 'table'
```

**Integration Tests:**

Scope: Multiple components working together

Backend integration tests (recommended pattern):
- Test full API flow: Request → Service → Database → Response
- Test with real database fixtures
- Test middleware and error handling

Example backend integration test:
```python
@pytest.mark.asyncio
def test_query_api_end_to_end(client: TestClient, db: Session):
    """Test complete query flow from API to database"""
    # Setup test data
    db.add(Order(user_id=1, amount=100, created_at=datetime.now()))
    db.commit()
    
    # Test API call
    response = client.post('/api/query', json={
        'natural_language_query': 'recent orders'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['result']) > 0
    assert 'execution_time' in data
```

Frontend integration tests (when implemented):
- Test page components with navigation
- Test data flow through hooks and API calls
- Test user interactions end-to-end

**E2E Tests:**
- Framework: Not yet implemented
- Recommended: Cypress or Playwright for browser automation
- Scope: Full user workflows (login → query → export data)

## Common Patterns

**Async Testing:**

Frontend (Vitest + React Testing Library):
```typescript
it('should handle async query', async () => {
  render(<DataQuery />)
  await userEvent.type(screen.getByRole('textbox'), 'test query')
  await userEvent.click(screen.getByText('查询'))
  
  // Wait for async operation to complete
  await waitFor(() => {
    expect(screen.getByText(/数据统计/)).toBeInTheDocument()
  })
})
```

Backend (pytest-asyncio):
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async service method"""
    service = RAGService()
    results = await service.retrieve_documents('test query', top_k=5)
    
    assert isinstance(results, list)
    assert all('text' in doc for doc in results)
```

**Error Testing:**

Frontend error test pattern:
```typescript
it('should show error message on API failure', async () => {
  const mockError = vi.fn().mockRejectedValueOnce(
    new Error('Network error')
  )
  vi.mock('@services/api', () => ({ queryData: mockError }))
  
  render(<DataQuery />)
  await userEvent.type(screen.getByRole('textbox'), 'query')
  await userEvent.click(screen.getByText('查询'))
  
  await waitFor(() => {
    expect(screen.getByText(/查询失败/)).toBeInTheDocument()
  })
})
```

Backend error test pattern:
```python
@pytest.mark.asyncio
async def test_invalid_sql_rejected():
    """Should reject non-SELECT queries"""
    service = SQLService()
    
    with pytest.raises(ValueError, match='只允许执行 SELECT 查询'):
        await service.execute_query('DELETE FROM orders', mock_db)

@pytest.mark.asyncio
async def test_operation_logs_failures():
    """Should log operation failures"""
    service = OperationService()
    
    result = await service.execute_operation(
        'approve_order',
        {'order_id': 99999},  # Non-existent
        user_id=1
    )
    
    assert result['status'] == 'failed'
    assert 'error' in result
```

**Testing API Responses:**

Backend response validation pattern:
```python
def test_chat_response_structure(client: TestClient):
    """Validate response matches ChatResponse schema"""
    response = client.post('/api/chat', json={
        'question': 'test question'
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate required fields match schema
    assert 'answer' in data
    assert 'sources' in data
    assert 'confidence' in data
    assert 0 <= data['confidence'] <= 1
    
    # Validate source structure
    for source in data['sources']:
        assert 'document_id' in source
        assert 'title' in source
        assert 'relevance' in source
        assert 0 <= source['relevance'] <= 1
```

---

*Testing analysis: 2026-04-16*
