"""
Seed random data for an existing user by email.
Run from the backend/ directory:
    python seed_user.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.models.pet import DigitalPet
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.subscription import SubscriptionLog, PaymentStatus

TARGET_EMAIL = "aungkoko.work@gmail.com"

INGREDIENTS = [
    ("Milk", "L"), ("Eggs", "pcs"), ("Butter", "g"), ("Flour", "g"),
    ("Sugar", "g"), ("Salt", "tsp"), ("Olive Oil", "ml"), ("Garlic", "pcs"),
    ("Onion", "pcs"), ("Tomato", "pcs"), ("Chicken Breast", "g"),
    ("Ground Beef", "g"), ("Salmon", "g"), ("Broccoli", "g"),
    ("Spinach", "g"), ("Carrot", "pcs"), ("Potato", "pcs"),
    ("Rice", "g"), ("Pasta", "g"), ("Cheese", "g"), ("Yogurt", "g"),
    ("Lemon", "pcs"), ("Apple", "pcs"), ("Banana", "pcs"),
    ("Soy Sauce", "ml"), ("Honey", "g"), ("Pepper", "tsp"),
    ("Cumin", "tsp"), ("Paprika", "tsp"), ("Coconut Milk", "ml"),
]

MOOD_STATUSES = ["Happy", "Sad", "Excited", "Tired", "Hungry"]


def random_date(days_offset_min: int, days_offset_max: int) -> datetime:
    offset = random.randint(days_offset_min, days_offset_max)
    return datetime.utcnow() + timedelta(days=offset)


async def seed_for_user():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Look up the user (outside a transaction — read-only)
        result = await session.execute(select(User).where(User.email == TARGET_EMAIL))
        user = result.scalar_one_or_none()

        if user is None:
            print(f"No user found with email: {TARGET_EMAIL}")
            await engine.dispose()
            return

        print(f"Found user: {user.username} ({user.user_id})")

        pet_result = await session.execute(
            select(DigitalPet).where(DigitalPet.user_id == user.user_id)
        )
        existing_pet = pet_result.scalar_one_or_none()

        # Build all objects first, then commit in one transaction
        to_add = []

        if existing_pet is None:
            to_add.append(DigitalPet(
                pet_id=uuid.uuid4(),
                user_id=user.user_id,
                health_points=random.randint(60, 100),
                mood_status=random.choice(MOOD_STATUSES),
                appearance_level=random.randint(1, 5),
            ))
            print("Will create pet")
        else:
            print("Pet already exists — skipping")

        ingredients = random.sample(INGREDIENTS, 10)
        batches = []
        for name, unit in ingredients:
            status = random.choices(
                [BatchStatus.PANTRY, BatchStatus.CONSUMED, BatchStatus.EXPIRED, BatchStatus.DISCARDED],
                weights=[50, 25, 15, 10],
            )[0]
            if status == BatchStatus.PANTRY:
                expiry = random_date(1, 30)
            elif status == BatchStatus.EXPIRED:
                expiry = random_date(-30, -1)
            else:
                expiry = random_date(-60, 30)

            batches.append(IngredientBatch(
                batch_id=uuid.uuid4(),
                user_id=user.user_id,
                item_name=name,
                quantity=round(random.uniform(0.1, 5.0), 2),
                unit=unit,
                upload_date=random_date(-30, 0),
                expiry_date=expiry,
                status=status,
                estimated_cost=round(random.uniform(0.5, 20.0), 2),
            ))
        to_add.extend(batches)

        logs = []
        if user.subscription_tier == SubscriptionTier.PREMIUM:
            for _ in range(random.randint(1, 3)):
                logs.append(SubscriptionLog(
                    transaction_id=uuid.uuid4(),
                    user_id=user.user_id,
                    payment_date=random_date(-180, 0),
                    amount=round(random.choice([4.99, 9.99, 19.99]), 2),
                    status=random.choices(
                        [PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.REFUNDED],
                        weights=[85, 10, 5],
                    )[0],
                ))
            to_add.extend(logs)
        else:
            print("User is FREE tier — skipping subscription logs")

        user.total_co2_saved = round(random.uniform(5, 50), 4)
        user.total_money_saved = round(random.uniform(10, 200), 2)
        user.recipes_generated_today = random.randint(0, 3)

        session.add_all(to_add)
        session.add(user)
        await session.commit()

        print(f"Added {len(batches)} ingredient batches")
        if logs:
            print(f"Added {len(logs)} subscription log entries")
        print(f"Updated stats: co2_saved={user.total_co2_saved}, money_saved={user.total_money_saved}")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed_for_user())
