import io
import os
import soundfile as sf

# Try importing Kokoro
has_kokoro = False
try:
    from kokoro import KPipeline
    has_kokoro = True
except Exception as e:
    print(f"Kokoro package not available or failed to load: {e}. Using fallback engines.")

# Fallback engine: gTTS (Google Text-to-Speech)
try:
    from gtts import gTTS
    has_gtts = True
except ImportError:
    has_gtts = False
    print("gTTS package not installed. Ensure gTTS is installed.")

def generate_speech(text: str, voice: str = "af_heart", speed: float = 1.0, pitch: float = 1.0) -> tuple[bytes, float]:
    """
    Synthesize text into speech using Kokoro TTS (or gTTS fallback).
    
    Args:
        text: The phrase or text payload to speak.
        voice: The voice ID/gender combination.
        speed: The multiplier for speed of speech.
        pitch: The frequency pitch multiplier.
        
    Returns:
        A tuple of (audio_bytes, duration_in_seconds).
    """
    if has_kokoro:
        try:
            # American 'a' or British 'b' based on voice prefix
            lang = 'b' if voice.startswith('b') else 'a'
            pipeline = KPipeline(lang_code=lang)
            generator = pipeline(text, voice=voice, speed=speed)
            
            audio_chunks = []
            sample_rate = 24000
            for _, _, audio in generator:
                audio_chunks.append(audio)
            
            if audio_chunks:
                import numpy as np
                full_audio = np.concatenate(audio_chunks)
                
                # Apply pitch shifting using SciPy interpolation if requested and pitch != 1.0
                if pitch != 1.0:
                    try:
                        from scipy.ndimage import zoom
                        full_audio = zoom(full_audio, 1.0 / pitch)
                    except Exception as pe:
                        print(f"Pitch shift failed: {pe}")
                
                buf = io.BytesIO()
                sf.write(buf, full_audio, sample_rate, format="WAV")
                duration = len(full_audio) / sample_rate
                return buf.getvalue(), duration
        except Exception as e:
            print(f"Kokoro synthesis failed: {e}. Falling back.")
            
    # Fallback 1: gTTS
    if has_gtts:
        try:
            tts = gTTS(text=text, lang='en', slow=(speed < 0.85))
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            mp3_bytes = buf.getvalue()
            # Calculate estimation of audio duration
            duration = max(1.0, len(text) / 15.0)
            return mp3_bytes, duration
        except Exception as e:
            print(f"gTTS synthesis failed: {e}. Using beep synth.")
            
    # Fallback 2: Basic numpy synthesized sine waves (beep tone) to represent text
    import numpy as np
    sample_rate = 24000
    duration = max(1.0, len(text) / 13.0)
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Synthesize simple voice-like harmonic tone
    audio = 0.4 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t)
    # Apply standard fade out
    fade_len = int(sample_rate * 0.1)
    if len(audio) > fade_len:
        audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
        
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV")
    return buf.getvalue(), duration
