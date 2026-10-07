"""Build the pitch timeline: every scene's start/duration, which voice line it carries, and music sections.

Visual-only beats (cold open, logo reveal, feature montage, outro hold) are inserted between narrated scenes.
Writes demo/out/pitch2/timeline.json and demo/out/pitch2/timeline.js (window.TIMELINE for the director page).
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch2"
PAD = 0.75   # silence after each narrated line
LEAD = 0.25  # silence before a line starts inside its scene

# (scene id, voice id or None, extra seconds of visual-only time)
ORDER = [
    ("cold_open", None, 3.2),
    ("s01", "s01", 0), ("s02", "s02", 0),
    ("s03", "s03", 0.6),
    ("logo", None, 3.4),
    ("s04", "s04", 0),
    ("whyhit", None, 2.2),
    ("s05", "s05", 0), ("s06", "s06", 0), ("s07", "s07", 0.6), ("s08", "s08", 0),
    ("reveal", None, 2.6),
    ("s09", "s09", 0), ("s10", "s10", 0), ("s11", "s11", 0.4),
    ("s12", "s12", 0), ("s13", "s13", 0), ("s14", "s14", 0), ("s15", "s15", 0), ("s16", "s16", 0), ("s17", "s17", 0),
    ("s18", "s18", 0.2),
    ("montage", None, 5.4),
    ("s19", "s19", 0), ("s20", "s20", 0), ("s21", "s21", 0.8),
    ("s22", "s22", 3.8),
]

# Music energy per scene range (used by make_music.py)
SECTIONS = [("intro", "cold_open"), ("who", "s03"), ("why", "whyhit"), ("what", "reveal"), ("impact", "s19"),
            ("outro", "s22")]


def main() -> None:
    durs = json.loads((OUT / "voice" / "durations.json").read_text())
    t = 0.0
    scenes = []
    for sid, voice, extra in ORDER:
        dur = (LEAD + durs[voice] + PAD if voice else 0.0) + extra
        scenes.append({"id": sid, "start": round(t, 3), "dur": round(dur, 3), "voice": voice,
                       "voice_at": round(t + LEAD, 3) if voice else None})
        t += dur
    starts = {s["id"]: s["start"] for s in scenes}
    sections = []
    for i, (name, first) in enumerate(SECTIONS):
        end = starts[SECTIONS[i + 1][1]] if i + 1 < len(SECTIONS) else t
        sections.append({"name": name, "start": starts[first], "end": round(end, 3)})
    timeline = {"total": round(t, 3), "scenes": scenes, "sections": sections}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "timeline.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    (OUT / "timeline.js").write_text("window.TIMELINE = " + json.dumps(timeline) + ";\n", encoding="utf-8")
    print(f"total {t:.1f}s ({int(t // 60)}:{int(t % 60):02d}), {len(scenes)} scenes")
    for s in sections:
        print(f"  {s['name']:<7} {s['start']:6.1f} -> {s['end']:6.1f}")


if __name__ == "__main__":
    main()
