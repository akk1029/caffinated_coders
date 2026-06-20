"""
Seed script: inserts ~100 test users with pets, inventory batches, and subscription logs.
Run from the backend/ directory:
    python seed.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, SubscriptionTier
from app.models.pet import DigitalPet
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.subscription import SubscriptionLog, PaymentStatus

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry",
    "Iris", "Jack", "Karen", "Liam", "Mia", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zoe",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson",
    "White", "Harris", "Martin", "Thompson", "Young", "Lee",
]

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


def make_user(index: int) -> User:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    username = f"{first.lower()}_{last.lower()}_{index}"
    email = f"{username}@example.com"
    tier = random.choices(
        [SubscriptionTier.FREE, SubscriptionTier.PREMIUM], weights=[70, 30]
    )[0]
    expiry = random_date(30, 365) if tier == SubscriptionTier.PREMIUM else None
    return User(
        user_id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=get_password_hash("Password123!"),
        recipes_generated_today=random.randint(0, 5),
        subscription_tier=tier,
        subscription_expiry=expiry,
        total_co2_saved=round(random.uniform(0, 50), 4),
        total_money_saved=round(random.uniform(0, 200), 2),
        created_at=random_date(-365, 0),
    )


def make_pet(user_id: uuid.UUID) -> DigitalPet:
    return DigitalPet(
        pet_id=uuid.uuid4(),
        user_id=user_id,
        health_points=random.randint(20, 100),
        mood_status=random.choice(MOOD_STATUSES),
        appearance_level=random.randint(1, 5),
    )


def make_batches(user_id: uuid.UUID) -> list[IngredientBatch]:
    batches = []
    count = random.randint(3, 10)
    ingredients = random.sample(INGREDIENTS, min(count, len(INGREDIENTS)))
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
            user_id=user_id,
            item_name=name,
            quantity=round(random.uniform(0.1, 5.0), 2),
            unit=unit,
            upload_date=random_date(-90, 0),
            expiry_date=expiry,
            status=status,
            estimated_cost=round(random.uniform(0.5, 20.0), 2),
        ))
    return batches


def make_subscription_logs(user: User) -> list[SubscriptionLog]:
    if user.subscription_tier != SubscriptionTier.PREMIUM:
        return []
    logs = []
    for _ in range(random.randint(1, 3)):
        logs.append(SubscriptionLog(
            transaction_id=uuid.uuid4(),
            user_id=user.user_id,
            payment_date=random_date(-365, 0),
            amount=round(random.choice([4.99, 9.99, 19.99]), 2),
            status=random.choices(
                [PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.REFUNDED],
                weights=[85, 10, 5],
            )[0],
        ))
    return logs


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            users = [make_user(i) for i in range(1, 101)]
            session.add_all(users)

        async with session.begin():
            pets = [make_pet(u.user_id) for u in users]
            session.add_all(pets)

        async with session.begin():
            batches = [b for u in users for b in make_batches(u.user_id)]
            session.add_all(batches)

        async with session.begin():
            logs = [log for u in users for log in make_subscription_logs(u)]
            if logs:
                session.add_all(logs)

    await engine.dispose()

    print(f"Seeded {len(users)} users")
    print(f"  {sum(1 for u in users if u.subscription_tier == SubscriptionTier.PREMIUM)} premium users")
    print(f"  {len(batches)} ingredient batches")
    print(f"  {len(logs)} subscription log entries")


if __name__ == "__main__":
    asyncio.run(seed())
