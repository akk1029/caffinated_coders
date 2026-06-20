"""
Seed ~200 pantry items for an existing user by email.
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
from app.models.user import User
from app.models.pet import DigitalPet
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.subscription import SubscriptionLog  # noqa: F401 — needed for SQLAlchemy relationship resolution

TARGET_EMAIL = "test@gmail.com"

# Ingredient names match MealDB naming so recipe generation works well
INGREDIENTS = [
    # Proteins
    ("Chicken", "g"), ("Chicken Breast", "g"), ("Chicken Thighs", "g"),
    ("Ground Beef", "g"), ("Beef", "g"), ("Bacon", "g"), ("Pork", "g"),
    ("Salmon", "g"), ("Tuna", "g"), ("Shrimp", "g"), ("Eggs", "pcs"),
    # Dairy
    ("Milk", "ml"), ("Butter", "g"), ("Cheese", "g"), ("Parmesan", "g"),
    ("Mozzarella", "g"), ("Cheddar", "g"), ("Cream", "ml"), ("Yogurt", "g"),
    # Grains & Starches
    ("Rice", "g"), ("Pasta", "g"), ("Spaghetti", "g"), ("Penne", "g"),
    ("Flour", "g"), ("Bread", "pcs"), ("Oats", "g"), ("Noodles", "g"),
    # Vegetables
    ("Garlic", "pcs"), ("Onion", "pcs"), ("Tomato", "pcs"), ("Potato", "pcs"),
    ("Carrot", "pcs"), ("Broccoli", "g"), ("Spinach", "g"), ("Celery", "pcs"),
    ("Bell Pepper", "pcs"), ("Zucchini", "pcs"), ("Mushrooms", "g"),
    ("Corn", "pcs"), ("Peas", "g"), ("Leek", "pcs"), ("Aubergine", "pcs"),
    ("Sweet Potato", "pcs"), ("Cucumber", "pcs"), ("Lettuce", "g"),
    ("Asparagus", "g"), ("Cabbage", "g"), ("Kale", "g"), ("Courgette", "pcs"),
    ("Spring Onion", "pcs"), ("Red Pepper", "pcs"), ("Green Pepper", "pcs"),
    # Fruits
    ("Lemon", "pcs"), ("Lime", "pcs"), ("Apple", "pcs"), ("Banana", "pcs"),
    ("Tomatoes", "pcs"), ("Cherry Tomatoes", "g"), ("Avocado", "pcs"),
    # Pantry / Condiments
    ("Olive Oil", "ml"), ("Vegetable Oil", "ml"), ("Soy Sauce", "ml"),
    ("Honey", "g"), ("Vinegar", "ml"), ("Tomato Paste", "g"),
    ("Tomato Sauce", "ml"), ("Coconut Milk", "ml"), ("Chicken Stock", "ml"),
    ("Beef Stock", "ml"), ("Vegetable Stock", "ml"), ("White Wine", "ml"),
    ("Red Wine", "ml"), ("Worcestershire Sauce", "ml"), ("Fish Sauce", "ml"),
    # Spices & Herbs
    ("Salt", "tsp"), ("Pepper", "tsp"), ("Paprika", "tsp"), ("Cumin", "tsp"),
    ("Coriander", "tsp"), ("Thyme", "tsp"), ("Rosemary", "tsp"),
    ("Oregano", "tsp"), ("Basil", "tsp"), ("Bay Leaves", "pcs"),
    ("Ginger", "g"), ("Turmeric", "tsp"), ("Chilli Flakes", "tsp"),
    ("Garlic Powder", "tsp"), ("Onion Powder", "tsp"), ("Cinnamon", "tsp"),
    # Legumes & Canned
    ("Chickpeas", "g"), ("Black Beans", "g"), ("Kidney Beans", "g"),
    ("Lentils", "g"), ("Cannellini Beans", "g"),
    # Baking
    ("Sugar", "g"), ("Brown Sugar", "g"), ("Baking Powder", "tsp"),
    ("Vanilla Extract", "ml"), ("Cocoa Powder", "g"), ("Chocolate", "g"),
]

MOOD_STATUSES = ["Happy", "Excited", "Content"]


def random_date(days_min: int, days_max: int) -> datetime:
    return datetime.utcnow() + timedelta(days=random.randint(days_min, days_max))


async def seed_for_user():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == TARGET_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"No user found with email: {TARGET_EMAIL}")
            await engine.dispose()
            return

        print(f"Found user: {user.username} ({user.user_id})")

        pet_result = await session.execute(select(DigitalPet).where(DigitalPet.user_id == user.user_id))
        existing_pet = pet_result.scalar_one_or_none()

        to_add = []

        if existing_pet is None:
            to_add.append(DigitalPet(
                pet_id=uuid.uuid4(),
                user_id=user.user_id,
                health_points=random.randint(60, 100),
                mood_status=random.choice(MOOD_STATUSES),
                appearance_level=random.randint(1, 5),
            ))
            print("Created pet")
        else:
            print("Pet already exists — skipping")

        batches = []

        # ~30 items expiring in 1-3 days (for testing expiry-priority feature)
        expiring_pool = random.sample(INGREDIENTS, min(30, len(INGREDIENTS)))
        for name, unit in expiring_pool:
            batches.append(IngredientBatch(
                batch_id=uuid.uuid4(),
                user_id=user.user_id,
                item_name=name,
                quantity=round(random.uniform(0.5, 3.0), 2),
                unit=unit,
                upload_date=random_date(-10, -1),
                expiry_date=random_date(1, 3),
                status=BatchStatus.PANTRY,
                estimated_cost=round(random.uniform(1.0, 15.0), 2),
            ))

        # ~120 normal pantry items (expiry 4-30 days)
        normal_pool = INGREDIENTS * 3  # repeat so we can pick 120+
        random.shuffle(normal_pool)
        for name, unit in normal_pool[:120]:
            batches.append(IngredientBatch(
                batch_id=uuid.uuid4(),
                user_id=user.user_id,
                item_name=name,
                quantity=round(random.uniform(0.1, 5.0), 2),
                unit=unit,
                upload_date=random_date(-20, -1),
                expiry_date=random_date(4, 30),
                status=BatchStatus.PANTRY,
                estimated_cost=round(random.uniform(0.5, 20.0), 2),
            ))

        # ~50 historical (consumed / expired / discarded)
        hist_pool = random.sample(INGREDIENTS, min(50, len(INGREDIENTS)))
        for name, unit in hist_pool:
            status = random.choices(
                [BatchStatus.CONSUMED, BatchStatus.EXPIRED, BatchStatus.DISCARDED],
                weights=[60, 25, 15],
            )[0]
            batches.append(IngredientBatch(
                batch_id=uuid.uuid4(),
                user_id=user.user_id,
                item_name=name,
                quantity=round(random.uniform(0.1, 5.0), 2),
                unit=unit,
                upload_date=random_date(-60, -10),
                expiry_date=random_date(-30, -1),
                status=status,
                estimated_cost=round(random.uniform(0.5, 20.0), 2),
            ))

        to_add.extend(batches)

        user.total_co2_saved = round(random.uniform(5, 50), 4)
        user.total_money_saved = round(random.uniform(10, 200), 2)
        user.recipes_generated_today = 0

        session.add_all(to_add)
        session.add(user)
        await session.commit()

        pantry_count = sum(1 for b in batches if b.status == BatchStatus.PANTRY)
        expiring_count = sum(1 for b in batches if b.status == BatchStatus.PANTRY and
                             b.expiry_date <= datetime.utcnow() + timedelta(days=3))
        print(f"Added {len(batches)} total batches")
        print(f"  · {pantry_count} in pantry ({expiring_count} expiring in ≤3 days)")
        print(f"  · {len(batches) - pantry_count} historical (consumed/expired/discarded)")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed_for_user())
