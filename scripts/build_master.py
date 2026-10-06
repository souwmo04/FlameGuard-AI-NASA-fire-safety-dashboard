"""Build data/processed/combustion_master.csv from the raw FLEX table.

Usage (from the project root):
    python scripts/build_master.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flameguard.data_loader import load_flex_raw  # noqa: E402
from flameguard.preprocessing import clean_flex, qc_summary  # noqa: E402

OUT_DIR = ROOT / "data" / "processed"


def main() -> int:
    raw = load_flex_raw()
    master = clean_flex(raw)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master_path = OUT_DIR / "combustion_master.csv"
    master.to_csv(master_path, index=False, encoding="utf-8")

    summary = qc_summary(master)
    (OUT_DIR / "qc_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {master_path.relative_to(ROOT)}: {master.shape[0]} rows x {master.shape[1]} columns")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
