"""Synthesize the 4-minute pitch narration (pitch.json) with Kokoro, an open-weight neural TTS that runs offline.

    python demo/pitch/make_voiceover.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin [--voice am_michael]

Writes demo/out/pitch/voice/<id>.wav (16-bit PCM) and prints durations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch" / "voice"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--voices", required=True)
    ap.add_argument("--voice", default="am_michael")
    ap.add_argument("--speed", type=float, default=1.0)
    args = ap.parse_args()

    kokoro = Kokoro(args.model, args.voices)
    lang = "en-gb" if args.voice.startswith("b") else "en-us"
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0.0
    by_section: dict[int, float] = {}
    for seg in json.loads((HERE / "pitch.json").read_text(encoding="utf-8")):
        audio, rate = kokoro.create(seg["text"], voice=args.voice, speed=args.speed, lang=lang)
        sf.write(OUT / f"{seg['id']}.wav", audio, rate, subtype="PCM_16")
        seconds = len(audio) / rate
        total += seconds
        by_section[seg["section"]] = by_section.get(seg["section"], 0.0) + seconds
        print(f"{seg['id']:<14} {seconds:5.1f} s")
    print("sections:", {k: round(v, 1) for k, v in by_section.items()}, f"total {total:.1f} s")


if __name__ == "__main__":
    main()
