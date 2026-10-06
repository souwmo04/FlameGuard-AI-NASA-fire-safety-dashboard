# EDA findings — FLEX (PSI-69)

Source: `notebooks/01_eda.ipynb` (executed), figures in `docs/figures/`.
All statements describe **observed** NASA test results (274 tests); none are model outputs.
Rates are shares of tests with 95% Wilson intervals.

## Findings

1. **Oxygen dominates.** O₂ mole fraction alone separates outcomes with AUC ≈ 0.82 (descriptive, no
   validation split). O₂ partial pressure is weaker (≈ 0.78); pressure alone ≈ 0.51.
2. **Heptane sustains combustion more often than methanol** under every diluent
   (N₂-only: 60% [45–72%] vs 28% [18–41%]).
3. **Coverage gaps.** CO₂/He tests span O₂ ≈ 0.13–0.25 only; O₂ 0.30–0.34 exists only without added
   suppressant. All 9 tests above ~1 atm are a single CO₂ series (O₂ 0.21, CO₂ 0.70).
4. **O₂ and suppressant are near-collinear within series** (corr −0.99 for He and CO₂ at 0.7 atm, −0.93 for He at
   1 atm): suppressant was added while O₂ was removed. "Same O₂, more suppressant" is outside the tested region.
5. **Droplet-size effect depends on fuel.** Heptane: larger droplets far less often sustained (70% → 19% by
   quartile; 89% → 21% within O₂ 0.20–0.25), with extinctions replacing completions — consistent with the radiative
   extinction of large droplets documented in NASA/TP-2015-216046. Methanol: weak opposite trend (10% → 28%),
   largely explained by higher O₂ in the larger-droplet tests (22% → 32% within the O₂ band). Pooled, the two cancel.
6. **Diluent is confounded with time.** N₂ series 2009–early 2010, CO₂ mid 2010–mid 2011, all He tests late 2011.
7. **Validation groups.** `group_id_atmosphere`: 45 groups, median 5 tests, largest 29 (11%), 49% single-outcome.
   `group_id_fill`: 79 groups, median 2, largest 13.
8. **Missing d₀ (12 tests)**: 9 heptane, 6 sustained; dropping removes 7% of sustained cases, mostly in
   well-covered high-O₂ heptane conditions.

## Decisions for Phases 5–7

| Topic | Decision |
|---|---|
| Features | `fuel`, `x_o2`, `x_co2`, `x_he`, `pressure_atm`, `d0_mm`, plus `fuel × d0_mm` interaction for linear models |
| Missing d₀ | Drop for the primary model; sensitivity run with in-fold imputation + missing indicator |
| Validation | Repeated `StratifiedGroupKFold` (5 folds) on `group_id_atmosphere`; stress tests: leave-one-diluent-out, train-1 atm/test-0.7 atm |
| Scope of predictions | Bound what-if inputs to tested ranges; exclude 2–3 atm from interactive predictions; flag off-diagonal O₂/suppressant combinations as extrapolation |
| Interpretation | Read SHAP for O₂ and suppressant jointly; no causal claims about suppressants |
| Suppressant comparison | Limiting-oxygen (P(sustained) = 0.5) per fuel × diluent × pressure with bootstrap intervals, following NASA's test design |
