from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.pet import DigitalPet
from app.dependencies import get_current_user

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/")
async def get_leaderboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, DigitalPet)
        .join(DigitalPet, DigitalPet.user_id == User.user_id, isouter=True)
        .order_by(User.total_co2_saved.desc())
        .limit(50)
    )
    rows = result.all()

    user_rank = None
    rankings = []
    for i, (u, pet) in enumerate(rows, start=1):
        rankings.append({
            "user_id": str(u.user_id),
            "username": u.username,
            "total_co2_saved": float(u.total_co2_saved or 0),
            "total_money_saved": float(u.total_money_saved or 0),
            "pet_level": pet.appearance_level if pet else 1,
            "pet_type": pet.pet_type if pet else "fox",
            "health_points": pet.health_points if pet else 100,
        })
        if u.user_id == user.user_id:
            user_rank = i

    return {"rankings": rankings, "user_rank": user_rank}
