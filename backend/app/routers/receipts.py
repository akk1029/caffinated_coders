from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.inventory import IngredientBatch
from app.services.receipt_service import scan_receipt, get_scan_count, incr_scan_count
from app.dependencies import get_current_user

router = APIRouter(prefix="/receipts", tags=["receipts"])

FREE_DAILY_LIMIT = 2
PREMIUM_DAILY_LIMIT = 10


@router.post("/scan/")
async def scan(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_premium = user.subscription_tier == SubscriptionTier.PREMIUM
    limit = PREMIUM_DAILY_LIMIT if is_premium else FREE_DAILY_LIMIT

    used = await get_scan_count(str(user.user_id))
    if used >= limit:
        upsell = "" if is_premium else " Upgrade to Premium for 10 scans/day."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Daily receipt scan limit reached ({used}/{limit}).{upsell}",
        )

    contents = await file.read()
    result = await scan_receipt(contents)

    # OCR unavailable/failed — surface the real reason, don't add sample data to the pantry
    if result.get("demo"):
        return {"added": [], "count": 0, "demo": True, "error": result.get("error"),
                "scans_used": used, "scans_limit": limit}

    # Auto-add parsed items to the pantry (expiry from shelf life, cost from receipt)
    added = []
    for it in result["items"]:
        expiry = datetime.utcnow() + timedelta(days=int(it["suggested_shelf_days"]))
        db.add(IngredientBatch(
            user_id=user.user_id,
            item_name=it["item_name"],
            quantity=it["quantity"],
            unit=it["unit"],
            expiry_date=expiry,
            estimated_cost=it["estimated_cost"],
        ))
        added.append(it)
    if added:
        await db.commit()

    # Only spend a scan when something was actually added
    scans_used = await incr_scan_count(str(user.user_id)) if added else used

    return {
        "added": added,
        "count": len(added),
        "demo": False,
        "error": None,
        "scans_used": scans_used,
        "scans_limit": limit,
    }
