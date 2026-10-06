import pandas as pd
import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge, risk_card
from flameguard.explainability import describe

fm = data.model()
ranges = fm.domain.ranges

st.title("Fire Risk Predictor")
st.write(
    "Estimate whether a burning fuel droplet in a quiescent microgravity atmosphere would **keep burning** or "
    "**put itself out**, using the model trained on NASA FLEX experiments."
)

with st.container(border=True):
    badge("hypothetical")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        fuel = st.radio("Fuel", ["Methanol", "Heptane"], horizontal=True, key="fuel")
        r = ranges[fuel]
        supp = st.selectbox("Suppressant added", ["None (O₂/N₂ only)", "CO₂", "He"], key="supp")
        x_co2 = x_he = 0.0
        if supp == "CO₂":
            x_co2 = st.slider("CO₂ mole fraction", 0.0, float(r["x_co2"][1]), 0.20, 0.01, key="co2")
        elif supp == "He":
            x_he = st.slider("He mole fraction", 0.0, float(r["x_he"][1]), 0.20, 0.01, key="he")
    with c2:
        o2 = st.slider("Oxygen mole fraction", float(r["x_o2"][0]), float(r["x_o2"][1]), 0.21, 0.01, key="o2",
                       help=f"Tested range for {fuel.lower()}: {r['x_o2'][0]:.2f}–{r['x_o2'][1]:.2f}. Air is 0.21.")
        d0 = st.slider("Initial droplet diameter (mm)", float(r["d0_mm"][0]), float(r["d0_mm"][1]), 3.0, 0.05, key="d0")
    st.caption("Pressure is not a model input; the model is only valid for 0.7–1 atm (decision D-001).")
    current = {"fuel": fuel, "x_o2": o2, "x_co2": x_co2, "x_he": x_he, "d0_mm": d0}
    if st.button("Analyze fire risk", type="primary", width="stretch", key="analyze"):
        st.session_state["last_query"] = current

if "last_query" not in st.session_state:
    st.info("Set the conditions and press **Analyze fire risk**.")
    st.stop()

query = pd.DataFrame([st.session_state["last_query"]])
res = fm.predict(query).iloc[0]
stale = st.session_state["last_query"] != current

if stale:
    st.info("Inputs changed — press **Analyze fire risk** to update. Showing the previous analysis.",
            icon=":material/refresh:")
if not res["supported_by_data"] or not res["in_tested_range"]:
    st.warning("**Extrapolation — treat this number with caution.**\n\n" + "\n\n".join(res["warnings"]),
               icon=":material/report:")
risk_card(res, fm.bands.band_stats)

st.subheader("Why?")
badge("explanation")
contrib = data.explain_query(query)
st.plotly_chart(charts.waterfall(contrib), theme="streamlit", width="stretch")
st.write(describe(contrib, res["risk_band"], query.iloc[0]))
st.caption("Fuel is accounted for first, then the atmosphere (O₂, CO₂ and He together, because NASA varied them "
           "together) and droplet size. The split between O₂ and suppressant is not reliable from this data.")

st.divider()
st.subheader("Most similar NASA tests")
badge("observed")
near = data.nearest_tests(query.iloc[0])
st.dataframe(
    near[["test_id", "flex_identifier", "x_o2", "x_co2", "x_he", "d0_mm", "pressure_level", "outcome_raw",
          "similarity"]],
    hide_index=True, width="stretch",
    column_config={"test_id": "Test", "flex_identifier": "FLEX ID", "x_o2": "O₂", "x_co2": "CO₂", "x_he": "He",
                   "d0_mm": st.column_config.NumberColumn("d₀ (mm)", format="%.2f"), "pressure_level": "Pressure",
                   "outcome_raw": "Observed outcome",
                   "similarity": st.column_config.ProgressColumn("Similarity", min_value=0, max_value=100,
                                                                 format="%d%%")},
)
st.caption(f"Nearest tested {query.iloc[0]['fuel'].lower()} conditions by standardised O₂, CO₂, He and droplet size. "
           "Similarity is 100% for an identical condition and about 37% at the typical spacing between tested "
           "atmospheres. These are real ISS results, shown so every prediction can be checked against evidence.")
