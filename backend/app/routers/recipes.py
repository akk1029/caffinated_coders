from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.pet import DigitalPet
from app.services.recipe_service import (
    generate_recipes, save_recipe, list_saved_recipes, unsave_recipe,
)
from app.services.food_data import estimate_co2, estimate_cost
from app.dependencies import get_current_user


class CookedRequest(BaseModel):
    ingredients: List[str]


class SaveRecipeRequest(BaseModel):
    id: str
    title: str
    image: str = ""
    youtube: str = ""
    instructions: str = ""
    category: str = ""
    area: str = ""

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

    expiry_cutoff = datetime.utcnow() + timedelta(days=3)
    exp_result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.user_id == user.user_id)
        .where(IngredientBatch.status == BatchStatus.PANTRY)
        .where(IngredientBatch.expiry_date <= expiry_cutoff)
    )
    expiring_names = list({i.item_name for i in exp_result.scalars().all()})

    recipes = await generate_recipes(ingredient_names, expiring=expiring_names)

    user.recipes_generated_today += 1
    await db.commit()

    return {"recipes": recipes, "expiring_ingredients": expiring_names}


@router.post("/cooked/")
async def mark_cooked(
    body: CookedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recipe_ings = {i.lower() for i in body.ingredients}

    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.user_id == user.user_id)
        .where(IngredientBatch.status == BatchStatus.PANTRY)
    )
    pantry = result.scalars().all()

    consumed, total_co2, total_money = 0, 0.0, 0.0
    for batch in pantry:
        name = batch.item_name.lower()
        if any(name in ing or ing in name for ing in recipe_ings):
            batch.status = BatchStatus.CONSUMED
            co2 = estimate_co2(batch.item_name, batch.quantity, batch.unit)
            money = float(batch.estimated_cost) if batch.estimated_cost else estimate_cost(batch.item_name, batch.quantity, batch.unit)
            total_co2 += co2
            total_money += money
            user.total_co2_saved = float(user.total_co2_saved or 0) + co2
            user.total_money_saved = float(user.total_money_saved or 0) + money
            consumed += 1

    pet_result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = pet_result.scalar_one_or_none()
    if pet and consumed > 0:
        pet.health_points = min(100, pet.health_points + consumed * 5)
        if pet.health_points >= 100 and pet.appearance_level < 10:
            pet.appearance_level += 1
        pet.mood_status = "Ecstatic" if pet.health_points == 100 else "Happy" if pet.health_points >= 70 else "Content"

    await db.commit()
    return {"consumed": consumed, "co2_saved": round(total_co2, 4), "money_saved": round(total_money, 2)}


@router.post("/save/")
async def save(body: SaveRecipeRequest, user: User = Depends(get_current_user)):
    ok = await save_recipe(str(user.user_id), body.dict())
    if not ok:
        raise HTTPException(status_code=503, detail="Could not save recipe (cache offline)")
    return {"saved": True}


@router.get("/saved/")
async def saved(user: User = Depends(get_current_user)):
    return {"recipes": await list_saved_recipes(str(user.user_id))}


@router.delete("/saved/{recipe_id}")
async def unsave(recipe_id: str, user: User = Depends(get_current_user)):
    await unsave_recipe(str(user.user_id), recipe_id)
    return {"saved": False}