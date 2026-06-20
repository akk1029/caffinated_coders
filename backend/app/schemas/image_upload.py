from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ImageUploadResponse(BaseModel):
    upload_id: uuid.UUID
    filename: str
    content_type: Optional[str] = None
    file_size: int
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
