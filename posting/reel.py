from __future__ import annotations

import math
import os
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional

from imageio_ffmpeg import get_ffmpeg_exe

FFMPEG = get_ffmpeg_exe()

SLIDE_DURATION = 2.5
WIDTH = 1080
HEIGHT = 1920
FPS = 30
SAMPLE_RATE = 44100


def _generate_bg_music(duration: float, output_path: str | Path) -> str:
    """Generate a short ambient/electronic background music track as WAV."""
    n_samples = int(SAMPLE_RATE * duration)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    samples = []
    bpm = 120
    beat_sec = 60.0 / bpm

    for i in range(n_samples):
        t = i / SAMPLE_RATE

        # bass pulse on beats
        beat_phase = (t % beat_sec) / beat_sec
        bass = math.sin(2 * math.pi * 55 * t) * 0.15 * max(0, 1 - beat_phase * 4)
        bass += math.sin(2 * math.pi * 110 * t) * 0.08 * max(0, 1 - beat_phase * 4)

        # pad chord (Am7)
        chord = 0
        for freq in [220, 261.63, 329.63, 392]:
            chord += math.sin(2 * math.pi * freq * t) * 0.03

        # arpeggio
        arp_note = [440, 523.25, 659.25, 783.99]
        arp_idx = int((t * 2) % len(arp_note))
        arp = math.sin(2 * math.pi * arp_note[arp_idx] * t) * 0.04

        # hi-hat on 8th notes
        hat_phase = (t % (beat_sec / 2)) / (beat_sec / 2)
        hat = 0
        if hat_phase < 0.05:
            hat = math.sin(2 * math.pi * 8000 * t) * 0.06 * (1 - hat_phase / 0.05)

        sample = bass + chord + arp + hat

        # clip
        sample = max(-1, min(1, sample))
        samples.append(int(sample * 32767))

    with wave.open(str(out), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return str(out)


def images_to_video(
    image_paths: list[str],
    output_path: str | Path,
    audio_path: Optional[str | Path] = None,
    generate_audio: bool = True,
) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    total_duration = len(image_paths) * SLIDE_DURATION
    tmpdir = Path(tempfile.mkdtemp(prefix="reel_"))

    cmd = [FFMPEG, "-y"]
    filter_inputs = []
    stream_idx = 0
    n = len(image_paths)
    for img_path in image_paths:
        cmd.extend(["-loop", "1", "-t", str(SLIDE_DURATION), "-i", str(img_path)])
        filter_inputs.append(f"[{stream_idx}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setpts=PTS-STARTPTS[v{stream_idx}]")
        stream_idx += 1

    concat_filter = "".join(f"[v{i}]" for i in range(n))
    filter_inputs.append(f"{concat_filter}concat=n={n}:v=1:a=0[vout]")

    cmd.extend(["-filter_complex", ";".join(filter_inputs)])
    cmd.extend(["-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])

    subprocess.run(cmd, check=True, capture_output=True)

    # audio
    if audio_path:
        audio_source = str(audio_path)
    elif generate_audio:
        audio_source = _generate_bg_music(total_duration, tmpdir / "bgmusic.wav")
    else:
        audio_source = None

    if audio_source:
        audio_out = out.with_stem(out.stem + "_audio")
        subprocess.run(
            [
                FFMPEG, "-y", "-i", str(out), "-i", audio_source,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(audio_out),
            ],
            check=True, capture_output=True,
        )
        os.replace(str(audio_out), str(out))

    # cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    return str(out)
