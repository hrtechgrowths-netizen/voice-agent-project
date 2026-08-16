from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import engine, Base, get_db
from app.models import User, AudioFile
from app.schemas import (
    UserCreate,
    UserResponse,
    Token,
    AudioFileResponse,
    TTSRequest,
)
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_or_create_development_user,
)

from app.services.cloudinary_service import upload_audio
from app.services.tts_service import generate_speech
from app.services.voice_cloning_service import clone_voice
from app.services.voice_mixing_service import blend_audio_waveforms


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="AI Voice Platform API")


# ============================================================
# CORS
# ============================================================
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="AI Voice Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# STATIC FILES
# ============================================================

static_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
)

os.makedirs(static_dir, exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=static_dir),
    name="static",
)


# ============================================================
# AUTH - SIGNUP
# ============================================================

@app.post("/api/auth/signup", response_model=UserResponse)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    db_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(
        user_data.password
    )

    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# AUTH - LOGIN
# ============================================================

@app.post("/api/auth/login", response_model=Token)
def login(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if not user or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ============================================================
# TEXT TO SPEECH
# ============================================================

@app.post(
    "/api/tts/generate",
    response_model=AudioFileResponse,
)
def generate_tts(
    request: TTSRequest,
    db: Session = Depends(get_db),
):
    try:
        audio_bytes, duration = generate_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch,
        )

        title = f"TTS: {request.text[:30]}"

        url = upload_audio(
            audio_bytes,
            filename="tts.wav",
        )

        dev_user = get_or_create_development_user(db)

        db_audio = AudioFile(
            title=title,
            model_used="Kokoro TTS",
            voice_name=request.voice,
            cloudinary_url=url,
            duration=duration,
            user_id=dev_user.id,
        )

        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)

        return db_audio

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Speech generation failed: {str(e)}",
        )


# ============================================================
# VOICE CLONING
# ============================================================

@app.post(
    "/api/voice-cloning/clone",
    response_model=AudioFileResponse,
)
async def clone_voice_endpoint(
    text: str = Form(...),
    voice_name: str = Form("cloned_voice"),
    reference_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        ref_bytes = await reference_file.read()

        audio_bytes, duration = clone_voice(
            text=text,
            reference_audio_bytes=ref_bytes,
            voice_name=voice_name,
        )

        title = f"Cloned: {text[:30]}"

        url = upload_audio(
            audio_bytes,
            filename="cloned.wav",
        )

        dev_user = get_or_create_development_user(db)

        db_audio = AudioFile(
            title=title,
            model_used="Pocket TTS Clone",
            voice_name=voice_name,
            cloudinary_url=url,
            duration=duration,
            user_id=dev_user.id,
        )

        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)

        return db_audio

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice cloning failed: {str(e)}",
        )


# ============================================================
# VOICE MIXING
# ============================================================

@app.post(
    "/api/voice-mixing/blend",
    response_model=AudioFileResponse,
)
async def mix_voices_endpoint(
    text: Optional[str] = Form(None),
    voice1: Optional[str] = Form(None),
    voice2: Optional[str] = Form(None),
    blend_ratio: float = Form(0.5),
    audio1: Optional[UploadFile] = File(None),
    audio2: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    try:
        # Two uploaded audio files
        if audio1 and audio2:
            audio1_bytes = await audio1.read()
            audio2_bytes = await audio2.read()

            title = (
                f"Mix: {audio1.filename} & "
                f"{audio2.filename}"
            )

        # Generate two voices from text
        elif text and voice1 and voice2:
            audio1_bytes, _ = generate_speech(
                text,
                voice=voice1,
            )

            audio2_bytes, _ = generate_speech(
                text,
                voice=voice2,
            )

            title = (
                f"Mix: {voice1} & "
                f"{voice2} ({text[:15]})"
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Must provide either prompt text/voice1/voice2, "
                    "OR two uploaded files to blend."
                ),
            )

        mixed_bytes, duration = blend_audio_waveforms(
            audio1_bytes=audio1_bytes,
            audio2_bytes=audio2_bytes,
            blend_ratio=blend_ratio,
        )

        url = upload_audio(
            mixed_bytes,
            filename="mixed.wav",
        )

        dev_user = get_or_create_development_user(db)

        db_audio = AudioFile(
            title=title,
            model_used="Speech Blend",
            voice_name=f"Blend {blend_ratio}",
            cloudinary_url=url,
            duration=duration,
            user_id=dev_user.id,
        )

        db.add(db_audio)
        db.commit()
        db.refresh(db_audio)

        return db_audio

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Speech blending failed: {str(e)}",
        )


# ============================================================
# AUDIO HISTORY
# ============================================================

@app.get(
    "/api/history",
    response_model=List[AudioFileResponse],
)
def get_history(
    db: Session = Depends(get_db),
):
    dev_user = get_or_create_development_user(db)

    return (
        db.query(AudioFile)
        .filter(AudioFile.user_id == dev_user.id)
        .order_by(AudioFile.created_at.desc())
        .all()
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "AI Voice Platform API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
