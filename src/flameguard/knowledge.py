"""Phase 13: the knowledge base behind "Ask FlameGuard" (retrieval-augmented answers).

The corpus is:
  * NASA/TP-2015-216046 (Dietrich et al., FLEX results 2009-2011; NTRS 20150023456, public use
    permitted, no third-party material), split per page so answers can cite page numbers;
  * this project's own documentation (data card, model card, decisions, findings), split per section.

The large data-table appendix of the report is skipped: those rows are the dataset itself and are
served exactly by the API, not paraphrased by a language model.

Retrieval is hybrid: dense embeddings (BAAI/bge-small-en-v1.5 via fastembed/ONNX, no PyTorch) for
meaning plus TF-IDF for exact terms (test identifiers, "O2_50", chemical names). With a few hundred
chunks exact cosine search in numpy is instant, so no vector database is needed.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
REPO_URL = "https://github.com/souwmo04/FlameGuard-AI-NASA-fire-safety-dashboard/blob/main"
REPORT_ID = "nasa-tp-2015-216046"
REPORT_TITLE = "NASA/TP-2015-216046 — Detailed Results From the Flame Extinguishment Experiment (FLEX), March 2009 to December 2011"
REPORT_URL = "https://ntrs.nasa.gov/citations/20150023456"
REPORT_PDF_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf"

CHUNK_WORDS = 220
OVERLAP_WORDS = 40
DENSE_WEIGHT = 0.65  # remaining weight goes to TF-IDF

DOCS = {  # file -> short title shown in citations
    "README.md": "FlameGuard README",
    "docs/data_card.md": "FlameGuard data card",
    "docs/eda_findings.md": "FlameGuard exploratory findings",
    "docs/target_features_validation.md": "FlameGuard target, features and validation",
    "docs/decisions.md": "FlameGuard decision log",
    "docs/model_card.md": "FlameGuard model card",
    "docs/whatif_and_suppressants.md": "FlameGuard what-if and suppressant analysis",
    "docs/ask_flameguard.md": "Ask FlameGuard: sources and method",
}


@dataclass(frozen=True)
class Chunk:
    id: str
    source_id: str
    source_title: str
    location: str      # "p. 25" or a section heading
    section: str
    text: str
    url: str


# --- chunking ----------------------------------------------------------------------------


def _split_words(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [" ".join(words)] if words else []
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(1, len(words) - overlap), step)]


def _clean_pdf_text(text: str) -> str:
    text = text.replace("�", "-").replace(" ", " ")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)           # words hyphenated across lines
    text = re.sub(r"[ \t]+", " ", text)
    # "FLEX −094", "FLEX –130" -> "FLEX-094", so test references match the way users type them
    text = re.sub(r"FLEX\s*[−–—-]\s*(\d+)", r"FLEX-\1", text)
    return text


TEST_REF = re.compile(r"\b(?:FLEX[\s−–-]*|test\s+(?:no\.?\s*|number\s+|#\s*)?)(\d{1,3})\b", re.IGNORECASE)


def referenced_tests(text: str) -> list[int]:
    """Test numbers mentioned in a question ("FLEX-094", "test 94", "test #94")."""
    return sorted({int(m.group(1)) for m in TEST_REF.finditer(text) if 0 < int(m.group(1)) < 1000})


_PAGE_NO = re.compile(r"NASA/TP\W+2015-216046\s+([ivxlcdm]+|\d+)\b", re.IGNORECASE)
_HEADING = re.compile(r"^\s*((?:\d+|[A-Z])\.\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,90})$")
_APPENDIX = re.compile(r"^\s*(Appendix [A-Z])\W+(.{3,80})$")
_FIGURE_TEST = re.compile(r"Figure \d+\.\W+Test FLEX\W*(\d+)")


def _is_table_page(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    flex_rows = sum(1 for ln in lines if re.match(r"\s*FLEX\W\d+", ln))
    return bool(lines) and flex_rows / len(lines) > 0.25


def chunks_from_report(pdf_path: Path) -> list[Chunk]:
    """Chunk the NASA report page by page, keeping the printed page number and current section."""
    from pypdf import PdfReader  # only needed when (re)building the corpus

    chunks: list[Chunk] = []
    section = "Front matter"
    for index, page in enumerate(PdfReader(str(pdf_path)).pages):
        raw = page.extract_text() or ""
        if len(raw.split()) < 40 or raw.count(".....") > 5 or _is_table_page(raw):
            continue  # figures, table of contents, data-table appendix
        match = _PAGE_NO.search(raw[:200])
        # printed page numbers where the page has one; cover pages are labelled by PDF page instead
        location = f"p. {match.group(1)}" if match else f"PDF p. {index + 1}"
        body = _PAGE_NO.sub("", _clean_pdf_text(raw), count=1)
        figure = _FIGURE_TEST.search(body[:300])
        if figure:  # Appendix A: one page of images and observations per test
            page_section = f"Appendix A — Test FLEX-{int(figure.group(1)):03d}"
        else:
            for line in body.splitlines():
                h = _HEADING.match(line) or _APPENDIX.match(line)
                if h and "..." not in line:
                    section = f"{h.group(1)} {h.group(2).strip()}"
                    break
                if line.strip() == "References":
                    section = "References"
                    break
            if section == "References":
                continue  # a bibliography, not findings
            page_section = section
        for j, piece in enumerate(_split_words(body)):
            chunks.append(Chunk(id=f"{REPORT_ID}-p{index + 1}-{j}", source_id=REPORT_ID, source_title=REPORT_TITLE,
                                location=location, section=page_section, text=piece,
                                url=f"{REPORT_PDF_URL}#page={index + 1}"))
    return chunks


def _slug(heading: str) -> str:
    """GitHub-style heading anchor."""
    s = re.sub(r"[^\w\- ]", "", heading.lower()).strip()
    return re.sub(r" ", "-", s)


def chunks_from_markdown(path: Path, rel: str, title: str) -> list[Chunk]:
    """Chunk a markdown document by headings; long sections are split with overlap."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)        # code blocks are not prose
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)               # images
    sections: list[tuple[str, list[str]]] = [("Introduction", [])]
    for line in text.splitlines():
        h = re.match(r"^#{1,4}\s+(.*)", line)
        if h:
            sections.append((h.group(1).strip(), []))
        else:
            sections[-1][1].append(line)
    chunks = []
    doc_id = Path(rel).stem
    for k, (heading, lines) in enumerate(sections):
        body = re.sub(r"\s+", " ", " ".join(lines)).strip()
        if len(body.split()) < 12:
            continue
        anchor = "" if heading == "Introduction" else f"#{_slug(heading)}"
        for j, piece in enumerate(_split_words(body)):
            chunks.append(Chunk(id=f"{doc_id}-{k}-{j}", source_id=doc_id, source_title=title, location=heading,
                                section=heading, text=f"{heading}: {piece}", url=f"{REPO_URL}/{rel}{anchor}"))
    return chunks


