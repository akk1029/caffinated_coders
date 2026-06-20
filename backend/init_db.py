"""Run once to create all database tables."""
import asyncio
from app.core.database import Base, _get_engine

# Import every model so SQLAlchemy registers it before create_all
from app.models import user, inventory, pet, subscription, shelf_life  # noqa: F401


async def main():
    engine, _ = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")


asyncio.run(main())
