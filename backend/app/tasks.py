"""
Celery background tasks.
Uses synchronous SQLAlchemy (psycopg2) because Celery workers are not async.
"""
from celery_app import celery
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Sync DB URL (strip asyncpg driver)
_SYNC_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_URL, pool_pre_ping=True)
_Session = sessionmaker(_engine)


def _db() -> Session:
    return _Session()


@celery.task(name="app.tasks.decay_pet_health")
def decay_pet_health():
    """
    Mark expired pantry items, penalise pet HP (-10 per expired item),
    and update mood accordingly.
    """
    from app.models.inventory import IngredientBatch, BatchStatus
    from app.models.pet import DigitalPet

    db = _db()
    try:
        now = datetime.utcnow()
        expired = (
            db.query(IngredientBatch)
            .filter(IngredientBatch.status == BatchStatus.PANTRY, IngredientBatch.expiry_date < now)
            .all()
        )

        penalties: dict = {}
        for item in expired:
            item.status = BatchStatus.EXPIRED
            penalties[item.user_id] = penalties.get(item.user_id, 0) + 10

        for uid, penalty in penalties.items():
            pet = db.query(DigitalPet).filter_by(user_id=uid).first()
            if pet:
                pet.health_points = max(0, pet.health_points - penalty)
                pet.mood_status = (
                    "Dying" if pet.health_points == 0
                    else "Sick" if pet.health_points < 20
                    else "Sad" if pet.health_points < 50
                    else "Content"
                )

        db.commit()
        return f"Expired {len(expired)} batches across {len(penalties)} users"
    finally:
        db.close()


@celery.task(name="app.tasks.reset_daily_counts")
def reset_daily_counts():
    """Reset recipes_generated_today for all users at midnight."""
    from app.models.user import User

    db = _db()
    try:
        db.query(User).update({User.recipes_generated_today: 0})
        db.commit()
    finally:
        db.close()


@celery.task(name="app.tasks.expire_lapsed_subscriptions")
def expire_lapsed_subscriptions():
    """Downgrade Premium users whose subscription_expiry has passed."""
    from app.models.user import User, SubscriptionTier

    db = _db()
    try:
        expired = (
            db.query(User)
            .filter(
                User.subscription_tier == SubscriptionTier.PREMIUM,
                User.subscription_expiry < datetime.utcnow(),
            )
            .all()
        )
        for u in expired:
            u.subscription_tier = SubscriptionTier.FREE
            u.subscription_expiry = None
        db.commit()
        return f"Expired {len(expired)} subscriptions"
    finally:
        db.close()
