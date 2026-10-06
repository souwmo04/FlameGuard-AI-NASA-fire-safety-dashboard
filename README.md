# FlameGuard AI

AI-powered fire safety intelligence from NASA microgravity combustion experiments.
Built for the NASA Space Apps Challenge 2026 — *Flame in Freefall*.

> Research prototype. Not a certified spacecraft fire-safety system. Every number is labelled as an
> observed NASA result, a model prediction, a statistical estimate, an explanation, or a hypothetical scenario.

## Architecture

```
Next.js frontend (UI, charts, motion)  ──REST──▶  FastAPI backend (backend/)  ──▶  flameguard library (src/)
                                                                                 data · model · SHAP · what-if
```

The frontend contains no ML logic; the API contains no science of its own — it calls the tested library.

## Data

| Program | Source | Used for |
|---|---|---|
| FLEX (ISS droplet combustion, 274 tests) | NASA PSI, [PSI-69](https://psi.nasa.gov/physci/repo/data/investigations/PSI-69), DOI [10.60555/mbq8-0451](https://doi.org/10.60555/mbq8-0451), CC0-1.0 | MVP model |

Details and known data issues: [docs/data_card.md](docs/data_card.md).

## Progress

| Phase | Output |
|---|---|
| Data discovery, download, cleaning | `data/processed/combustion_master.csv`, [data card](docs/data_card.md) |
| EDA | [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb), [findings](docs/eda_findings.md) |
| Target, features, validation design | [notebooks/02_target_features_validation.ipynb](notebooks/02_target_features_validation.ipynb), [design](docs/target_features_validation.md) |
| Baseline models | [notebooks/03_baseline_models.ipynb](notebooks/03_baseline_models.ipynb), `reports/phase7/` |
| Tuning, ablation, sensitivity, stress tests | [notebooks/04_tuning_ablation_stress.ipynb](notebooks/04_tuning_ablation_stress.ipynb), `reports/phase8/`, [decision log](docs/decisions.md) |
| Final evaluation, risk bands, deployable model | [notebooks/05_final_evaluation.ipynb](notebooks/05_final_evaluation.ipynb), [model card](docs/model_card.md), `models/final_model.joblib` |
| Explainable AI (SHAP) | [notebooks/06_explainability_shap.ipynb](notebooks/06_explainability_shap.ipynb), `reports/phase10/` |
| What-if and suppressant analysis | `src/flameguard/whatif.py`, `src/flameguard/suppressant.py`, [method and results](docs/whatif_and_suppressants.md), `reports/phase12/` |
| **FastAPI backend** | [backend/](backend/README.md) — 13 endpoints, Pydantic schemas, provenance on every response |
| Next.js frontend | next |

**Final model (selected by a pre-registered rule):** L2 logistic regression on fuel, O₂, CO₂, He, initial droplet
diameter and a fuel × droplet-size term; pressure was dropped (decision D-001). Cross-validated over 25 grouped folds:
log loss 0.336, Brier 0.103, ROC-AUC 0.925, PR-AUC 0.877; at the recall-0.90 operating point, precision 0.625.
These are model predictions on held-out FLEX tests, not experimental results. Valid only for methanol/n-heptane
droplets at 0.7–1 atm within the tested O₂/suppressant ranges.

**Fire Risk Score** = 100 × P(sustained), calibrated (slope 0.90–1.02). Bands from out-of-fold predictions:
LOW < 18.4 (6% of tests kept burning), ELEVATED 18.4–50 (28%), HIGH ≥ 50 (87%). Every prediction is checked
against the tested conditions and flagged when it is an extrapolation. Full details: [model card](docs/model_card.md).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
pip install -e .                   # the flameguard library (used by the API)
python -m uvicorn app.main:app --app-dir backend --reload --port 8000   # API + docs at http://localhost:8000/docs
python -m pytest                   # library + API tests
```

Rebuild the pipeline from the raw NASA data (outputs are already committed):

```bash
python scripts/download_flex.py        # raw NASA data (~43 MB, mostly the FLEX report PDF)
python scripts/build_master.py         # clean -> data/processed/combustion_master.csv
python scripts/train_baselines.py      # cross-validated baselines -> reports/phase7/
python scripts/phase8_experiments.py   # tuning/ablation/sensitivity/stress -> reports/phase8/
python scripts/finalize_model.py       # calibration, risk bands, final model -> models/, reports/phase9/
python scripts/explain_model.py        # SHAP explanations -> reports/phase10/
python scripts/suppressant_analysis.py # O2-50 per test series -> reports/phase12/
```

## Layout

```
backend/            FastAPI service (see backend/README.md)
src/flameguard/     science library: loading, cleaning, features, models, evaluation, explainability,
                    prediction, what-if, suppressant analysis, similarity
data/raw/flex/      raw NASA files + MANIFEST.json (never edited)
data/processed/     combustion_master.csv (model-ready)
documents/flex/     NASA reports (knowledge-base corpus)
docs/               data card, EDA findings, design, decisions, model card, figures
notebooks/          executed analysis notebooks
models/             deployable final model
reports/            cross-validation and analysis results per phase
scripts/            pipeline entry points
tests/              library tests (API tests live in backend/tests/)
```
