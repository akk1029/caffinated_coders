from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.inventory import IngredientBatch, BatchStatus
from app.services.recipe_service import generate_recipes
from app.dependencies import get_current_user

router = APIRouter(prefix="/recipes", tags=["recipes"])

FREE_TIER_DAILY_LIMIT = 3


@router.post("/generate/")
async def generate(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.subscription_tier == SubscriptionTier.FREE:
        if user.recipes_generated_today >= FREE_TIER_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Daily recipe limit reached. Upgrade to Premium for unlimited recipes.",
            )

    # Fetch pantry items ordered by expiry (FIFO — use what expires soonest)
    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.user_id == user.user_id)
        .where(IngredientBatch.status == BatchStatus.PANTRY)
        .order_by(IngredientBatch.expiry_date.asc())
    )
    ingredients = result.scalars().all()
    if not ingredients:
        raise HTTPException(status_code=400, detail="No ingredients in pantry")

    ingredient_names = list({i.item_name for i in ingredients})
    recipes = await generate_recipes(ingredient_names)

    user.recipes_generated_today += 1
    await db.commit()

    return {"recipes": recipes}
