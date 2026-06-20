import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Numeric, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class SubscriptionLog(Base):
    __tablename__ = "subscriptions_log"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)

    user = relationship("User", back_populates="subscriptions")
