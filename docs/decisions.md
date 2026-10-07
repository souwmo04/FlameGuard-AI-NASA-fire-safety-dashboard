# Decision log

Decisions that change the pre-registered design (docs/target_features_validation.md) are recorded here with
their evidence, so every reported result can be traced to the design it was produced under.

## D-001 · Drop `pressure_atm` from the final model (2026-10-06)

**Decision (project owner):** the final model does not use chamber pressure as an input. Pressure still defines
the model's scope: only 0.7–1 atm tests are used, and the dashboard only accepts conditions in that range.

**Status:** post-hoc, i.e. made after seeing Phase 8 stress-test results, not part of the Phase 6 pre-registration.
Results for the original design (with pressure) remain in `reports/phase7/` and `reports/phase8/` and are not
removed.

**Evidence** (all from `reports/phase8/`):
1. *No in-distribution skill.* Removing pressure from logistic regression changed mean ROC-AUC by +0.004 and log
   loss by −0.010 over the 25 grouped folds; the reduced model was better in 11–12 of 25 folds, i.e. no
   measurable difference (`ablation_paired.csv`).
2. *Unsafe extrapolation.* FLEX ran at two pressure levels (~0.7 and ~1 atm). Inside a level, pressure varies only
   by measurement noise (training sd 0.005–0.006 atm). Trained on one level and applied to the other, the scaled
   pressure input lands ~50 standard deviations outside the training range and the logistic model's probabilities
   collapse (`stress_no_pressure.csv`):

   | Stress split | Brier with → without pressure | Mean predicted vs observed (with) | Recall at safe threshold (with → without) |
   |---|---|---|---|
   | train 1 atm → test 0.7 atm | 0.296 → 0.121 | 0.05 vs 0.38 | 0.34 → 0.90 |
   | train 0.7 atm → test 1 atm | 0.722 → 0.108 | 1.00 vs 0.28 | 1.00 (flags every test) → 0.98 |

   Ranking ability (ROC-AUC 0.90–0.93) was unaffected, so the failure is in the probabilities — exactly what the
   Fire Risk Score depends on.
3. Dropping pressure also improved calibration on the held-out-suppressant splits (Brier 0.146 → 0.120 without
   CO₂ in training, 0.167 → 0.129 without He).

**What this does not claim:** that pressure has no physical effect on droplet flammability. FLEX covers only two
closely spaced levels, so the data cannot estimate a pressure effect reliably; the model therefore makes no
statement about pressure, and predictions outside 0.7–1 atm are not offered.

**Consequence for model selection:** all final candidates (logistic regression, random forest, XGBoost; untuned and
nested-CV-tuned) were re-evaluated without pressure on the same 25 grouped splits, and the pre-registered selection
rule (lowest mean log loss; simplest model within one standard error) was applied unchanged to that set
(`final_selection.csv`).

## D-002 · Fuel-needle contamination: keep the model, show a methanol contamination check (2026-10-07)

**Finding.** NASA/TP-2015-216046 (§5.2, pp. 16–17) reports that a conformal coating on the fuel-dispensing needles
dissolved or flaked into the droplets in all tests in this dataset. NASA states that disruptive extinction of
methanol "is probably due to the presence of the contaminant". For heptane, NASA draws no conclusion, because later
clean-needle tests also disrupted. FlameGuard's target counts disruption as sustained burning.

**Evidence** (`scripts/contamination_sensitivity.py` → `reports/phase14/`; same model and 5 × 5 grouped CV):

| Variant | Tests | Sustained (methanol / heptane) | ROC-AUC | PR-AUC | Methanol PR-AUC |
|---|---|---|---|---|---|
| primary (deployed) | 252 | 80 (30 / 50) | 0.925 | 0.877 | 0.714 |
| without methanol disruptions | 230 | 58 (8 / 50) | 0.940 | 0.894 | 0.438 |
| without any disruptions | 199 | 27 (8 / 19) | 0.907 | 0.735 | 0.406 |

| Fire Risk, 3 mm droplet | primary | without methanol disruptions |
|---|---|---|
| heptane, air | 56.4 | 54.6 |
| heptane, 18% O₂ + 15% CO₂ | 14.9 | 17.3 |
| methanol, air | 28.7 | 8.4 |
| methanol, 25% O₂ | 72.9 | 33.6 |

**Reading.** Heptane conclusions are stable. Methanol scores are not: most methanol "sustained" outcomes are
disruptions, and only 8 methanol tests burned to completion, so methanol has little uncontested evidence either way.

**Decision (interim, pending the project owner).** The deployed model and its pre-registered target are unchanged.
Changing the target is the owner's call, as with D-001. For every methanol prediction, the API refits the same
model without methanol disruptions at start-up and reports that score as `evidence.contamination_check`. The
interpretation adds a "data caveat" statement, and the Fire Risk page shows both numbers. The Science page and the
data and model cards describe the issue.

**Revisit if** cleaner (post-2011) FLEX data with uncoated needles becomes available, or if the owner decides to
redefine the target.
