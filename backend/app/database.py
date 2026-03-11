from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from fastapi import HTTPException
from app.config import settings

if settings.maintenance_mode:
    engine = None
    AsyncSessionLocal = None
else:
    engine = create_async_engine(
        settings.async_database_url,
        echo=True,
        future=True
    )
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable for maintenance"
        )
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

