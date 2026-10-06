# FlameGuard AI

AI-powered fire safety intelligence from NASA microgravity combustion experiments.
Built for the NASA Space Apps Challenge 2026 — *Flame in Freefall*.

> Research prototype. Not a certified spacecraft fire-safety system. The dashboard
> labels every number as an observed NASA result, a model prediction, an AI-generated
> explanation, or a hypothetical what-if scenario.

## Data

| Program | Source | Used for |
|---|---|---|
| FLEX (ISS droplet combustion, 274 tests) | NASA PSI, [PSI-69](https://psi.nasa.gov/physci/repo/data/investigations/PSI-69), DOI [10.60555/mbq8-0451](https://doi.org/10.60555/mbq8-0451), CC0-1.0 | MVP model |

Details and known data issues: [docs/data_card.md](docs/data_card.md).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/download_flex.py # fetch raw NASA data (~43 MB, mostly the FLEX report PDF)
python scripts/build_master.py  # clean -> data/processed/combustion_master.csv
python -m pytest                # run tests
```

## Layout

```
data/raw/flex/      raw NASA files + MANIFEST.json (never edited)
data/interim/       intermediate outputs
data/processed/     combustion_master.csv (model-ready)
documents/flex/     NASA reports (RAG corpus)
docs/               data card, EDA findings, figures, model card
notebooks/          exploration
src/flameguard/     package: loading, cleaning, features, models, explainability, RAG
dashboard/          Streamlit app
models/             trained model artifacts
scripts/            data download and pipeline entry points
tests/              unit tests
```
