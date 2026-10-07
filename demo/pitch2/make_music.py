"""Compose an original background track for the pitch (no samples, no licences needed).

Additive-synthesis pads, a plucked arpeggio, sub bass, a soft kick and hats, risers before big moments and a
convolution reverb. Energy follows the timeline sections: intro -> who -> why -> what (full) -> impact -> outro.

    python demo/pitch2/make_music.py   ->  demo/out/pitch2/music.wav (44.1 kHz stereo)
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch2"
SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

# A minor: Am - F - C - G, two bars each
CHORDS = [
    (45, [57, 60, 64, 69]),  # Am
    (41, [53, 57, 60, 65]),  # F
    (48, [55, 60, 64, 67]),  # C
    (43, [55, 59, 62, 67]),  # G
]


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n: int, a: float, r: float) -> np.ndarray:
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def pad_note(m: int, dur: float, bright: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for cents in (-7, 0, 7):
        f = hz(m) * 2 ** (cents / 1200)
        for k in range(1, 7):
            out += np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) * (1 / k ** (2.2 - bright))
    return out * env_adsr(n, 1.2, 1.6) / 10


def pluck(m: int, dur: float = 0.5) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)) * np.exp(-t * 7)


def kick() -> np.ndarray:
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 48 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)


def hat() -> np.ndarray:
    n = int(0.09 * SR)
    noise = rng.standard_normal(n + 1)
    return np.diff(noise) * np.exp(-np.arange(n) / SR * 55) * 0.25


def riser(dur: float) -> np.ndarray:
    n = int(dur * SR)
    noise = np.diff(rng.standard_normal(n + 1))
    return noise * np.linspace(0, 1, n) ** 2.5 * 0.18


def add(buf: np.ndarray, sig: np.ndarray, at: float, gain: float, pan: float = 0.0) -> None:
    i = int(at * SR)
    if i >= buf.shape[1]:
        return
    sig = sig[: buf.shape[1] - i]
    buf[0, i:i + len(sig)] += sig * gain * (1 - max(0.0, pan))
    buf[1, i:i + len(sig)] += sig * gain * (1 + min(0.0, pan))


def reverb(x: np.ndarray, seconds: float = 2.6, wet: float = 0.32) -> np.ndarray:
    n_ir = int(seconds * SR)
    t = np.arange(n_ir) / SR
    out = np.empty_like(x)
    block = 1 << 17
    for ch in range(2):
        ir = rng.standard_normal(n_ir) * np.exp(-t / 0.55)
        ir /= np.sqrt(np.sum(ir ** 2))
        nfft = 1 << int(np.ceil(np.log2(block + n_ir)))
        IR = np.fft.rfft(ir, nfft)
        y = np.zeros(x.shape[1] + n_ir)
        for s in range(0, x.shape[1], block):
            seg = x[ch, s:s + block]
            conv = np.fft.irfft(np.fft.rfft(seg, nfft) * IR, nfft)[: len(seg) + n_ir]
            y[s:s + len(conv)] += conv
        out[ch] = x[ch] * (1 - wet) + y[: x.shape[1]] * wet * 0.9
    return out


def main() -> None:
    tl = json.loads((OUT / "timeline.json").read_text())
    total = tl["total"] + 1.5
    sec = {s["name"]: (s["start"], s["end"]) for s in tl["sections"]}
    level = lambda name: name  # noqa: E731 (documentation only)

    def section_at(t: float) -> str:
        for name, (a, b) in sec.items():
            if a <= t < b:
                return name
        return "outro"

    n = int(total * SR)
    pads = np.zeros((2, n))
    arps = np.zeros((2, n))
    drums = np.zeros((2, n))
    bass = np.zeros((2, n))

    chord_len = 2 * BAR
    t = 0.0
    ci = 0
    while t < total:
        root, notes = CHORDS[ci % 4]
        s = section_at(t)
        bright = {"intro": 0.4, "who": 0.6, "why": 0.5, "what": 0.9, "impact": 0.7, "outro": 0.5}[s]
        for j, m in enumerate(notes):
            add(pads, pad_note(m, chord_len + 1.6, bright), t, 0.9, pan=(-0.35, 0.35, -0.15, 0.15)[j])
        if s in ("why", "what", "impact"):
            nb = int((chord_len + 0.4) * SR)
            tt = np.arange(nb) / SR
            sub = np.sin(2 * np.pi * hz(root - 12) * tt) * env_adsr(nb, 0.08, 0.4)
            add(bass, sub, t, 0.16 if s == "what" else 0.12)
        # arpeggio: 16ths in "what", 8ths elsewhere (not in intro)
        if s != "intro":
            step = BEAT / (4 if s == "what" else 2)
            seq = notes + [x + 12 for x in notes]
            k = 0
            tt = t
            while tt < t + chord_len:
                g = {"who": 0.26, "why": 0.2, "what": 0.3, "impact": 0.24, "outro": 0.16}[s]
                add(arps, pluck(seq[k % len(seq)] + 12), tt, g, pan=(-0.5 if k % 2 else 0.5))
                k += 1
                tt += step
        # drums
        for b in range(8):
            tb = t + b * BEAT
            sb = section_at(tb)
            if sb == "what":
                add(drums, kick(), tb, 0.42)
                add(drums, hat(), tb + BEAT / 2, 1.1, pan=0.2)
                if b % 2 == 1:
                    add(drums, hat(), tb + BEAT / 4 * 3, 0.6, pan=-0.2)
            elif sb == "why" and b % 4 == 0:
                add(drums, kick(), tb, 0.3)           # heartbeat
                add(drums, kick(), tb + 0.28, 0.18)
            elif sb == "impact" and b % 2 == 0:
                add(drums, kick(), tb, 0.22)
        t += chord_len
        ci += 1

    fx = np.zeros((2, n))
    for name in ("who", "why", "what"):
        start = sec[name][0]
        add(fx, riser(2.4), max(0.0, start - 2.4), 1.0)
    # big hit + swell at the product reveal
    hit_at = sec["what"][0]
    add(fx, kick() * 0.7, hit_at, 1.0)

    mix = reverb(pads * 0.9 + arps * 0.8, 2.8, 0.38) + drums + bass + fx * 0.8
    # gentle master: fade in/out, soft clip, normalise
    fade_in = int(2.0 * SR)
    mix[:, :fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = int(4.0 * SR)
    mix[:, -fade_out:] *= np.linspace(1, 0, fade_out)
    mix = np.tanh(mix * 1.2)
    mix /= np.max(np.abs(mix)) / 0.89
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(OUT / "music.wav"), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"wrote {OUT / 'music.wav'} ({total:.1f} s)")


if __name__ == "__main__":
    main()
