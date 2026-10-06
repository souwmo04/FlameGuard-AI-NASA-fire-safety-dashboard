"""Shared types. Every response states its provenance so the UI never has to guess whether a
number is a NASA measurement, a model prediction, a statistical estimate or a hypothetical."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Provenance(str, Enum):
    OBSERVED = "observed"              # measured on the ISS (NASA FLEX)
    PREDICTION = "prediction"          # output of the trained model
    ESTIMATE = "estimate"              # statistical summary fitted to observed tests (no ML model)
    EXPLANATION = "explanation"        # Shapley attribution of a model prediction
    INTERPRETATION = "interpretation"  # plain-language text generated from model outputs by a template
    HYPOTHETICAL = "hypothetical"      # conditions chosen by the user
    EVALUATION = "evaluation"          # cross-validated model performance


class Fuel(str, Enum):
    METHANOL = "Methanol"
    HEPTANE = "Heptane"


class Suppressant(str, Enum):
    NONE = "none"
    CO2 = "CO2"
    HE = "He"


class RiskLevel(str, Enum):
    LOW = "LOW"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"


class Conditions(BaseModel):
    """Conditions a user can set. These are exactly the final model's inputs; pressure, temperature
    and airflow are not inputs (FLEX: quiescent, ambient temperature; pressure dropped, decision D-001)."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "fuel": "Methanol", "oxygen_percent": 21, "suppressant": "CO2", "suppressant_percent": 10,
        "droplet_diameter_mm": 3.0}})

    fuel: Fuel
    oxygen_percent: float = Field(..., ge=0, le=100, description="O2 mole fraction in percent (air = 21).")
    suppressant: Suppressant = Field(Suppressant.NONE, description="Added diluent gas; 'none' = O2/N2 only.")
    suppressant_percent: float = Field(0.0, ge=0, le=100, description="Suppressant mole fraction in percent.")
    droplet_diameter_mm: float = Field(..., gt=0, le=10, description="Initial droplet diameter in mm.")

    @model_validator(mode="after")
    def _consistent(self) -> "Conditions":
        if self.suppressant == Suppressant.NONE and self.suppressant_percent > 0:
            raise ValueError("suppressant_percent must be 0 when suppressant is 'none'")
        if self.oxygen_percent + self.suppressant_percent > 100:
            raise ValueError("oxygen_percent + suppressant_percent cannot exceed 100")
        return self

    def to_inputs(self) -> dict:
        """Model-input dict (mole fractions)."""
        frac = self.suppressant_percent / 100
        return {
            "fuel": self.fuel.value,
            "x_o2": self.oxygen_percent / 100,
            "x_co2": frac if self.suppressant == Suppressant.CO2 else 0.0,
            "x_he": frac if self.suppressant == Suppressant.HE else 0.0,
            "d0_mm": self.droplet_diameter_mm,
        }


class SourceRef(BaseModel):
    id: str
    title: str
    url: str
    doi: str | None = None
