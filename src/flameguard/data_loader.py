"""Load raw NASA files exactly as published, with header validation.

Raw values are returned as strings so nothing is silently coerced here; all
parsing and cleaning lives in preprocessing.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FLEX_DIR = PROJECT_ROOT / "data" / "raw" / "flex"
FLEX_TABLE_PATH = RAW_FLEX_DIR / "PSI-69_Experimental table_FLEX.csv"

# Published header -> internal raw name. Subscripts were lost in the PSI export
# ("O" is O2, "CO" is CO2) and the burning-rate unit is really mm^2/s; the
# internal names record the corrected meaning.
FLEX_RAW_COLUMNS: dict[str, str] = {
    "FLEX Test #": "test_no",
    "FLEX Identifier": "flex_identifier",
    "Test Date": "test_date",
    "Test GMT": "test_gmt",
    "Fuel": "fuel",
    "Ambient pressure; mmHg": "pressure_mmhg",
    "O initial ambient composition; mole fraction": "x_o2",
    "N initial ambient composition; mole fraction": "x_n2",
    "CO initial ambient composition; mole fraction": "x_co2",
    "He initial ambient composition; mole fraction": "x_he",
    "Droplet initial diameter; mm": "d0_mm",
    "Visible flame extinction diameter; mm": "d_ext_mm",
    "Burning rate; mm": "burn_rate_mm2_s",
    "Burn time; s": "burn_time_s",
    "Test end": "test_end",
}

# The PSI CSV is Windows-1252 encoded (missing values are en dashes, byte 0x96).
FLEX_ENCODING = "cp1252"


def load_flex_raw(path: Path | str = FLEX_TABLE_PATH) -> pd.DataFrame:
    """Read the FLEX experimental table with every value kept as a raw string.

    Adds `source_row`: the 1-based line number in the CSV (header is line 1),
    so any cleaned value can be traced back to the original file.

    Raises:
        FileNotFoundError: the file is missing (run scripts/download_flex.py).
        ValueError: the header differs from the expected PSI-69 layout.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python scripts/download_flex.py")

    raw = pd.read_csv(path, encoding=FLEX_ENCODING, dtype=str, keep_default_na=False)

    expected = list(FLEX_RAW_COLUMNS)
    actual = list(raw.columns)
    if actual != expected:
        missing = [c for c in expected if c not in actual]
        extra = [c for c in actual if c not in expected]
        raise ValueError(
            f"Unexpected FLEX header in {path.name}. Missing: {missing}. Unexpected: {extra}. "
            "The PSI file may have been revised; update FLEX_RAW_COLUMNS after checking it."
        )
    if raw.empty:
        raise ValueError(f"{path.name} contains no rows")

    raw = raw.rename(columns=FLEX_RAW_COLUMNS)
    raw = raw.apply(lambda col: col.str.strip())
    raw.insert(0, "source_row", range(2, len(raw) + 2))
    return raw
