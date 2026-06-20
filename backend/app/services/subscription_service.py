from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, SubscriptionTier


async def expire_lapsed_subscriptions(db: AsyncSession) -> int:
    """Downgrade users whose Premium subscription has passed its expiry date."""
    result = await db.execute(
        select(User)
        .where(User.subscription_tier == SubscriptionTier.PREMIUM)
        .where(User.subscription_expiry < datetime.utcnow())
    )
    expired = result.scalars().all()
    for user in expired:
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_expiry = None
    await db.commit()
    return len(expired)


async def reset_daily_recipe_counts(db: AsyncSession) -> None:
    """Reset recipe generation counters for all users (call via daily cron)."""
    result = await db.execute(select(User))
    for user in result.scalars().all():
        user.recipes_generated_today = 0
    await db.commit()
