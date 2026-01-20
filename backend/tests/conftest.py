import pytest
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["ENVIRONMENT"] = "test"

from app.database import Base, get_db
from app.models import User, Service, Snapshot, ChangeEvent, Alert, Subscription, Payment, Tag, SavedView
from app.main import app
from app.scheduler import scheduler, start_scheduler, shutdown_scheduler
from app.core.security import create_access_token

TEST_DB_FILE = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
TEST_DB_FILE.close()
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE.name}"

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session", autouse=True)
def setup_scheduler():
    if not scheduler.running:
        start_scheduler()
    yield
    if scheduler.running:
        shutdown_scheduler()


@pytest.fixture(scope="session", autouse=True)
async def cleanup_test_db():
    yield
    try:
        os.unlink(TEST_DB_FILE.name)
    except:
        pass


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    from app.core.security import get_password_hash
    import uuid
    
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def auth_headers(db_session: AsyncSession) -> dict:
    from app.core.security import get_password_hash
    import uuid
    
    user = User(
        id=uuid.uuid4(),
        email="authtest@example.com",
        password_hash=get_password_hash("testpass123")
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_fetch_page():
    mock_html = """
    <html>
    <head><title>Test Pricing Page</title></head>
    <body>
        <h1>Pricing Plans</h1>
        <div class="plan">
            <h2>Basic Plan</h2>
            <p class="price">$9.99/month</p>
        </div>
        <div class="plan">
            <h2>Premium Plan</h2>
            <p class="price">$19.99/month</p>
        </div>
    </body>
    </html>
    """
    
    async def mock_fetch(*args, **kwargs):
        return mock_html
    
    def noop_decorator(limit_string):
        def decorator(func):
            return func
        return decorator
    
    with patch('app.services.fetcher.fetch_page', new=mock_fetch):
        with patch('app.services.snapshot_service.fetch_page', new=mock_fetch):
            with patch('app.middleware.rate_limit.limiter.limit', noop_decorator):
                yield

