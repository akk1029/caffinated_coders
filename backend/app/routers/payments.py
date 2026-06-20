from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import stripe
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.models.subscription import SubscriptionLog, PaymentStatus
from app.schemas.subscription import SubscribeRequest
from app.dependencies import get_current_user

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/demo-subscribe/")
async def demo_subscribe(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.subscription_tier = SubscriptionTier.PREMIUM
    user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
    db.add(SubscriptionLog(user_id=user.user_id, amount=9.99, status=PaymentStatus.SUCCESS))
    await db.commit()
    return {"message": "Demo subscription activated", "expires": user.subscription_expiry}


@router.post("/subscribe/")
async def subscribe(
    request: SubscribeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stripe.PaymentIntent.create(
            amount=999,  # $9.99 in cents
            currency="usd",
            payment_method=request.payment_method_id,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )

        db.add(SubscriptionLog(user_id=user.user_id, amount=9.99, status=PaymentStatus.SUCCESS))
        user.subscription_tier = SubscriptionTier.PREMIUM
        user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        await db.commit()
        return {"message": "Subscription activated", "expires": user.subscription_expiry}

    except stripe.error.CardError as e:
        db.add(SubscriptionLog(user_id=user.user_id, amount=9.99, status=PaymentStatus.FAILED))
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e.user_message))


@router.post("/webhook/")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        stripe.Webhook.construct_event(payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    return {"status": "received"}
