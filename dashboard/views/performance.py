import pandas as pd
import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge

card = data.model_card()
meta = card["metadata"]
val = meta["validation"]
fm = data.model()

st.title("Model Performance")
badge("evaluation")
st.write(
    f"**{meta['model']}.** Trained on {meta['training_tests']} FLEX tests ({meta['training_sustained']} sustained). "
    "Evaluated with 5 × repeated 5-fold cross-validation grouped by chamber atmosphere: tests that shared an "
    "atmosphere never appear in both training and test data."
)

nested = val["nested_threshold_estimates"]
boot = val["oof_bootstrap_95ci"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("ROC-AUC", f"{nested['roc_auc'][0]:.3f}", help="Ranking quality; 0.5 = chance, 1 = perfect.")
c2.metric("Recall", f"{nested['recall@safe'][0]:.0%}",
          help="Share of sustained-combustion tests flagged at the alert threshold (chosen inside each training fold).")
c3.metric("Precision", f"{nested['precision@safe'][0]:.0%}",
          help="Share of alerts where the flame really kept burning.")
c4.metric("Brier", f"{nested['brier'][0]:.3f}", help="Mean squared error of the probability; lower is better.")

rows = []
for key, label in [("roc_auc", "ROC-AUC"), ("pr_auc", "PR-AUC"), ("brier", "Brier score"),
                   ("recall@safe", "Recall (sustained) at alert threshold"),
                   ("precision@safe", "Precision at alert threshold"),
                   ("false_negative_rate@safe", "Missed-fire rate")]:
    bkey = {"recall@safe": "recall", "precision@safe": "precision", "false_negative_rate@safe": "false_negative_rate"}.get(key, key)
    b = boot.get(bkey)
    rows.append({"Metric": label, "Nested CV (mean ± sd, 25 folds)": f"{nested[key][0]:.3f} ± {nested[key][1]:.3f}",
                 "Pooled out-of-fold, 95% group-bootstrap CI": f"{b[0]:.3f} [{b[1]:.3f}, {b[2]:.3f}]" if b else "—"})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
st.caption("The nested column is the honest estimate for new tests. The bootstrap column uses the single deployed "
           "threshold (chosen on the same predictions, so slightly optimistic for recall) and shows uncertainty "
           "from having only 44 distinct atmospheres.")

st.subheader("Calibration — can the score be read as a probability?")
c1, c2 = st.columns([1.1, 1])
with c1:
    st.plotly_chart(charts.calibration(data.report("phase9", "reliability.csv")), theme="streamlit", width="stretch")
with c2:
    lo, hi = val["calibration_slope_range"]
    st.write(f"Calibration slope across CV repeats: **{lo:.2f}–{hi:.2f}** (1.00 = perfect). Points near the "
             "diagonal mean that, for example, conditions scored around 40 kept burning about 40% of the time.")
    st.write("No recalibration is applied.")

st.subheader("Risk bands")
st.plotly_chart(charts.oof_strip(data.oof_final(), fm.bands.alert_threshold), theme="streamlit", width="stretch")
bands = data.report("phase9", "risk_bands.csv")
st.dataframe(bands[["band", "tests", "sustained", "observed_sustained_rate", "ci_low", "ci_high"]], hide_index=True,
             width="stretch", column_config={
                 "observed_sustained_rate": st.column_config.NumberColumn("Observed sustained", format="percent"),
                 "ci_low": st.column_config.NumberColumn("CI low", format="percent"),
                 "ci_high": st.column_config.NumberColumn("CI high", format="percent")})
st.caption(f"Alert threshold Fire Risk {100 * fm.bands.alert_threshold:.1f}: the highest score at which at least 90% "
           "of sustained tests were flagged out-of-fold. LOW is not 'safe' — some LOW tests kept burning.")

st.subheader("Where the model is weaker")
sub = data.report("phase9", "subgroups.csv")
st.dataframe(sub[["subgroup", "tests", "sustained", "roc_auc", "recall", "missed_fires", "false_alarms"]],
             hide_index=True, width="stretch",
             column_config={"roc_auc": st.column_config.NumberColumn("ROC-AUC", format="%.2f"),
                            "recall": st.column_config.NumberColumn("Recall", format="%.2f")})
st.write("Methanol fires are missed more often than heptane fires. The sustained tests missed in most CV repeats:")
st.dataframe(data.report("phase9", "consistently_missed_fires.csv")[
    ["test_id", "flex_identifier", "fuel", "diluent", "x_o2", "x_co2", "x_he", "d0_mm", "outcome_raw",
     "missed_in_repeats"]], hide_index=True, width="stretch")
st.caption("Full details: docs/model_card.md in the project repository.")
