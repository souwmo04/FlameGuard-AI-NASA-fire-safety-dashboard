"""Phase 12: per-series O2_50 suppressant comparison from observed FLEX data.

Writes reports/phase12/o2_50_by_series.csv (used by the dashboard).

Usage:  .venv/Scripts/python scripts/suppressant_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from flameguard.suppressant import summarize_series  # noqa: E402

OUT = ROOT / "reports" / "phase12"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    table = summarize_series(master)
    table.to_csv(OUT / "o2_50_by_series.csv", index=False)
    pd.set_option("display.width", 220)
    print(table.round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
