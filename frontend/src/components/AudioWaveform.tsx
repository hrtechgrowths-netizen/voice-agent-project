import React, { useRef, useEffect, useState } from 'react';
import { Play, Pause } from 'lucide-react';

interface AudioWaveformProps {
  audioUrl: string;
  duration?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ audioUrl, duration }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration || 0);

  // Generate deterministic pseudo-random peak heights for custom canvas rendering
  const generatePeaks = (url: string, count: number): number[] => {
    const peaks: number[] = [];
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
      hash = url.charCodeAt(i) + ((hash << 5) - hash);
    }
    for (let i = 0; i < count; i++) {
      const r = Math.abs(Math.sin(hash + i * 453.2)) * 0.8 + 0.2;
      peaks.push(r);
    }
    return peaks;
  };

  useEffect(() => {
    // Instantiate new HTMLAudioElement pointing to API url
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => {
      if (audio.duration && audio.duration !== Infinity) {
        setTotalDuration(audio.duration);
      }
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.pause();
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
      audioRef.current = null;
    };
  }, [audioUrl]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const barWidth = 3;
    const barGap = 2;
    const count = Math.floor(width / (barWidth + barGap));
    const normalizedPeaks = generatePeaks(audioUrl, count);

    const progress = totalDuration > 0 ? currentTime / totalDuration : 0;
    const activeIndex = Math.floor(count * progress);

    for (let i = 0; i < count; i++) {
      const peak = normalizedPeaks[i];
      const barHeight = peak * (height - 8);
      const x = i * (barWidth + barGap);
      const y = (height - barHeight) / 2;

      if (i <= activeIndex) {
        // Neon Indigo/Purple gradient for the played section
        const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, '#6366f1');
        grad.addColorStop(1, '#a855f7');
        ctx.fillStyle = grad;
      } else {
        // Slate color for unplayed audio
        ctx.fillStyle = '#475569';
      }

      ctx.beginPath();
      // Round rect support (or manual rounded rectangles if older browser)
      if (typeof ctx.roundRect === 'function') {
        ctx.roundRect(x, y, barWidth, barHeight, 1.5);
      } else {
        ctx.rect(x, y, barWidth, barHeight);
      }
      ctx.fill();
    }
  }, [currentTime, totalDuration, audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => console.log('Audio autoplay error:', err));
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !audioRef.current || totalDuration === 0) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percent = clickX / rect.width;
    const seekTime = percent * totalDuration;
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (time: number) => {
    if (isNaN(time)) return '0:00';
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '10px 14px',
      background: 'var(--bg-tertiary)',
      border: '1px solid var(--glass-border)',
      borderRadius: '8px',
      width: '100%',
      boxSizing: 'border-box'
    }}>
      <button 
        onClick={togglePlay}
        style={{
          width: '34px',
          height: '34px',
          borderRadius: '50%',
          border: 'none',
          background: 'var(--accent-gradient)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'transform 0.2s ease',
          flexShrink: 0
        }}
      >
        {isPlaying ? <Pause size={14} fill="#fff" /> : <Play size={14} fill="#fff" style={{ marginLeft: '1px' }} />}
      </button>

      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
        <canvas
          ref={canvasRef}
          width={400}
          height={30}
          onClick={handleSeek}
          style={{
            width: '100%',
            height: '30px',
            cursor: 'pointer',
            display: 'block'
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(totalDuration)}</span>
        </div>
      </div>
    </div>
  );
};
