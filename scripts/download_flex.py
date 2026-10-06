"""Download the FLEX (PSI-69) raw data from NASA Physical Sciences Informatics.

Fetches:
  - the FLEX experimental table CSV          -> data/raw/flex/
  - the PSI investigation metadata (JSON)    -> data/raw/flex/
  - NASA/TP-2015-216046 (FLEX results report) -> documents/flex/

and writes data/raw/flex/MANIFEST.json with source URL, DOI, size and SHA-256
for every file, so the raw inputs are traceable and verifiable.

Usage (from the project root):
    python scripts/download_flex.py            # skip files that already exist
    python scripts/download_flex.py --force    # re-download everything

Uses only the Python standard library. Raw files are never modified after
download; all cleaning happens downstream in src/flameguard/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "flex"
DOCS_DIR = ROOT / "documents" / "flex"

PSI_ID = "PSI-69"
PSI_DOI = "10.60555/mbq8-0451"
PSI_LICENSE = "CC0-1.0"
PSI_API = "https://psi.nasa.gov/geode-py/ws"
TABLE_FILE = "PSI-69_Experimental table_FLEX.csv"

REPORT_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf"
REPORT_FILE = "NASA-TP-2015-216046_FLEX_results_2009-2011.pdf"

USER_AGENT = "FlameGuard-AI/0.1 (NASA Space Apps 2026 research prototype)"


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def psi_signed_url(psi_id: str, file_name: str, version: int = 1) -> str:
    """PSI's download endpoint returns a short-lived signed S3 URL as plain text."""
    query = urllib.parse.urlencode(
        {"file": file_name, "version": version, "redirect": "false"},
        quote_via=urllib.parse.quote,
    )
    url = f"{PSI_API}/studies/{psi_id}/download?{query}"
    return http_get(url).decode().strip().strip('"')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url_fn, dest: Path, force: bool) -> str:
    """Download to dest unless it exists. url_fn is called lazily (signed URLs expire)."""
    if dest.exists() and not force:
        print(f"  exists, skipping: {dest.relative_to(ROOT)}")
        return "existing"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = http_get(url_fn())
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    print(f"  downloaded: {dest.relative_to(ROOT)} ({len(data):,} bytes)")
    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args()

    print(f"FLEX ({PSI_ID}, DOI {PSI_DOI}, license {PSI_LICENSE})")

    metadata_path = RAW_DIR / f"{PSI_ID}_investigation_metadata.json"
    table_path = RAW_DIR / TABLE_FILE
    report_path = DOCS_DIR / REPORT_FILE

    sources = {
        metadata_path: f"{PSI_API}/repo/investigations/{PSI_ID}",
        table_path: f"https://psi.nasa.gov/physci/repo/data/investigations/{PSI_ID} ({TABLE_FILE})",
        report_path: REPORT_URL,
    }

    try:
        fetch(lambda: sources[metadata_path], metadata_path, args.force)
        fetch(lambda: psi_signed_url(PSI_ID, TABLE_FILE), table_path, args.force)
        fetch(lambda: REPORT_URL, report_path, args.force)
    except Exception as exc:  # network / HTTP errors
        print(f"ERROR: download failed: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "investigation": PSI_ID,
        "program": "FLEX - Flame Extinguishment Experiment (ISS, MDCA in CIR)",
        "doi": f"https://doi.org/{PSI_DOI}",
        "license": PSI_LICENSE,
        "citation_note": "PSI requires citing the investigation DOI in any publication or presentation.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": [
            {
                "path": p.relative_to(ROOT).as_posix(),
                "source": sources[p],
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            }
            for p in (table_path, metadata_path, report_path)
        ],
    }
    manifest_path = RAW_DIR / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
