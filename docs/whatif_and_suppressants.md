# What-if analysis and suppressant comparison (Phase 12)

## What-if analysis (`src/flameguard/whatif.py`, dashboard page *What-if Analysis*)

**Provenance: hypothetical scenario + model prediction.**

- Two scenarios, A (baseline) and B (changed), each set within the per-fuel tested ranges.
- **Step-by-step path:** inputs change one at a time in a fixed order (oxygen → suppressant → droplet size →
  fuel); each intermediate state is predicted and checked against the applicability domain. Step sizes depend on
  the order because fuel and droplet size interact; the total change does not.
- **Sensitivity curves:** Fire Risk as oxygen or droplet size varies across the tested range, other inputs fixed;
  points far from any tested condition are drawn hollow.
- Example (final model): methanol, 3 mm, O₂ 0.21 → Fire Risk 28.7; O₂ 0.18 → 8.8 (−19.9); then +10% CO₂ → 6.2 (−2.6).
- **Caveat shown on the page whenever the suppressant changes:** FLEX lowered O₂ while adding CO₂/He, so the model
  cannot isolate a suppressant effect (Phase 8 ablation: suppressant inputs add no measurable skill).

## Suppressant comparison (`src/flameguard/suppressant.py`, page *Suppressant Comparison*)

**Provenance: observed NASA tests + statistical estimate. No machine-learning model is used.**

For each FLEX series (fuel × pressure × diluent), **O₂₅₀** = the O₂ mole fraction at which half of 3 mm droplets
kept burning, from a logistic fit `P(sustained) = logistic(b0 + b1·O₂[%] + b2·(d0 − 3 mm))` on that series only
(weak L2 penalty, C = 10). 95% intervals: 1000 percentile-bootstrap resamples of the tested atmospheres within the
series. A series is reported only if it has ≥ 3 sustained and ≥ 3 extinguished tests, the estimate lies inside the
series' tested O₂ range, and ≥ 80% of bootstrap refits are valid.

Results (`reports/phase12/o2_50_by_series.csv`): 6 of 12 series estimable.

| Series | O₂₅₀ | 95% CI |
|---|---|---|
| Heptane · 0.7 atm · CO₂ | 0.236 | 0.228–0.241 |
| Heptane · 1 atm · N₂ only | 0.195 | 0.191–0.217 |
| Heptane · 1 atm · CO₂ | 0.218 | 0.206–0.235 |
| Heptane · 1 atm · He | 0.209 | 0.179–0.352 (beyond tested range) |
| Methanol · 0.7 atm · CO₂ | 0.236 | 0.219–0.279 (beyond tested range) |
| Methanol · 1 atm · N₂ only | 0.280 | 0.217–0.299 |

**Conclusion:** only heptane at 1 atm allows a comparison across suppressants. CO₂-diluted atmospheres needed
somewhat more oxygen than N₂-only ones, but the intervals overlap and helium is too uncertain to place. **The data
do not establish a ranking of the suppressants.**

**Not NASA's LOI.** NASA's limiting oxygen index is the O₂ level below which quasi-steady burning is not observed;
O₂₅₀ asks whether the flame survived until its fuel was gone. Series also differ in test days, droplet sizes and in
how the suppressant fraction moved with O₂. SF₆ is named in FLEX's objectives but has no tests in this dataset.
