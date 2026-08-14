from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from utils.password_utils import check_password, hash_password

AUTH_BYPASS_FOR_DEVELOPMENT = True
DEVELOPMENT_USERNAME = "dev_user"

# Use a custom oauth2 scheme that reads from Bearer header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    """
    hashed_password_bytes = hashed_password.encode("utf-8")
    plain_password_bytes = plain_password.encode("utf-8")

    try:
        if bcrypt.checkpw(plain_password_bytes, hashed_password_bytes):
            return True
    except ValueError:
        pass

    return check_password(plain_password, hashed_password_bytes)

def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash from plain text password.
    """
    return hash_password(password).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JSON Web Token containing payload claims and expiration metadata.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_or_create_development_user(db: Session) -> User:
    """
    Returns a shared development user account for local bypass mode.
    """
    dev_user = db.query(User).filter(User.username == DEVELOPMENT_USERNAME).first()
    if dev_user is None:
        dev_user = User(
            username=DEVELOPMENT_USERNAME,
            hashed_password=get_password_hash("dev-only-password")
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)
    return dev_user

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency that decodes the Bearer token, fetches the user, and returns it.
    If token is invalid or missing, raises 401 Unauthorized.
    In development bypass mode, always returns a shared development user.
    """
    if AUTH_BYPASS_FOR_DEVELOPMENT:
        return get_or_create_development_user(db)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
