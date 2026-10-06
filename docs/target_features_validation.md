# Target, features and validation design (Phases 5–6)

Fixed **before** any model is trained. Executed evidence: `notebooks/02_target_features_validation.ipynb`.
Code: `src/flameguard/dataset.py`, `features.py`, `validation.py`; tests in `tests/test_features_validation.py`.

## Target (Phase 5)

`y_sustained` = 1 if the NASA `Test end` is **Completion** or **Disruption**, 0 if **Extinction**.
Disruption counts as sustained because the flame had not self-extinguished while fuel remained when the droplet
broke up. This is a judgement call, tested by the `exclude_disruption` variant.

| Variant | Tests | Sustained | Groups | Purpose |
|---|---|---|---|---|
| `primary` | 252 | 80 | 44 | main model |
| `exclude_disruption` | 199 | 27 | 43 | sensitivity: Disruption tests removed |
| `impute_d0` | 264 | 86 | 44 | sensitivity: missing d₀ imputed inside each training fold |

Primary exclusions (22 tests, each listed with its reason by `ModelingData.excluded`): 9 at 2–3 atm (a single CO₂
series, pressure and CO₂ inseparable), 12 without initial droplet diameter, 1 with invalid pressure.

**Fire Risk Score:** `100 × P(sustained)` from calibrated, cross-validated probabilities — the estimated chance that a
burning fuel droplet in a given atmosphere keeps burning instead of self-extinguishing, *within FLEX test
conditions*. Risk-level bands are set in Phase 9 from the validated operating threshold.

## Features (Phase 6)

Inputs (all known before ignition): `is_heptane`, `x_o2`, `x_co2`, `x_he`, `pressure_atm`, `d0_mm`;
linear models add `heptane_x_d0` (the droplet-size effect has opposite signs for the two fuels).

| Excluded | Reason | Evidence |
|---|---|---|
| `x_n2` | mole fractions sum to 1 | VIF > 1000 when added |
| `p_o2_atm` | = x_o2 × pressure (kept as `with_po2` ablation) | VIF ≈ 50–58 when added |
| `diluent` | implied by x_co2 / x_he | – |
| `d_ext_mm`, `burn_rate_mm2_s`, `burn_time_s` | measured after ignition (label leakage) | – |

Chosen set VIFs: all ≤ 2.3. All fitted preprocessing (scaling, interaction centring, imputation) runs inside an
sklearn `Pipeline` on the training fold only. XGBoost gets one monotone constraint: more O₂ never lowers
P(sustained). Suppressant signs are left free because O₂ and suppressant were varied together.

## Validation (Phase 6)

- **Primary:** 5 × repeated 5-fold `StratifiedGroupKFold` on `group_id_atmosphere` (25 splits). Automatically
  checked: no group in both train and test, no row overlap, both classes in every test fold, each repeat partitions
  the data. Test folds: 44–69 tests, 7–11 groups, 28–39% sustained.
- **Stress tests:** leave out all CO₂ tests (111) or all He tests (47); train on 1 atm and test on 0.7 atm, and the
  reverse. With He left out, training contains no helium, so that split measures degradation on an untested
  suppressant, not a fair score.

## Evaluation plan

- Safety: recall on sustained and false-negative rate (a false negative = predicted to self-extinguish but kept
  burning), alongside ROC-AUC, PR-AUC, F1, precision, accuracy, confusion matrix.
- Calibration: Brier score and reliability curve.
- Operating threshold chosen inside training folds for recall ≥ 0.90; report the precision it costs.
- Baselines: majority class and O₂-only logistic regression. Report mean ± sd over the 25 folds plus pooled
  out-of-fold metrics.
