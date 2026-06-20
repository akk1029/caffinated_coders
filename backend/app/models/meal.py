import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Meal(Base):
    __tablename__ = "meals"

    meal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    meal_name = Column(String, nullable=False)
    estimated_calories = Column(Numeric(10, 2), nullable=True)
    meal_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="meals")
    images = relationship("MealImage", back_populates="meal")


class MealImage(Base):
    __tablename__ = "meal_images"

    image_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meals.meal_id"), nullable=False)
    image_url = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    ai_processed = Column(Boolean, default=False)

    meal = relationship("Meal", back_populates="images")
