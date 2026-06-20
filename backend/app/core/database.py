from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase):
    pass

_engine = None
_AsyncSessionLocal = None


def _async_db_url(url: str) -> str:
    """Managed hosts (Render/Heroku) hand out 'postgresql://' or 'postgres://';
    the async engine needs the asyncpg driver. Normalise it so DATABASE_URL
    works without manual editing."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _get_engine():
    global _engine, _AsyncSessionLocal
    if _engine is None:
        _engine = create_async_engine(_async_db_url(settings.DATABASE_URL), echo=settings.DEBUG)
        _AsyncSessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine, _AsyncSessionLocal


async def get_db():
    _, session_factory = _get_engine()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
