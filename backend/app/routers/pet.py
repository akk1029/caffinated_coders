from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.pet import DigitalPet
from app.schemas.pet import PetResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/pet", tags=["pet"])


@router.get("/", response_model=PetResponse)
async def get_pet(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@router.post("/hatch/", response_model=PetResponse)
async def hatch_pet(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    pet.is_hatched = True
    await db.commit()
    await db.refresh(pet)
    return pet


@router.post("/feed/", response_model=PetResponse)
async def feed_pet(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet.health_points = min(100, pet.health_points + 10)
    pet.mood_status = "Thriving" if pet.health_points >= 75 else "Happy" if pet.health_points >= 50 else "Struggling" if pet.health_points >= 25 else "Forgotten"

    await db.commit()
    await db.refresh(pet)
    return pet


@router.post("/poke/", response_model=PetResponse)
async def poke_pet(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet.health_points = max(0, pet.health_points - 10)
    pet.mood_status = "Thriving" if pet.health_points >= 75 else "Happy" if pet.health_points >= 50 else "Struggling" if pet.health_points >= 25 else "Forgotten"

    await db.commit()
    await db.refresh(pet)
    return pet
