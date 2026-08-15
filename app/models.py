from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base 

class User(Base):
"""
User database model representing registrants on the platform.
Has a structural link to their generated audio files.
"""
**tablename** = "users" 

id = Column(Integer, primary_key=True, index=True)
username = Column(String, unique=True, index=True, nullable=False)
hashed_password = Column(String, nullable=False)
created_at = Column(DateTime, default=datetime.utcnow)
# Structural relationship linking user to their generated audio files

audio_files = relationship(
"AudioFile",
back_populates="owner",
cascade="all, delete-orphan"
)

class AudioFile(Base):
"""
AudioFile database model tracking AI generated TTS tracks,
cloned voices, or blended audio waveforms.
"""
**tablename** = "audio_files" 

id = Column(Integer, primary_key=True, index=True)
title = Column(String, nullable=False)               # E.g., "TTS: Hello World"
model_used = Column(String, nullable=False)          # E.g., "Kokoro TTS", "Pocket TTS Clone"
voice_name = Column(String, nullable=False)          # E.g., "af_bella", "cloned_voice"
cloudinary_url = Column(String, nullable=False)      # Cloudinary hosted audio secure URL
duration = Column(Float, nullable=False, default=0.0)# Audio length in seconds
user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
created_at = Column(DateTime, default=datetime.utcnow)

owner = relationship("User", back_populates="audio_files")
