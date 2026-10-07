"""Voiceover for the motion-graphics pitch: Kokoro TTS (offline, open weights) from script.json.

    python demo/pitch2/make_voiceover.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin [--voice am_michael --speed 1.1]

Writes demo/out/pitch2/voice/<id>.wav and voice/durations.json (used by build_timeline.py).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch2" / "voice"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--voices", required=True)
    ap.add_argument("--voice", default="am_michael")
    ap.add_argument("--speed", type=float, default=1.1)
    args = ap.parse_args()
    kokoro = Kokoro(args.model, args.voices)
    lang = "en-gb" if args.voice.startswith("b") else "en-us"
    OUT.mkdir(parents=True, exist_ok=True)
    durations = {}
    for seg in json.loads((HERE / "script.json").read_text(encoding="utf-8")):
        audio, rate = kokoro.create(seg["text"], voice=args.voice, speed=args.speed, lang=lang)
        sf.write(OUT / f"{seg['id']}.wav", audio, rate, subtype="PCM_16")
        durations[seg["id"]] = round(len(audio) / rate, 2)
    (OUT / "durations.json").write_text(json.dumps(durations, indent=1), encoding="utf-8")
    print(f"{len(durations)} lines, {sum(durations.values()):.1f} s of speech")


if __name__ == "__main__":
    main()
