from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "PantryPet"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://pantrypet:pantrypet123@localhost/pantrypet"

    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google Cloud Vision — leave empty to use Application Default Credentials
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    SPOONACULAR_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
