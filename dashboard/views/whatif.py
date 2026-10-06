import numpy as np
import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge, condition_inputs
from flameguard.explainability import format_risk
from flameguard.whatif import predict_one, scenario_path, sweep

fm = data.model()
ranges = fm.domain.ranges

st.title("What-if Analysis")
badge("hypothetical")
st.write(
    "Compare a baseline (**A**) with a changed scenario (**B**) and see how the model's Fire Risk moves as each "
    "condition changes. Every number here is a **model prediction for a hypothetical condition**, not a "
    "measurement."
)

col_a, col_b = st.columns(2, gap="large")
with col_a:
    with st.container(border=True):
        st.markdown("**Scenario A — baseline**")
        a = condition_inputs("wa_", ranges, {"fuel": "Methanol", "x_o2": 0.21, "supp": "None (O₂/N₂ only)",
                                             "d0_mm": 3.0})
with col_b:
    with st.container(border=True):
        st.markdown("**Scenario B — changed**")
        b = condition_inputs("wb_", ranges, {"fuel": "Methanol", "x_o2": 0.18, "supp": "CO₂", "amount": 0.10,
                                             "d0_mm": 3.0})

ra, rb = predict_one(fm, a), predict_one(fm, b)
st.divider()
badge("prediction")
m1, m2, m3 = st.columns(3)
m1.metric("Scenario A", f"{format_risk(ra['fire_risk'])} / 100", help=f"{ra['risk_band']} band")
m2.metric("Scenario B", f"{format_risk(rb['fire_risk'])} / 100", help=f"{rb['risk_band']} band")
m3.metric("Change (B − A)", f"{rb['fire_risk'] - ra['fire_risk']:+.1f} pts", delta_color="off")
st.caption(f"Bands: A = **{ra['risk_band']}**, B = **{rb['risk_band']}**.")

for name, res in [("A", ra), ("B", rb)]:
    if not res["supported_by_data"] or not res["in_tested_range"]:
        st.warning(f"**Scenario {name} is an extrapolation.** " + " ".join(res["warnings"]), icon=":material/report:")

supp_changed_at_fixed_o2 = (a["x_co2"], a["x_he"]) != (b["x_co2"], b["x_he"])
if supp_changed_at_fixed_o2:
    st.info(
        "**About suppressant changes.** NASA lowered oxygen *while* adding CO₂ or He, so the data cannot separate "
        "the two, and adding suppressant at an unchanged oxygen level was rarely tested. The model's response to "
        "the suppressant step below is weakly supported; see **Suppressant Comparison** for what the observed data "
        "can and cannot say.", icon=":material/info:")

st.subheader("Step by step from A to B")
path = scenario_path(fm, a, b)
if len(path) == 1:
    st.write("Scenarios A and B are identical — change something in B.")
else:
    st.plotly_chart(charts.path_chart(path), theme="streamlit", width="stretch")
    table = path[["step", "change", "fire_risk", "delta", "risk_band", "supported_by_data"]].copy()
    table["supported_by_data"] = table["supported_by_data"].map({True: "yes", False: "no — extrapolation"})
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "step": "Step", "change": "Change", "fire_risk": st.column_config.NumberColumn("Fire Risk", format="%.1f"),
        "delta": st.column_config.NumberColumn("Change (pts)", format="%+.1f"), "risk_band": "Band",
        "supported_by_data": "Near tested conditions?"})
    st.caption("Inputs change one at a time in a fixed order (oxygen, suppressant, droplet size, fuel). Because "
               "fuel and droplet size interact, the size of each step depends on that order; the total does not.")

st.subheader("Sensitivity curves")
feature = st.radio("Vary", ["Oxygen", "Droplet size"], horizontal=True, key="sweep_feature")
key, label = ("x_o2", "Oxygen mole fraction") if feature == "Oxygen" else ("d0_mm", "Initial droplet diameter (mm)")
curves = {}
for name, cond in [("A", a), ("B", b)]:
    lo, hi = ranges[cond["fuel"]][key]
    curves[name] = sweep(fm, cond, key, np.linspace(lo, hi, 60))
st.plotly_chart(charts.sweep_chart(curves, key, label, markers={"A": a[key], "B": b[key]}), theme="streamlit",
                width="stretch")
st.caption("Each line holds that scenario's other conditions fixed and varies one input across the range tested "
           "for its fuel. Hollow points mark combinations far from any tested FLEX condition (extrapolation). "
           "Large dots are the scenarios themselves.")
