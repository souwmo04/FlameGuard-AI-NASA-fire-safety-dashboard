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
