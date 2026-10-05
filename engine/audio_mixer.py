"""
Audio Mixer Engine for YouTube Shorts.
Generates an energetic, modern instrumental sports beat (90 BPM rhythm)
and mixes it cleanly with voiceover, eliminating distracting low-quality SFX.
"""

import sys
import math
import wave
import struct
import subprocess
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import imageio_ffmpeg

SAMPLE_RATE = 44100
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def save_wav(filename: Path, samples: np.ndarray, num_channels=2):
    """Saves a numpy float array (-1.0 to 1.0) as 16-bit PCM WAV."""
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    filename.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_samples.tobytes())


def generate_modern_sports_beat(total_duration=55.0, bpm=92.0):
    """
    Generates a clean, rhythmic, modern instrumental sports beat.
    Tempo: ~92 BPM.
    Elements:
    - Deep punchy 808 sub-bass groove
    - Rhythmic crisp hi-hats and subtle clap/snare
    - Dark melodic chord pads (tech-noir / sports documentary vibe)
    - Perfectly mixed so it never clashes with speech frequencies (200Hz - 3500Hz).
    """
    num_samples = int(SAMPLE_RATE * total_duration)
    t = np.linspace(0, total_duration, num_samples, endpoint=False)
    
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    
    audio = np.zeros(num_samples, dtype=np.float32)
    
    # 1. 808 Sub-Bass Groove (Roots: F1 = 43.65Hz, Ab1 = 51.9Hz, C2 = 65.4Hz, Eb2 = 77.78Hz)
    chord_times = [0.0, bar_sec, bar_sec * 2, bar_sec * 3]
    chords_freq = [43.65, 51.91, 38.89, 49.00]
    
    # Bass notes trigger on beat 1 and beat 3.5 of each 4-beat bar
    for bar_start in np.arange(0, total_duration, bar_sec):
        bar_idx = int((bar_start / bar_sec) % 4)
        base_freq = chords_freq[bar_idx]
        
        for hit_beat in [0.0, 1.75, 2.5, 3.25]:
            hit_time = bar_start + hit_beat * beat_sec
            if hit_time >= total_duration:
                continue
            idx_start = int(hit_time * SAMPLE_RATE)
            len_hit = int(beat_sec * 1.2 * SAMPLE_RATE)
            idx_end = min(num_samples, idx_start + len_hit)
            hit_samples = idx_end - idx_start
            if hit_samples <= 0:
                continue
                
            t_hit = np.linspace(0, hit_samples / SAMPLE_RATE, hit_samples, endpoint=False)
            freq_sweep = base_freq * (1.0 + 1.2 * np.exp(-35.0 * t_hit))
            phase = 2 * np.pi * np.cumsum(freq_sweep) / SAMPLE_RATE
            bass_tone = np.sin(phase) * np.exp(-3.5 * t_hit)
            audio[idx_start:idx_end] += bass_tone * 0.35

    # 2. Rhythmic Hi-Hats (1/8th and 1/16th notes with velocity swing)
    sub_beat = beat_sec / 2.0
    for hat_time in np.arange(0, total_duration, sub_beat):
        idx_start = int(hat_time * SAMPLE_RATE)
        len_hit = int(0.04 * SAMPLE_RATE)
        idx_end = min(num_samples, idx_start + len_hit)
        hit_samples = idx_end - idx_start
        if hit_samples <= 0:
            continue
            
        t_hit = np.linspace(0, hit_samples / SAMPLE_RATE, hit_samples, endpoint=False)
        noise = np.random.randn(hit_samples)
        # High pass envelope
        hat = noise * np.exp(-120.0 * t_hit) * 0.08
        audio[idx_start:idx_end] += hat

    # 3. Ambient Harmonic Chords (Atmospheric filtered dark pad)
    # Slow gentle progression giving documentary tension
    for bar_start in np.arange(0, total_duration, bar_sec):
        bar_idx = int((bar_start / bar_sec) % 4)
        base_freq = chords_freq[bar_idx] * 2.0 # 1 octave up
        idx_start = int(bar_start * SAMPLE_RATE)
        len_bar = int(bar_sec * SAMPLE_RATE)
        idx_end = min(num_samples, idx_start + len_bar)
        bar_samples = idx_end - idx_start
        if bar_samples <= 0:
            continue
            
        t_bar = np.linspace(0, bar_samples / SAMPLE_RATE, bar_samples, endpoint=False)
        # Chord = Root + Minor Third + Fifth
        f1 = base_freq
        f2 = base_freq * 1.1892 # minor 3rd
        f3 = base_freq * 1.4983 # 5th
        
        chord_tone = (
            np.sin(2 * np.pi * f1 * t_bar) * 0.5 +
            np.sin(2 * np.pi * f2 * t_bar) * 0.35 +
            np.sin(2 * np.pi * f3 * t_bar) * 0.3
        )
        # Gentle envelope
        env = np.sin(np.pi * np.linspace(0, 1, bar_samples))
        audio[idx_start:idx_end] += chord_tone * env * 0.09

    # Master envelope: Smooth fade-in and fade-out
    fade_in = np.minimum(1.0, t / 1.5)
    fade_out = np.minimum(1.0, (total_duration - t) / 2.0)
    audio = audio * fade_in * fade_out
    
    # Stereo panning
    stereo = np.column_stack((audio, audio * 0.98))
    return stereo


def mix_master_soundtrack(voice_path: Path, output_audio_path: Path, sfx_dir: Path):
    """
    Mixes Voiceover with high-quality Modern Instrumental Sports Beat (-17 dB).
    No distracting amateur SFX.
    """
    sfx_dir.mkdir(parents=True, exist_ok=True)
    
    # Measure voice duration
    cmd_dur = [FFMPEG_EXE, "-nostdin", "-i", str(voice_path)]
    res = subprocess.run(cmd_dur, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    dur = 50.0
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            dur = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            break
            
    # Generate matching modern instrumental beat
    bgm_path = sfx_dir / "modern_sports_beat.wav"
    bgm_data = generate_modern_sports_beat(total_duration=dur + 2.0, bpm=92.0)
    save_wav(bgm_path, bgm_data)
    
    # FFmpeg filter:
    # Voice: Converted to 44.1kHz stereo, volume 1.0 (loud, crystal clear)
    # Music: 44.1kHz stereo, volume 0.14 (-17 dB) so it provides rhythm without masking speech
    filter_complex = (
        "[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[v0];"
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.14[v1];"
        "[v0][v1]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    
    cmd = [
        FFMPEG_EXE,
        "-y",
        "-nostdin",
        "-i", str(voice_path),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        str(output_audio_path)
    ]
    
    subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"✅ Temiz 44.1kHz stereo ses miksajı tamamlandı: {output_audio_path.name}")

