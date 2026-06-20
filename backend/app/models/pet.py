import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DigitalPet(Base):
    __tablename__ = "digital_pet"

    pet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    health_points = Column(Integer, default=100)
    mood_status = Column(String, default="Happy")
    appearance_level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    evolution_stage = Column(String, default="Egg")  # Egg, Baby, Teen, Adult

    user = relationship("User", back_populates="pet")
    activities = relationship("PetActivityLog", back_populates="pet")


class PetActivityLog(Base):
    __tablename__ = "pet_activity_log"

    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("digital_pet.pet_id"), nullable=False)
    activity_type = Column(String, nullable=False)
    points_change = Column(Integer, nullable=False)
    activity_date = Column(DateTime, default=datetime.utcnow)

    pet = relationship("DigitalPet", back_populates="activities")
