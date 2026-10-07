"""Synthesize the demo narration (demo/narration.json) with Piper, an offline neural text-to-speech engine.

Writes one WAV per segment to demo/out/voice/<id>.wav and prints each duration.

    python demo/make_voiceover.py --voice path/to/en_US-lessac-high.onnx
"""

from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="Piper .onnx voice model")
    ap.add_argument("--pace", type=float, default=1.0, help="length scale: >1 slower, <1 faster")
    args = ap.parse_args()

    voice = PiperVoice.load(args.voice)
    out = HERE / "out" / "voice"
    out.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for seg in json.loads((HERE / "narration.json").read_text(encoding="utf-8")):
        path = out / f"{seg['id']}.wav"
        with wave.open(str(path), "wb") as wf:
            voice.synthesize_wav(seg["text"], wf, syn_config=SynthesisConfig(length_scale=args.pace))
        with wave.open(str(path), "rb") as wf:
            seconds = wf.getnframes() / wf.getframerate()
        total += seconds
        print(f"{seg['id']:<12} {seconds:5.1f} s")
    print(f"{'total':<12} {total:5.1f} s")


if __name__ == "__main__":
    main()
