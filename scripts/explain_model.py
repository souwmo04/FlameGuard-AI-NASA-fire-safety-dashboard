"""Phase 10: SHAP explanations of the final model for all 252 training tests.

Writes to reports/phase10/:
  shap_grouped.csv, shap_detailed.csv,  per-test contributions (Fire Risk points), columns
  shap_detailed_symmetric.csv           prefixed "phi:"; fuel-first except *_symmetric
  global_importance.csv                 mean |contribution| per player, both groupings
  examples.csv                          four illustrative tests with plain-language summaries

Background distribution = the 252 primary training tests.

Usage:  .venv/Scripts/python scripts/explain_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from flameguard import explainability as ex  # noqa: E402
from flameguard.dataset import build_modeling_data  # noqa: E402
from flameguard.prediction import FinalModel  # noqa: E402

OUT = ROOT / "reports" / "phase10"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    data = build_modeling_data(master, "primary")
    model = FinalModel.load()
    X = data.X.drop(columns="pressure_atm")
    ids = data.meta[["test_id", "flex_identifier", "diluent", "outcome_raw"]].reset_index(drop=True)

    grouped = ex.explain(model, X, X, "grouped")
    detailed = ex.explain(model, X, X, "detailed")
    symmetric = ex.explain(model, X, X, "detailed_symmetric")
    for name, frame in [("grouped", grouped), ("detailed", detailed), ("detailed_symmetric", symmetric)]:
        additivity = (frame.drop(columns=["base", "fire_risk"]).sum(axis=1) + frame["base"] - frame["fire_risk"]).abs()
        assert additivity.max() < 1e-8, name
        contrib = frame.reset_index(drop=True).rename(
            columns={c: f"phi: {c}" for c in frame.columns if c not in {"base", "fire_risk"}})
        pd.concat([ids, X.reset_index(drop=True), contrib], axis=1).to_csv(
            OUT / f"shap_{name}.csv", index=False)

    imp = pd.concat([ex.global_importance(grouped).assign(grouping="grouped"),
                     ex.global_importance(detailed).assign(grouping="detailed"),
                     ex.global_importance(symmetric).assign(grouping="detailed_symmetric")])
    imp.rename_axis("player").to_csv(OUT / "global_importance.csv")

    # Illustrative tests: chosen by rule, not hand-picked for flattering results.
    risk = grouped["fire_risk"]
    band = risk.map(lambda r: model.bands.band(r / 100))
    picks = {
        "highest-risk test": risk.idxmax(),
        "typical ELEVATED test": (risk[band == "ELEVATED"] - risk[band == "ELEVATED"].median()).abs().idxmin(),
        "typical LOW test": (risk[band == "LOW"] - risk[band == "LOW"].median()).abs().idxmin(),
        "missed fire (test 151: LOW prediction, but it burned to completion)":
            ids.index[ids["test_id"] == 151][0],
    }
    rows = []
    for label, i in picks.items():
        g = grouped.loc[i]
        rows.append({"example": label, **ids.loc[i].to_dict(), **X.loc[i].to_dict(),
                     **{(k if k in {"base", "fire_risk"} else f"phi: {k}"): v for k, v in g.to_dict().items()},
                     "band": band.loc[i], "summary": ex.describe(g, band.loc[i], X.loc[i])})
    pd.DataFrame(rows).to_csv(OUT / "examples.csv", index=False)

    print(imp.round(3).to_string())
    for r in rows:
        print(f"\n[{r['example']}] test {r['test_id']} ({r['outcome_raw']} observed)\n  {r['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
