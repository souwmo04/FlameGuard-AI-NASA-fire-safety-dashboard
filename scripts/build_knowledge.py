"""Phase 13: build the "Ask FlameGuard" knowledge base.

Reads NASA/TP-2015-216046 (documents/flex/, fetched by scripts/download_flex.py) and the project's
docs, chunks them, embeds every chunk with BAAI/bge-small-en-v1.5 and writes

    data/knowledge/chunks.jsonl     one chunk per line (text + citation metadata)
    data/knowledge/embeddings.npy   float16 matrix, one row per chunk
    data/knowledge/manifest.json    model, counts per source, input checksums

Both outputs are committed so the API never needs the 41 MB PDF. Re-run after editing the docs:
    .venv/Scripts/python scripts/build_knowledge.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flameguard.knowledge import DOCS, EMBED_MODEL, Embedder, build_corpus, save_corpus  # noqa: E402

PDF = ROOT / "documents" / "flex" / "NASA-TP-2015-216046_FLEX_results_2009-2011.pdf"
OUT = ROOT / "data" / "knowledge"
CACHE = ROOT / ".cache" / "fastembed"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> None:
    if not PDF.exists():
        sys.exit(f"Missing {PDF.relative_to(ROOT)} - run scripts/download_flex.py first.")
    t0 = time.time()
    chunks = build_corpus(ROOT, PDF)
    print(f"{len(chunks)} chunks from {len(set(c.source_id for c in chunks))} sources")
    embedder = Embedder(cache_dir=CACHE)
    emb = embedder.passages([c.text for c in chunks])
    save_corpus(chunks, emb, OUT)
    manifest = {
        "embedding_model": EMBED_MODEL,
        "dimensions": int(emb.shape[1]),
        "chunks": len(chunks),
        "per_source": dict(Counter(c.source_id for c in chunks)),
        "inputs": {str(PDF.relative_to(ROOT)).replace("\\", "/"): sha(PDF),
                   **{rel: sha(ROOT / rel) for rel in DOCS if (ROOT / rel).exists()}},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["per_source"], indent=2))
    print(f"done in {time.time() - t0:.1f}s -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
