from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.pet import DigitalPet
from app.schemas.inventory import UploadResponse, ConfirmInventoryRequest, BatchResponse
from app.services.cv_service import detect_ingredients
from app.dependencies import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])

# 0.25 kg assumed average weight per unit — simplified CO2 calc
_KG_PER_UNIT = 0.25
_CO2_PER_KG = 2.5


@router.post("/upload/", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    contents = await file.read()
    detected = await detect_ingredients(contents)
    return {"detected_ingredients": detected}


@router.post("/confirm/", response_model=List[BatchResponse], status_code=201)
async def confirm_inventory(
    request: ConfirmInventoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    batches = []
    for item in request.batches:
        batch = IngredientBatch(
            user_id=user.user_id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit=item.unit,
            expiry_date=item.expiry_date,
            estimated_cost=item.estimated_cost,
        )
        db.add(batch)
        batches.append(batch)
    await db.commit()
    for b in batches:
        await db.refresh(b)
    return batches


@router.get("/", response_model=List[BatchResponse])
async def get_inventory(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.user_id == user.user_id)
        .where(IngredientBatch.status == BatchStatus.PANTRY)
        .order_by(IngredientBatch.expiry_date.asc())
    )
    return result.scalars().all()


@router.post("/{batch_id}/consume")
async def consume_batch(
    batch_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark as consumed: updates pet HP, CO2 saved, and money saved."""
    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.batch_id == batch_id)
        .where(IngredientBatch.user_id == user.user_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch.status = BatchStatus.CONSUMED

    weight_kg = float(batch.quantity) * _KG_PER_UNIT
    co2 = weight_kg * _CO2_PER_KG
    user.total_co2_saved = float(user.total_co2_saved or 0) + co2
    if batch.estimated_cost:
        user.total_money_saved = float(user.total_money_saved or 0) + float(batch.estimated_cost)

    pet_result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = pet_result.scalar_one_or_none()
    if pet:
        pet.health_points = min(100, pet.health_points + 5)
        if pet.health_points >= 100 and pet.appearance_level < 10:
            pet.appearance_level += 1
        pet.mood_status = "Ecstatic" if pet.health_points == 100 else "Happy" if pet.health_points >= 70 else "Content"

    await db.commit()
    return {"co2_saved": round(co2, 4), "message": "Ingredient marked as consumed"}


@router.delete("/{batch_id}")
async def discard_batch(
    batch_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngredientBatch)
        .where(IngredientBatch.batch_id == batch_id)
        .where(IngredientBatch.user_id == user.user_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch.status = BatchStatus.DISCARDED

    pet_result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = pet_result.scalar_one_or_none()
    if pet:
        pet.health_points = max(0, pet.health_points - 5)
        pet.mood_status = "Sad" if pet.health_points < 50 else "Content"

    await db.commit()
    return {"message": "Batch discarded"}
