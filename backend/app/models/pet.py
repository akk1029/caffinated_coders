import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
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

    user = relationship("User", back_populates="pet")
