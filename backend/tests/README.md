# Testing Guide

## Test Structure

```
backend/tests/
├── unit/              # Unit tests for individual functions/classes
├── integration/       # Integration tests for API endpoints
├── performance/       # Performance benchmarks
├── security/          # Security tests
├── factories.py      # Test data factories
└── conftest.py        # Pytest fixtures and configuration
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance tests only
pytest -m performance

# Security tests only
pytest -m security
```

### Run specific test file
```bash
pytest tests/unit/test_security.py
```

### Run specific test
```bash
pytest tests/integration/test_auth_api.py::test_user_registration
```

### Run with verbose output
```bash
pytest -v
```

### Run with output capture disabled
```bash
pytest -s
```

## Coverage Goals

- **Overall**: >80% coverage
- **Critical paths**: >90% coverage
- **API endpoints**: 100% coverage
- **Services**: >85% coverage

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow running tests

## Test Fixtures

Common fixtures available in `conftest.py`:

- `db_session` - Database session for tests
- `client` - HTTP client for API tests
- `test_user` - Test user fixture
- `auth_headers` - Authentication headers

## Test Factories

Use factories from `tests/factories.py` to create test data:

```python
from tests.factories import create_test_user, create_test_service

user = await create_test_user(db_session, email="test@example.com")
service = await create_test_service(db_session, user.id, name="Test Service")
```

## Performance Benchmarks

Performance tests verify:

- API endpoints: <200ms (p95)
- Database queries: <50ms (p95)
- Background jobs: <5s per service
- Snapshot processing: <2s per service

## Security Tests

Security tests cover:

- Authentication bypass attempts
- Authorization checks
- Input validation (SQL injection, XSS)
- Rate limiting

## Writing New Tests

### Unit Test Example
```python
import pytest
from app.services.subscription_service import get_service_limit

@pytest.mark.unit
def test_get_service_limit_free_tier():
    limit = get_service_limit(PlanType.free)
    assert limit == 3
```

### Integration Test Example
```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/services",
        json={"name": "Test", "url": "https://example.com"},
        headers=auth_headers
    )
    assert response.status_code == 201
```

## CI/CD

Tests run automatically on:
- Every push to main/develop branches
- Every pull request

Coverage must be >80% for tests to pass.

## Mocking External Services

External services are mocked in tests:

- **Stripe**: Mocked using `unittest.mock.patch`
- **Mailgun**: Mocked using `unittest.mock.patch`
- **HTTP requests**: Use test fixtures or mocks

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test
- Torn down after each test
- Isolated from other tests

## Troubleshooting

### Tests failing with database errors
- Ensure test database is properly set up
- Check that migrations are applied

### Tests failing with import errors
- Ensure you're running from the `backend` directory
- Check that all dependencies are installed

### Coverage not meeting threshold
- Run coverage report: `pytest --cov=app --cov-report=html`
- Open `htmlcov/index.html` to see uncovered lines
- Add tests for uncovered code

