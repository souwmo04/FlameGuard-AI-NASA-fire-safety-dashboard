"""Mix the narration onto the recording and encode the final MP4 (+ SRT subtitles).

Each voice segment is placed at the moment its scene actually started (demo/out/timings.json), so the voice
stays in sync even if a page took longer to load than planned.

    python demo/make_video.py   ->  demo/out/flameguard-demo.mp4, demo/out/flameguard-demo.srt
"""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
LEAD = 0.35  # seconds of silence before each scene's narration starts


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    timing = json.loads((OUT / "timings.json").read_text(encoding="utf-8"))
    segs = timing["segments"]

    first = wave.open(str(OUT / "voice" / f"{segs[0]['id']}.wav"), "rb")
    rate, width, channels = first.getframerate(), first.getsampwidth(), first.getnchannels()
    first.close()
    total = timing["total"]
    mix = np.zeros(int((total + 1) * rate), dtype=np.int16)
    srt = []
    for i, s in enumerate(segs, 1):
        with wave.open(str(OUT / "voice" / f"{s['id']}.wav"), "rb") as wf:
            pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        at = int((s["start"] + LEAD) * rate)
        mix[at:at + len(pcm)] = pcm[: max(0, len(mix) - at)]
        srt.append(f"{i}\n{srt_time(s['start'] + LEAD)} --> {srt_time(s['start'] + LEAD + s['voice'])}\n{s['text'].replace('A I', 'AI')}\n")
    with wave.open(str(OUT / "narration.wav"), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(mix.tobytes())
    (OUT / "flameguard-demo.srt").write_text("\n".join(srt), encoding="utf-8")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fade_out = max(0.0, total - 1.2)
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-i", str(OUT / "raw.webm"), "-i", str(OUT / "narration.wav"),
        "-map", "0:v", "-map", "1:a",
        "-vf", f"fps=30,fade=t=in:st=0:d=0.6,fade=t=out:st={fade_out:.2f}:d=1.2",
        "-af", f"afade=t=out:st={fade_out:.2f}:d=1.2,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
        str(OUT / "flameguard-demo.mp4"),
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {OUT / 'flameguard-demo.mp4'} ({total:.1f} s)")


if __name__ == "__main__":
    main()
