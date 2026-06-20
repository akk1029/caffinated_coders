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
    # Google API key (Vision via REST). Needs billing enabled on the GCP project.
    GOOGLE_API_KEY: str = ""
    # OCR.space — FREE receipt OCR, no billing/credit card. "helloworld" is the public
    # demo key (rate-limited); register a free key at https://ocr.space/ocrapi for reliability.
    OCR_SPACE_API_KEY: str = "helloworld"

    # Create database tables on startup (lets you deploy without shell access to run init_db).
    AUTO_INIT_DB: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"

    SPOONACULAR_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
