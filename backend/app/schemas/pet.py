from pydantic import BaseModel
import uuid


class PetResponse(BaseModel):
    pet_id: uuid.UUID
    health_points: int
    mood_status: str
    appearance_level: int

    model_config = {"from_attributes": True}
