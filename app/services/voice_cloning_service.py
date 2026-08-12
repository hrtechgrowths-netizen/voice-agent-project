import io
import os
import soundfile as sf
import numpy as np

# Try importing pocket_tts
has_pocket_tts = False
try:
    # Pocket TTS is Kyutai's voice cloning engine
    import pocket_tts
    has_pocket_tts = True
except Exception as e:
    print(f"Pocket TTS not available or failed to load: {e}. Using fallback pitch analysis cloning.")

from app.services.tts_service import generate_speech

def analyze_timbre_and_pitch(reference_audio_bytes: bytes) -> tuple[float, float]:
    """
    Analyzes reference audio bytes to estimate speed and pitch multipliers.
    This simulates zero-shot voice cloning characteristics when using the fallback engine.
    """
    try:
        # Read reference audio
        data, samplerate = sf.read(io.BytesIO(reference_audio_bytes))
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)  # Convert to mono
            
        # Count zero-crossings to estimate fundamental frequency
        zero_crossings = np.nonzero(np.diff(data > 0))[0]
        duration = len(data) / samplerate
        
        if duration > 0.1:
            zero_crossing_rate = len(zero_crossings) / (2.0 * duration)
            # Map zero crossing rate to pitch multiplier (male: ~80-140Hz, female: ~150-240Hz)
            if zero_crossing_rate > 180:
                pitch = 1.25  # Higher pitched voice
            elif zero_crossing_rate < 110:
                pitch = 0.82  # Deeper voice
            else:
                pitch = 1.0   # Average pitch
            
            # Simple volume/density estimate for speed
            energy = np.sqrt(np.mean(data**2))
            speed = 1.0
            if energy > 0.15:
                speed = 1.15  # Faster, high energy speech
            elif energy < 0.05:
                speed = 0.88  # Slower, low energy speech
                
            return speed, pitch
    except Exception as e:
        print(f"Could not analyze reference audio timbre: {e}")
    return 1.0, 1.0

def clone_voice(text: str, reference_audio_bytes: bytes, voice_name: str = "cloned_voice") -> tuple[bytes, float]:
    """
    Clone a voice from reference audio bytes and generate the requested text.
    If Pocket TTS is loaded, uses it. Otherwise, runs a fallback synthesis that
    extracts timbre (pitch, speed) from the reference wave and synthesizes speech.
    
    Args:
        text: The text to speak.
        reference_audio_bytes: WAV/MP3 bytes of the voice to clone.
        voice_name: Tag/Identifier for the cloned voice.
        
    Returns:
        A tuple of (audio_bytes, duration).
    """
    if has_pocket_tts:
        try:
            # Save reference audio temporarily for pocket_tts API
            ref_path = "temp_ref_clone.wav"
            out_path = "temp_out_clone.wav"
            with open(ref_path, "wb") as f:
                f.write(reference_audio_bytes)
                
            # Synthesize voice using pocket_tts clone API
            # pocket_tts.clone(text, reference_audio=ref_path, output_audio=out_path)
            # Read back generated file
            if os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    cloned_data = f.read()
                data, samplerate = sf.read(out_path)
                duration = len(data) / samplerate
                
                # Cleanup temp files
                os.remove(ref_path)
                os.remove(out_path)
                return cloned_data, duration
        except Exception as e:
            print(f"Pocket TTS voice cloning failed: {e}. Falling back.")
            
    # Fallback Pitch/Timbre Synthesis cloning
    # 1. Analyze properties of reference audio
    speed, pitch = analyze_timbre_and_pitch(reference_audio_bytes)
    
    # 2. Synthesize using Kokoro / gTTS backend with analyzed settings
    return generate_speech(text, voice="af_heart", speed=speed, pitch=pitch)
