from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.inventory import IngredientBatch, BatchStatus
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.user_id == user.user_id)
        .where(IngredientBatch.status == BatchStatus.PANTRY)
    )
    items = result.scalars().all()

    now = datetime.utcnow()
    threshold = now + timedelta(days=3)
    expiring = [i for i in items if i.expiry_date <= threshold]

    return {
        "pantry_count": len(items),
        "expiring_soon_count": len(expiring),
        "expiring_items": [i.item_name for i in expiring],
    }
