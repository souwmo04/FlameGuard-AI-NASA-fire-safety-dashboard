"""Phase 9: the deployable final model — Fire Risk Score, risk bands, applicability domain.

A FinalModel bundles
  * the fitted pipeline (logistic regression without pressure, decision D-001),
  * RiskBands derived from cross-validated (out-of-fold) predictions,
  * an ApplicabilityDomain describing where predictions are interpolations,
  * metadata (data checksum, library versions, validation metrics).

Every prediction is returned with an explicit label that it is a MODEL PREDICTION,
plus domain warnings. Nothing here produces or alters experimental results.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from flameguard.data_loader import PROJECT_ROOT

MODEL_DIR = PROJECT_ROOT / "models"
BUNDLE_PATH = MODEL_DIR / "final_model.joblib"
CARD_PATH = MODEL_DIR / "final_model.json"

DOMAIN_FEATURES = ["x_o2", "x_co2", "x_he", "d0_mm"]
SUPPORTED_FUELS = ("Methanol", "Heptane")
PREDICTION_LABEL = "Model prediction (logistic regression trained on NASA FLEX data) - not an experimental result"


@dataclass
class RiskBands:
    """Fire Risk Score bands. `alert_threshold` is the probability at which the model catches
    >= target_recall of sustained-combustion tests in cross-validation."""

    alert_threshold: float
    high_threshold: float = 0.5
    target_recall: float = 0.90
    band_stats: dict = field(default_factory=dict)  # observed outcomes per band in out-of-fold data

    def band(self, p: float) -> str:
        if p >= self.high_threshold:
            return "HIGH"
        if p >= self.alert_threshold:
            return "ELEVATED"
        return "LOW"


@dataclass
class ApplicabilityDomain:
    """Where the training data supports a prediction.

    Two checks per fuel:
      range   - each input inside the min/max tested for that fuel;
      support - the query's distance to the nearest tested condition (standardised
                O2, CO2, He, d0) is no larger than the typical gap between distinct
                tested atmospheres (95th percentile of each test's distance to the
                nearest test from a DIFFERENT atmosphere group).
    The second check catches combinations inside every range but never tested together,
    e.g. low O2 with low suppressant where only the O2/suppressant diagonal was run.
    """

    ranges: dict
    scale: dict
    points: dict
    support_radius: dict

    @classmethod
    def fit(cls, X: pd.DataFrame, groups: pd.Series, quantile: float = 0.95) -> "ApplicabilityDomain":
        # a constant feature (sd 0) would make every distance NaN; give it unit scale instead
        scale = {c: float(X[c].std()) or 1.0 for c in DOMAIN_FEATURES}
        ranges, points, radius = {}, {}, {}
        for fuel in SUPPORTED_FUELS:
            sub = X[X["fuel"] == fuel]
            g = groups[X["fuel"] == fuel].to_numpy()
            Z = cls._standardise(sub, scale)
            ranges[fuel] = {c: [float(sub[c].min()), float(sub[c].max())] for c in DOMAIN_FEATURES}
            d = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1))
            d[g[:, None] == g[None, :]] = np.inf  # same atmosphere = near-duplicate, not "support"
            gaps = d.min(axis=1)
            gaps = gaps[np.isfinite(gaps)]
            # With a single tested atmosphere there is no "typical gap": treat everything as unsupported.
            radius[fuel] = float(np.quantile(gaps, quantile)) if gaps.size else 0.0
            points[fuel] = Z.tolist()
        return cls(ranges=ranges, scale=scale, points=points, support_radius=radius)

    @staticmethod
    def _standardise(frame: pd.DataFrame, scale: dict) -> np.ndarray:
        return np.column_stack([frame[c].to_numpy(dtype=float) / scale[c] for c in DOMAIN_FEATURES])

    def check(self, row: pd.Series) -> dict:
        fuel = row["fuel"]
        if fuel not in self.ranges:
            return {"in_range": False, "supported": False, "nearest_distance": np.nan,
                    "warnings": [f"Fuel {fuel!r} was not tested in FLEX; no prediction is valid."]}
        warnings = []
        for c, (lo, hi) in self.ranges[fuel].items():
            v = float(row[c])
            if v < lo - 1e-9 or v > hi + 1e-9:
                warnings.append(f"{c} = {v:g} is outside the tested range for {fuel} ({lo:g}-{hi:g}).")
        z = self._standardise(row.to_frame().T, self.scale)[0]
        dist = float(np.sqrt(((np.asarray(self.points[fuel]) - z) ** 2).sum(1)).min())
        supported = dist <= self.support_radius[fuel]
        if not supported:
            warnings.append("This combination of oxygen, suppressant and droplet size is far from any tested "
                            "FLEX condition; the prediction is an extrapolation and may be badly calibrated.")
        return {"in_range": not any("outside the tested range" in w for w in warnings), "supported": supported,
                "nearest_distance": dist, "warnings": warnings}


@dataclass
class FinalModel:
    pipeline: object
    bands: RiskBands
    domain: ApplicabilityDomain
    metadata: dict

    # --- persistence -------------------------------------------------------------
    def save(self, bundle_path: Path = BUNDLE_PATH, card_path: Path = CARD_PATH) -> None:
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, bundle_path)
        card = {"metadata": self.metadata, "bands": asdict(self.bands),
                "domain": {"ranges": self.domain.ranges, "support_radius": self.domain.support_radius}}
        card_path.write_text(json.dumps(card, indent=2, default=float) + "\n", encoding="utf-8")

    @staticmethod
    def load(bundle_path: Path = BUNDLE_PATH) -> "FinalModel":
        return joblib.load(bundle_path)

    # --- prediction ----------------------------------------------------------------
    def predict(self, inputs: pd.DataFrame) -> pd.DataFrame:
        """inputs: columns fuel, x_o2, x_co2, x_he, d0_mm (pressure is not a model input)."""
        missing = {"fuel", *DOMAIN_FEATURES} - set(inputs.columns)
        if missing:
            raise ValueError(f"Missing inputs: {sorted(missing)}")
        X = inputs.copy()
        if "pressure_atm" not in X:
            X["pressure_atm"] = np.nan  # placeholder column; the final pipeline does not read it
        p = self.pipeline.predict_proba(X)[:, 1]
        rows = []
        for (_, row), prob in zip(X.iterrows(), p):
            dom = self.domain.check(row)
            rows.append({
                "p_sustained": float(prob),
                "p_extinction": float(1 - prob),
                "fire_risk": round(100 * float(prob), 1),
                "risk_band": self.bands.band(prob),
                "in_tested_range": dom["in_range"],
                "supported_by_data": dom["supported"],
                "nearest_tested_distance": dom["nearest_distance"],
                "warnings": dom["warnings"],
                "label": PREDICTION_LABEL,
            })
        return pd.DataFrame(rows, index=inputs.index)