def build_corpus(root: Path, report_pdf: Path | None) -> list[Chunk]:
    chunks: list[Chunk] = []
    if report_pdf is not None and report_pdf.exists():
        chunks += chunks_from_report(report_pdf)
    for rel, title in DOCS.items():
        p = root / rel
        if p.exists():
            chunks += chunks_from_markdown(p, rel, title)
    return chunks


# --- index ---------------------------------------------------------------------------------


def _normalise(m: np.ndarray) -> np.ndarray:
    return m / np.clip(np.linalg.norm(m, axis=1, keepdims=True), 1e-12, None)


class Embedder:
    """Thin wrapper around fastembed so the model is loaded once and can be swapped in tests."""

    def __init__(self, cache_dir: Path | None = None, model: str = EMBED_MODEL):
        from fastembed import TextEmbedding

        self.model_name = model
        self._model = TextEmbedding(model_name=model, cache_dir=str(cache_dir) if cache_dir else None)

    def passages(self, texts: list[str]) -> np.ndarray:
        return _normalise(np.array(list(self._model.passage_embed(texts)), dtype=np.float32))

    def query(self, text: str) -> np.ndarray:
        return _normalise(np.array(list(self._model.query_embed([text])), dtype=np.float32))[0]


def save_corpus(chunks: list[Chunk], embeddings: np.ndarray, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    np.save(directory / "embeddings.npy", embeddings.astype(np.float16))  # small enough to commit


def load_corpus(directory: Path) -> tuple[list[Chunk], np.ndarray]:
    lines = (directory / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    chunks = [Chunk(**json.loads(line)) for line in lines if line.strip()]
    emb = np.load(directory / "embeddings.npy").astype(np.float32)
    if len(chunks) != len(emb):
        raise ValueError("chunks.jsonl and embeddings.npy are out of sync; rebuild with scripts/build_knowledge.py")
    return chunks, _normalise(emb)


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class KnowledgeIndex:
    """Hybrid dense + TF-IDF search over a fixed set of chunks."""

    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray, embedder: Embedder | None):
        self.chunks = list(chunks)
        self.embeddings = _normalise(np.asarray(embeddings, dtype=np.float32))
        self.embedder = embedder
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, stop_words="english")
        self.tfidf_matrix = self.tfidf.fit_transform([c.text for c in self.chunks])

    def add(self, extra: list[Chunk]) -> "KnowledgeIndex":
        """A new index with extra chunks (e.g. live data facts built at startup)."""
        if not extra:
            return self
        emb = self.embedder.passages([c.text for c in extra]) if self.embedder else np.zeros((len(extra), self.embeddings.shape[1]))
        return KnowledgeIndex(self.chunks + list(extra), np.vstack([self.embeddings, emb]), self.embedder)

    def search(self, query: str, k: int = 6, min_score: float = 0.33) -> list[Hit]:
        sparse = (self.tfidf_matrix @ self.tfidf.transform([query]).T).toarray().ravel()
        if self.embedder is not None:
            dense = self.embeddings @ self.embedder.query(query)
            score = DENSE_WEIGHT * np.clip(dense, 0, 1) + (1 - DENSE_WEIGHT) * sparse
        else:
            score = sparse
        tests = referenced_tests(query)
        if tests:  # a question about a specific test should reach that test's appendix page
            wanted = tuple(f"FLEX-{t:03d}" for t in tests)
            score = score + np.array([0.3 if c.section.endswith(wanted) else 0.0 for c in self.chunks])
        order = np.argsort(-score)
        hits: list[Hit] = []
        per_source: dict[str, int] = {}
        for i in order:
            if score[i] < min_score or len(hits) >= k:
                break
            c = self.chunks[i]
            # keep the answer grounded in more than one place: at most 3 chunks per source document
            if per_source.get(c.source_id, 0) >= 3:
                continue
            per_source[c.source_id] = per_source.get(c.source_id, 0) + 1
            hits.append(Hit(chunk=c, score=float(score[i])))
        return hits
