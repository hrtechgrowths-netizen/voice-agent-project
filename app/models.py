from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    """
    User database model representing registrants on the platform.
    Has a relationship with generated AudioFiles.
    """
    __tablename__ = "users"

    id = Column(Integer, primary key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    audio_files = relationship("AudioFile", back_populates="owner", cascade="all, delete-orphan")

class AudioFile(Base):
    """
    AudioFile database model tracking synthesized or blended audio outputs,
    associated with their creator user and referencing their Cloudinary URLs.
    """
    __tablename__ = "audio_files"

    id = Column(Integer, primary key=True, index=True)
    title = Column(String, nullable=False)
    model_used = Column(String, nullable=False)  # "Kokoro TTS", "Pocket TTS Clone", "Speech Blend"
    voice_name = Column(String, nullable=True)
    cloudinary_url = Column(String, nullable=False)
    duration = Column(Float, nullable=False, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="audio_files")

