"""POST /api/what-if: two hypothetical scenarios, the step-by-step path between them and a sweep."""

from __future__ import annotations

import numpy as np

from flameguard import whatif as wf

from app.schemas.common import Conditions
from app.schemas.responses import PathStep, ScenarioResult, Sweep, SweepPoint, WhatIfResponse
from app.services.experiments import risk_level
from app.state import AppState

SWEEPS = {"oxygen": ("x_o2", "Oxygen", "% O₂", 100.0), "droplet": ("d0_mm", "Initial droplet diameter", "mm", 1.0)}


def scenario(state: AppState, conditions: Conditions) -> ScenarioResult:
    res = wf.predict_one(state.model, conditions.to_inputs())
    p = float(res["p_sustained"])
    return ScenarioResult(conditions=conditions, fire_risk=round(100 * p, 1), risk_level=risk_level(state, p),
                          sustained_probability=round(p, 4), supported_by_data=bool(res["supported_by_data"]),
                          in_tested_range=bool(res["in_tested_range"]), warnings=list(res["warnings"]))


def _sweep(state: AppState, a: dict, b: dict, feature: str, n: int) -> Sweep:
    key, label, unit, scale = SWEEPS[feature]
    ranges = state.model.domain.ranges
    lo = min(ranges[a["fuel"]][key][0], ranges[b["fuel"]][key][0])
    hi = max(ranges[a["fuel"]][key][1], ranges[b["fuel"]][key][1])
    grid = np.linspace(lo, hi, n)
    sa, sb = wf.sweep(state.model, a, key, grid), wf.sweep(state.model, b, key, grid)
    points = [SweepPoint(x=round(float(x) * scale, 3), a=round(float(ra), 2), b=round(float(rb), 2),
                         a_supported=bool(oa), b_supported=bool(ob))
              for x, ra, rb, oa, ob in zip(grid, sa["fire_risk"], sb["fire_risk"], sa["supported"], sb["supported"])]
    return Sweep(feature=feature, label=label, unit=unit, points=points)


def what_if(state: AppState, a: Conditions, b: Conditions, sweep: str | None, sweep_points: int) -> WhatIfResponse:
    ia, ib = a.to_inputs(), b.to_inputs()
    ra, rb = scenario(state, a), scenario(state, b)
    path = wf.scenario_path(state.model, ia, ib)
    steps = [PathStep(step=r["step"], change=r["change"], fire_risk=round(float(r["fire_risk"]), 1),
                      delta=round(float(r["delta"]), 1), risk_level=r["risk_band"],
                      supported=bool(r["supported_by_data"] and r["in_tested_range"]))
             for _, r in path.iterrows()]
    notes = []
    if (ia["x_co2"], ia["x_he"]) != (ib["x_co2"], ib["x_he"]):
        notes.append("NASA lowered oxygen while adding CO₂ or He, so the data cannot separate the two; the model's "
                     "response to a suppressant change at fixed oxygen is weakly supported.")
    if not all(s.supported for s in steps):
        notes.append("At least one step is far from any tested FLEX condition (extrapolation).")
    notes.append("Inputs change one at a time in a fixed order (oxygen, suppressant, droplet size, fuel). Because fuel "
                 "and droplet size interact, individual step sizes depend on this order; the total change does not.")
    return WhatIfResponse(a=ra, b=rb, delta=round(rb.fire_risk - ra.fire_risk, 1), path=steps,
                          sweep=_sweep(state, ia, ib, sweep, sweep_points) if sweep else None, notes=notes)
