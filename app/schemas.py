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

# ==========================================
# UPDATED: NEW CRYPTO DATA VALIDATION SCHEMAS
# ==========================================

class CryptoAnalysisResponse(BaseModel):
    """
    Pydantic schema for returning history records of crypto engine calculations.
    Replaces AudioFileResponse.
    """
    id: int
    title: str
    engine_used: str
    target_asset: str
    structured_data_url: str
    score_metric: float
    created_at: datetime

    class Config:
        from_attributes = True

class MarketRequest(BaseModel):
    """
    Validation schema for Market Analysis requests.
    Replaces TTSRequest.
    """
    token_symbol: str = Field(..., min_length=2, max_length=10) 
    timeframe: str = "4h"                                       
    indicators: List[str] = ["RSI", "MACD", "EMA"]

class SignalRequest(BaseModel):
    """
    Validation schema for Alpha Trade Signal triggers.
    """
    token_symbol: str = Field(..., min_length=2, max_length=10)
    risk_tolerance: str = "medium"                              # E.g., "low", "medium", "high"

class RebalanceRequest(BaseModel):
    """
    Validation schema for DeFi Portfolio structural balancing.
    """
    asset_one: str = Field(..., min_length=2, max_length=10)    # E.g., "BTC"
    asset_two: str = Field(..., min_length=2, max_length=10)    # E.g., "ETH"
    blend_ratio: float = Field(0.5, ge=0.0, le=1.0)             # Target weight structure
