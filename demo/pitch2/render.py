"""Render the motion-graphics pitch: record director.html in real time, then mix voice + music and encode.

    python demo/pitch2/render.py            -> demo/out/pitch2/flameguard-pitch-4min.mp4 (+ .srt)
    python demo/pitch2/render.py --mix-only (re-mix audio onto an existing recording)

Order of the full pipeline: make voice (script.json) -> build_timeline.py -> make_music.py -> record_clips.py -> render.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch2"
NAME = "flameguard-pitch-4min"
W, H = 1920, 1080


FPS = 30


def record(limit: float | None = None) -> float:
    """Render director.html frame by frame on its virtual clock and encode the frames to raw.mp4 (video only)."""
    tl = json.loads((OUT / "timeline.json").read_text())
    total = limit or tl["total"]
    frames = int(round(total * FPS))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    enc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                            str(OUT / "raw.mp4")], stdin=subprocess.PIPE)
    t_start = time.monotonic()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto((HERE / "director.html").as_uri())
        page.wait_for_function("window.__ready === true", timeout=300000)
        for f in range(frames):
            page.evaluate("t => window.__renderAt(t)", f / FPS)
            enc.stdin.write(page.screenshot(type="jpeg", quality=93))
            if f % 300 == 0:
                el = time.monotonic() - t_start
                print(f"frame {f}/{frames}  {el:5.0f}s elapsed  eta {el / max(f, 1) * (frames - f):5.0f}s", flush=True)
        browser.close()
    enc.stdin.close()
    enc.wait()
    print(f"rendered {frames} frames in {time.monotonic() - t_start:.0f}s")
    (OUT / "render.json").write_text(json.dumps({"go_at": 0.0}), encoding="utf-8")
    return 0.0


def mix_and_encode(go_at: float) -> None:
    tl = json.loads((OUT / "timeline.json").read_text())
    total = tl["total"]
    voices = [s for s in tl["scenes"] if s["voice"]]
    with wave.open(str(OUT / "voice" / f"{voices[0]['voice']}.wav"), "rb") as wf:
        rate = wf.getframerate()
    track = np.zeros(int((total + 2) * rate), dtype=np.int16)
    srt = []
    script = {s["id"]: s["text"] for s in json.loads((HERE / "script.json").read_text(encoding="utf-8"))}
    for i, s in enumerate(voices, 1):
        with wave.open(str(OUT / "voice" / f"{s['voice']}.wav"), "rb") as wf:
            pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        at = int(s["voice_at"] * rate)
        track[at:at + len(pcm)] = pcm[: len(track) - at]
        end = s["voice_at"] + len(pcm) / rate
        fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t * 1000)) % 1000:03d}"  # noqa: E731
        srt.append(f"{i}\n{fmt(s['voice_at'])} --> {fmt(end)}\n{script[s['voice']].replace('A I', 'AI')}\n")
    with wave.open(str(OUT / "voice_track.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(track.tobytes())
    (OUT / f"{NAME}.srt").write_text("\n".join(srt), encoding="utf-8")

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    end_fade = total - 1.5
    # Music level: the dense demo section plays lower (it has drums under narration); the montage keeps full energy.
    sec = {x["name"]: x for x in tl["sections"]}
    montage = next(x["start"] for x in tl["scenes"] if x["id"] == "montage")
    ws, we = sec["what"]["start"], montage
    graph = (
        "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[vk][vs];"
        f"[2:a]aresample=48000,volume='0.5*if(between(t,{ws:.2f},{we:.2f}),0.4,1)':eval=frame[mu];"
        "[mu][vs]sidechaincompress=threshold=0.012:ratio=8:attack=10:release=600:makeup=1[duck];"
        f"[duck][vk]amix=inputs=2:weights='1 1':normalize=0,afade=t=out:st={end_fade:.2f}:d=1.5,"
        "loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]"
    )
    cmd = [ff, "-y", "-loglevel", "error", "-ss", f"{go_at:.3f}", "-i", str(OUT / "raw.mp4"),
           "-i", str(OUT / "voice_track.wav"), "-i", str(OUT / "music.wav"),
           "-filter_complex", graph + f";[0:v]fps=30,scale=in_range=pc:out_range=tv,format=yuv420p,fade=t=in:st=0:d=0.5,fade=t=out:st={end_fade:.2f}:d=1.5[v]",
           "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-color_range", "tv", "-movflags", "+faststart", str(OUT / f"{NAME}.mp4")]
    subprocess.run(cmd, check=True)
    print(f"wrote {OUT / (NAME + '.mp4')} ({total:.1f} s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mix-only", action="store_true")
    ap.add_argument("--preview", type=float, help="render only the first N seconds (for checking)")
    args = ap.parse_args()
    if args.preview:
        record(args.preview)
        return
    go_at = json.loads((OUT / "render.json").read_text())["go_at"] if args.mix_only else record()
    mix_and_encode(go_at)


if __name__ == "__main__":
    main()
