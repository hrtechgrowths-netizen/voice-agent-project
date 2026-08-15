from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import engine, Base, get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token, AudioFileResponse, TTSRequest
from app.auth import get_password_hash, verify_password, create_access_token, get_or_create_development_user

from app.services.cloudinary_service import upload_audio
from app.services.tts_service import generate_speech
from app.services.voice_cloning_service import clone_voice
from app.services.voice_mixing_service import blend_audio_waveforms

# Dynamic Import Wrapper taake container kisi bhi haal mein crash na ho
try:
    from app.models import AudioFile
    TargetModel = AudioFile
    is_crypto = False
except ImportError:
    try:
        from app.models import CryptoLog
        TargetModel = CryptoLog
        is_crypto = True
    except ImportError:
        raise ImportError("Neither AudioFile nor CryptoLog model found in app.models")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Voice Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.post("/api/auth/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")  
    hashed_password = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=Token)
def login(user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")   
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/tts/generate")
def generate_tts(request: TTSRequest, db: Session = Depends(get_db)):
    try:
        audio_bytes, duration = generate_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch
        )      
        title = f"TTS: {request.text[:30]}"
        url = upload_audio(audio_bytes, filename="tts.wav")      
        dev_user = get_or_create_development_user(db)
        
        if not is_crypto:
            db_audio = TargetModel(
                title=title,
                model_used="Kokoro TTS",
                voice_name=request.voice,
                cloudinary_url=url,
                duration=duration,
                user_id=dev_user.id
            )
        else:
            db_audio = TargetModel(
                title=title,
                engine_used="Kokoro TTS",
                target_asset=request.voice,
                structured_data_url=url,
                score_metric=duration,
                user_id=dev_user.id
            )
            
        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)
        return db_audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    dev_user = get_or_create_development_user(db)
    return db.query(TargetModel).filter(TargetModel.user_id == dev_user.id).order_by(TargetModel.created_at.desc()).all()
