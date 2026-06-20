import uuid
import random
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

PET_TYPES = ["fox", "wolf", "tiger", "dragon", "bat"]


def random_pet_type() -> str:
    return random.choice(PET_TYPES)


class DigitalPet(Base):
    __tablename__ = "digital_pet"

    pet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    health_points = Column(Integer, default=65)
    mood_status = Column(String, default="Happy")
    appearance_level = Column(Integer, default=1)
    pet_type = Column(String, nullable=False, default=random_pet_type, server_default="fox")
    is_hatched = Column(Boolean, nullable=False, default=False, server_default="false")

    user = relationship("User", back_populates="pet")
