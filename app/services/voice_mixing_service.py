import io
import soundfile as sf
import numpy as np

def blend_audio_waveforms(audio1_bytes: bytes, audio2_bytes: bytes, blend_ratio: float = 0.5) -> tuple[bytes, float]:
    """
    Blends/mixes two audio files together using a weighted addition.
    Handles differing sample rates via linear interpolation resampling, and
    differing lengths by zero padding.
    
    Args:
        audio1_bytes: Raw audio content of the first sound layer.
        audio2_bytes: Raw audio content of the second sound layer.
        blend_ratio: Weight assigned to audio1 (from 0.0 to 1.0).
        
    Returns:
        A tuple of (mixed_audio_bytes, duration_in_seconds).
    """
    try:
        # Load audio 1
        data1, samplerate1 = sf.read(io.BytesIO(audio1_bytes))
        if len(data1.shape) > 1:
            data1 = np.mean(data1, axis=1)  # Mono conversion
            
        # Load audio 2
        data2, samplerate2 = sf.read(io.BytesIO(audio2_bytes))
        if len(data2.shape) > 1:
            data2 = np.mean(data2, axis=1)  # Mono conversion
            
        # Resample data2 to sample rate of data1 if they mismatch
        if samplerate1 != samplerate2:
            duration2 = len(data2) / samplerate2
            new_len = int(duration2 * samplerate1)
            data2 = np.interp(np.linspace(0, len(data2)-1, new_len), np.arange(len(data2)), data2)
            samplerate = samplerate1
        else:
            samplerate = samplerate1
            
        # Harmonize lengths
        len1 = len(data1)
        len2 = len(data2)
        max_len = max(len1, len2)
        
        # Pad with zeros
        if len1 < max_len:
            data1 = np.pad(data1, (0, max_len - len1), 'constant')
        if len2 < max_len:
            data2 = np.pad(data2, (0, max_len - len2), 'constant')
            
        # Weighted mix
        mixed_data = (blend_ratio * data1) + ((1.0 - blend_ratio) * data2)
        
        # Prevent clipping (normalize if max amplitude exceeds 1.0)
        max_val = np.max(np.abs(mixed_data))
        if max_val > 1.0:
            mixed_data = mixed_data / max_val
            
        # Write back to WAV buffer
        buf = io.BytesIO()
        sf.write(buf, mixed_data, samplerate, format="WAV")
        duration = len(mixed_data) / samplerate
        
        return buf.getvalue(), duration
        
    except Exception as e:
        print(f"Error blending waveforms: {e}")
        # Fallback to returning audio1
        return audio1_bytes, 1.0
