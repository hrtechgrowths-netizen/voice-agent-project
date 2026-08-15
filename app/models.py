from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    """
    User database model representing registrants on the platform.
    Has a structural link to their calculated crypto alpha logs.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Updated: audio_files changed to crypto_logs
    crypto_logs = relationship(
        "CryptoLog",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

class CryptoLog(Base):
    """
    CryptoLog database model tracking AI analytics calculations, 
    trade signals, or cross-chain rebalancing logs.
    """
    __tablename__ = "crypto_logs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)               # E.g., "Signal: BUY BTC"
    engine_used = Column(String, nullable=False)         # E.g., "AI Quant Model v4"
    target_asset = Column(String, nullable=False)        # E.g., "BTC", "ETH"
    structured_data_url = Column(String, nullable=False) # Cloudinary/S3 json report link
    score_metric = Column(Float, nullable=False, default=0.0)  # Volatility or Confidence Score
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="crypto_logs")

