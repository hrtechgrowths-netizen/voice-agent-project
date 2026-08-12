from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    """
    Pydantic schema for creating a new user (Signup).
    Requires a username (min 3 chars) and a password (min 6 chars).
    """
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    """
    Pydantic schema for outputting user account metadata.
    """
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """
    Pydantic schema representing the Bearer token returned upon login.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Pydantic schema containing token payload information.
    """
    username: Optional[str] = None

class AudioFileResponse(BaseModel):
    """
    Pydantic schema for returning history records of audio generations.
    """
    id: int
    title: str
    model_used: str
    voice_name: Optional[str] = None
    cloudinary_url: str
    duration: float
    created_at: datetime

    class Config:
        from_attributes = True

class TTSRequest(BaseModel):
    """
    Pydantic request body schema for Kokoro TTS voice generation.
    """
    text: str = Field(..., min_length=1)
    voice: str = "af_heart"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(1.0, ge=0.5, le=2.0)
