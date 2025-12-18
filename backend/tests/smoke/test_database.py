import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.user import User
from app.database import AsyncSessionLocal


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_database_connectivity(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_database_user_query(db_session: AsyncSession):
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    assert isinstance(users, list)


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_database_transaction(db_session: AsyncSession):
    from app.core.security import get_password_hash
    import uuid
    
    test_user = User(
        id=uuid.uuid4(),
        email=f"smoketest-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("testpass123")
    )
    
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    
    assert test_user.id is not None
    assert test_user.email is not None
    
    await db_session.delete(test_user)
    await db_session.commit()

