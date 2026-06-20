from pydantic import BaseModel
from datetime import datetime
import uuid


class SubscribeRequest(BaseModel):
    payment_method_id: str


class SubscriptionLogResponse(BaseModel):
    transaction_id: uuid.UUID
    payment_date: datetime
    amount: float
    status: str

    model_config = {"from_attributes": True}
