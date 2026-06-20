from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    recipes_generated_today: int
    subscription_tier: str
    subscription_expiry: Optional[datetime] = None
    total_co2_saved: float = 0
    total_money_saved: float = 0

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
