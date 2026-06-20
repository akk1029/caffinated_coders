import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BatchStatus(str, enum.Enum):
    PANTRY = "Pantry"
    CONSUMED = "Consumed"
    EXPIRED = "Expired"
    DISCARDED = "Discarded"


class IngredientBatch(Base):
    __tablename__ = "ingredients_inventory"

    batch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(Enum(BatchStatus), default=BatchStatus.PANTRY)
    estimated_cost = Column(Numeric(10, 2), nullable=True)

    user = relationship("User", back_populates="inventory")
