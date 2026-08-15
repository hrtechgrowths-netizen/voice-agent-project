import os
import cloudinary
import cloudinary.uploader
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./voice_agent.db"
    JWT_SECRET: str = "super_secret_jwt_token_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    CLOUDINARY_CLOUD_NAME: str = "du8baffic"
    CLOUDINARY_API_KEY: str = "672158762269852"
    CLOUDINARY_API_SECRET: str = "oIyOIZJpWbVPjooVFfCoK420sLQ"

    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)
