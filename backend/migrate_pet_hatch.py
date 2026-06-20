"""
Adds pet_type and is_hatched columns to digital_pet table.
Run once from the backend/ directory:
    python migrate_pet_hatch.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def migrate():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE digital_pet ADD COLUMN IF NOT EXISTS pet_type VARCHAR NOT NULL DEFAULT 'fox'"
        ))
        await conn.execute(text(
            "ALTER TABLE digital_pet ADD COLUMN IF NOT EXISTS is_hatched BOOLEAN NOT NULL DEFAULT TRUE"
        ))
        print("Columns added. Existing pets marked as already hatched (is_hatched=TRUE).")
    await engine.dispose()
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
