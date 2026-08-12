from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import engine, Base, get_db
from app.models import User, AudioFile
from app.schemas import UserCreate, UserResponse, Token, AudioFileResponse, TTSRequest
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.services.cloudinary_service import upload_audio
from app.services.tts_service import generate_speech
from app.services.voice_cloning_service import clone_voice
from app.services.voice_mixing_service import blend_audio_waveforms

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Voice Platform API")

# Add CORS Middleware to enable interaction from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://voicetest112233.vercel.app"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder to serve fallback local audio files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.post("/api/auth/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Checks if username exists; if not, hashes password and saves.
    """
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
    """
    Authenticate a user.
    Validates password and returns a JWT token.
    """
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/tts/generate", response_model=AudioFileResponse)
def generate_tts(
    request: TTSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate speech from a text prompt using Kokoro TTS (with fallback).
    Uploads output to Cloudinary/local storage and saves metadata.
    """
    try:
        audio_bytes, duration = generate_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch
        )
        
        title = f"TTS: {request.text[:30]}"
        url = upload_audio(audio_bytes, filename="tts.wav")
        
        db_audio = AudioFile(
            title=title,
            model_used="Kokoro TTS",
            voice_name=request.voice,
            cloudinary_url=url,
            duration=duration,
            user_id=current_user.id
        )
        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)
        return db_audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

@app.post("/api/voice-cloning/clone", response_model=AudioFileResponse)
async def clone_voice_endpoint(
    text: str = Form(...),
    voice_name: str = Form("cloned_voice"),
    reference_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clone a voice from reference WAV/MP3 files and synthesizes the input text.
    Uploads output to Cloudinary/local storage and saves metadata.
    """
    try:
        ref_bytes = await reference_file.read()
        
        audio_bytes, duration = clone_voice(
            text=text,
            reference_audio_bytes=ref_bytes,
            voice_name=voice_name
        )
        
        title = f"Cloned: {text[:30]}"
        url = upload_audio(audio_bytes, filename="cloned.wav")
        
        db_audio = AudioFile(
            title=title,
            model_used="Pocket TTS Clone",
            voice_name=voice_name,
            cloudinary_url=url,
            duration=duration,
            user_id=current_user.id
        )
        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)
        return db_audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

@app.post("/api/voice-mixing/blend", response_model=AudioFileResponse)
async def mix_voices_endpoint(
    text: Optional[str] = Form(None),
    voice1: Optional[str] = Form(None),
    voice2: Optional[str] = Form(None),
    blend_ratio: float = Form(0.5),
    audio1: Optional[UploadFile] = File(None),
    audio2: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Blends two voices/audio sources together.
    Accepts EITHER:
    1. Uploaded audio1 and audio2 files.
    2. Prompt text + voice1 + voice2 (generates both first, then blends).
    """
    try:
        if audio1 and audio2:
            audio1_bytes = await audio1.read()
            audio2_bytes = await audio2.read()
            title = f"Mix: {audio1.filename} & {audio2.filename}"
        elif text and voice1 and voice2:
            audio1_bytes, _ = generate_speech(text, voice=voice1)
            audio2_bytes, _ = generate_speech(text, voice=voice2)
            title = f"Mix: {voice1} & {voice2} ({text[:15]})"
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either prompt text/voice1/voice2, OR two uploaded files to blend."
            )
            
        mixed_bytes, duration = blend_audio_waveforms(
            audio1_bytes=audio1_bytes,
            audio2_bytes=audio2_bytes,
            blend_ratio=blend_ratio
        )
        
        url = upload_audio(mixed_bytes, filename="mixed.wav")
        
        db_audio = AudioFile(
            title=title,
            model_used="Speech Blend",
            voice_name=f"Blend {blend_ratio}",
            cloudinary_url=url,
            duration=duration,
            user_id=current_user.id
        )
        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)
        return db_audio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech blending failed: {str(e)}")

@app.get("/api/history", response_model=List[AudioFileResponse])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch history of voice generations for the authenticated user.
    """
    return db.query(AudioFile).filter(AudioFile.user_id == current_user.id).order_by(AudioFile.created_at.desc()).all()
