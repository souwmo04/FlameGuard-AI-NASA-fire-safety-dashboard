# FlameGuard AI — API

FastAPI service over the `flameguard` science library (`../src/flameguard`). The API holds no ML logic of
its own: it validates requests, calls the tested library and returns typed JSON.

## Run

From the repository root, with the virtual environment active:

```bash
pip install -r requirements.txt   # full dev environment (includes backend/requirements.txt)
pip install -e .                  # the flameguard library
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

- Interactive docs: http://localhost:8000/docs (OpenAPI JSON at `/openapi.json`)
- Tests: `python -m pytest backend/tests`

| Environment variable | Default | Purpose |
|---|---|---|
| `FLAMEGUARD_ROOT` | repository root | folder containing `data/`, `models/`, `reports/` |
| `FLAMEGUARD_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | browser origins allowed to call the API |

Data, model and reports are loaded once at startup (about 0.1 s); typical requests take 1–40 ms.

## Provenance

Every response says what kind of number it carries:

| Value | Meaning |
|---|---|
| `observed` | measured on the ISS in NASA FLEX |
| `prediction` | output of the trained model |
| `estimate` | statistical summary fitted to observed tests (no ML model) |
| `explanation` | Shapley attribution of a prediction |
| `interpretation` | plain-language text filled from model outputs by a fixed template (no language model) |
| `hypothetical` | conditions chosen by the user |
| `evaluation` | cross-validated model performance |

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | status, model, training-data checksum |
| GET | `/api/stats` | real dataset counts and cross-validated headline metrics |
| GET | `/api/sources` | NASA dataset and report behind the data (DOI, licence, citation) |
| GET | `/api/domain` | tested input ranges per fuel (for UI controls) |
| GET | `/api/model` | model card: metrics with intervals, calibration bins, risk bands, subgroups, importance |
| GET | `/api/experiments` | observed tests; filters `fuel`, `suppressant`, `pressure_level`, `outcome`, `in_model_scope`, `oxygen_min/max`, `search`, `sort`, `limit`, `offset` |
| GET | `/api/experiments/{test_id}` | one test with notes, source and out-of-fold prediction |
| POST | `/api/predict` | Fire Risk, probabilities, evidence (domain check, band's observed rate, nearest tests), Shapley contributions, interpretation |
| POST | `/api/what-if` | scenarios A and B, one-at-a-time path, optional oxygen or droplet-size sweep |
| GET | `/api/ranking?by=risk\|lowest_risk\|extinction\|burn_time` | ranked tests (out-of-fold predictions, or observed burn time) |
| GET | `/api/ranking/conditions` | tested atmospheres ranked by observed sustained rate (Wilson intervals) |
| GET | `/api/suppressants` | observed series, O₂₅₀ estimates, comparisons and the data-driven conclusion |
| POST | `/api/similar-experiments` | nearest tested conditions with similarity scores |

### Conditions (request body for `/api/predict`, `/api/similar-experiments`, both scenarios of `/api/what-if`)

```json
{
  "fuel": "Methanol",
  "oxygen_percent": 21,
  "suppressant": "CO2",
  "suppressant_percent": 10,
  "droplet_diameter_mm": 3.0
}
```

`fuel`: `Methanol` | `Heptane`; `suppressant`: `none` | `CO2` | `He`. These are exactly the model's inputs.
Pressure, temperature and airflow are **not** inputs: FLEX burned droplets in a quiescent chamber at ambient
temperature, and pressure was dropped from the model (decision D-001; predictions apply to 0.7–1 atm).
Values outside the tested region are accepted but flagged in `evidence` as extrapolations.

## Layout

```
backend/
├── app/
│   ├── main.py          app factory: CORS, gzip, startup loading, /api router
│   ├── config.py        settings from environment variables
│   ├── state.py         data/model/reports loaded once; get_state dependency
│   ├── schemas/         Pydantic request/response models (common.py, responses.py)
│   ├── services/        translate library results into responses
│   └── api/             routers: system, experiments, predictions, analysis
└── tests/test_api.py    HTTP-level tests against the real data and model
```
