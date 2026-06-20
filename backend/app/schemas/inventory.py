from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class DetectedIngredient(BaseModel):
    item_name: str
    suggested_shelf_days: int
    confidence: float


class UploadResponse(BaseModel):
    detected_ingredients: List[DetectedIngredient]


class BatchConfirm(BaseModel):
    item_name: str
    quantity: float
    unit: str
    expiry_date: datetime
    estimated_cost: Optional[float] = None


class ConfirmInventoryRequest(BaseModel):
    batches: List[BatchConfirm]


class BatchResponse(BaseModel):
    batch_id: uuid.UUID
    item_name: str
    quantity: float
    unit: str
    upload_date: datetime
    expiry_date: datetime
    status: str
    estimated_cost: Optional[float] = None

    model_config = {"from_attributes": True}
