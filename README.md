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

## Progress

| Phase | Output |
|---|---|
| 1–3 Data discovery, download, cleaning | `data/processed/combustion_master.csv`, [data card](docs/data_card.md) |
| 4 EDA | [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb), [findings](docs/eda_findings.md) |
| 5–6 Target, features, validation design | [notebooks/02_target_features_validation.ipynb](notebooks/02_target_features_validation.ipynb), [design](docs/target_features_validation.md) |
| 7 Baseline models | [notebooks/03_baseline_models.ipynb](notebooks/03_baseline_models.ipynb), `reports/phase7/` |
| 8 Tuning, ablation, sensitivity, stress tests | [notebooks/04_tuning_ablation_stress.ipynb](notebooks/04_tuning_ablation_stress.ipynb), `reports/phase8/`, [decision log](docs/decisions.md) |
| 9 Final evaluation, risk bands, deployable model | [notebooks/05_final_evaluation.ipynb](notebooks/05_final_evaluation.ipynb), [model card](docs/model_card.md), `models/final_model.joblib` |
| 10 Explainable AI (SHAP) | [notebooks/06_explainability_shap.ipynb](notebooks/06_explainability_shap.ipynb), `reports/phase10/` |
| 11 Streamlit dashboard | `dashboard/app.py` (Home, Experiment Explorer, Fire Risk Predictor, Ranking, Model Performance, Data & Methods) |
| 12 What-if analysis, suppressant comparison | dashboard pages *What-if Analysis* and *Suppressant Comparison*, [method and results](docs/whatif_and_suppressants.md), `reports/phase12/` |

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
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/download_flex.py # fetch raw NASA data (~43 MB, mostly the FLEX report PDF)
python scripts/build_master.py  # clean -> data/processed/combustion_master.csv
python scripts/train_baselines.py  # Phase 7 cross-validated models -> reports/phase7/
python scripts/phase8_experiments.py  # Phase 8 tuning/ablation/sensitivity/stress -> reports/phase8/
python scripts/finalize_model.py   # Phase 9 calibration, risk bands, final model -> models/, reports/phase9/
python scripts/explain_model.py    # Phase 10 SHAP explanations -> reports/phase10/
python scripts/suppressant_analysis.py  # Phase 12 O2-50 per test series -> reports/phase12/
streamlit run dashboard/app.py   # open the dashboard at http://localhost:8501
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
reports/            cross-validation results per phase
scripts/            data download and pipeline entry points
tests/              unit tests
```
