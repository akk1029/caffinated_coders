import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "Free"
    PREMIUM = "Premium"


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    recipes_generated_today = Column(Integer, default=0)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expiry = Column(DateTime, nullable=True)
    total_co2_saved = Column(Numeric(10, 4), default=0)
    total_money_saved = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("IngredientBatch", back_populates="user")
    pet = relationship("DigitalPet", back_populates="user", uselist=False)
    subscriptions = relationship("SubscriptionLog", back_populates="user")
