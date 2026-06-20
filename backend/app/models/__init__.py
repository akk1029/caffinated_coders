# Import every model here so SQLAlchemy's class registry is always complete.
# Relationship() strings like "Meal" only resolve if the class has been imported,
# and importing any submodule (e.g. app.models.user) runs this __init__ first.
from app.models.user import User, SubscriptionTier
from app.models.inventory import IngredientBatch, BatchStatus
from app.models.pet import DigitalPet, PetActivityLog
from app.models.subscription import SubscriptionLog, PaymentStatus
from app.models.shelf_life import ShelfLifeReference
from app.models.meal import Meal, MealImage
from app.models.recipe import Recipe, RecipeIngredient

__all__ = [
    "User", "SubscriptionTier",
    "IngredientBatch", "BatchStatus",
    "DigitalPet", "PetActivityLog",
    "SubscriptionLog", "PaymentStatus",
    "ShelfLifeReference",
    "Meal", "MealImage",
    "Recipe", "RecipeIngredient",
]
