import os
import uuid
import cloudinary
import cloudinary.uploader
from io import BytesIO
from app.config import settings

# Initialize Cloudinary if credentials are provided
cloudinary_configured = False
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        cloudinary_configured = True
    except Exception as e:
        print(f"Failed to configure Cloudinary: {e}")

# Create local media dir if it doesn't exist for fallback
STATIC_MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static", "media")
os.makedirs(STATIC_MEDIA_DIR, exist_ok=True)

def upload_audio(audio_data: bytes, filename: str = "voice.wav") -> str:
    """
    Uploads audio bytes to Cloudinary. If Cloudinary credentials are not configured,
    or if upload fails, falls back to storing the audio locally under `/static/media`
    and returns a path served by FastAPI.
    
    Args:
        audio_data: The audio content in bytes.
        filename: Optional base filename.
    
    Returns:
        The URL/path where the audio is hosted.
    """
    if cloudinary_configured:
        try:
            # Upload buffer to Cloudinary (resource_type="video" handles audio files)
            result = cloudinary.uploader.upload_stream(
                BytesIO(audio_data),
                resource_type="video",
                public_id=f"voice_agent/{uuid.uuid4()}",
                format=filename.split(".")[-1]
            )
            secure_url = result.get("secure_url")
            if secure_url:
                return secure_url
        except Exception as e:
            print(f"Cloudinary upload error, falling back to local: {e}")
            
    # Local storage fallback
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(STATIC_MEDIA_DIR, unique_filename)
    with open(filepath, "wb") as f:
        f.write(audio_data)
    
    # Return local relative path that can be served by FastAPI
    return f"/static/media/{unique_filename}"
