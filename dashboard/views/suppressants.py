import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge

st.title("Suppressant Comparison")
st.write(
    "FLEX ran separate test series for each fuel and pressure with **nitrogen only**, **CO₂ added** or **helium "
    "added**, lowering oxygen until flames stopped surviving. This page compares those series using the observed "
    "tests only — no machine-learning model is involved."
)

st.subheader("What was observed")
badge("observed")
m = data.master()
m = m[m["pressure_level"].isin(["0.7atm", "1atm"])]
st.plotly_chart(charts.series_strip(m), theme="streamlit", width="stretch")
st.caption("Each mark is one ISS test. Triangles: kept burning; circles: self-extinguished. Within the CO₂ and He "
           "series the suppressant fraction increased as oxygen decreased (hover a point for its full atmosphere).")

st.subheader("How much oxygen did flames need?")
badge("estimate")
table = data.report("phase12", "o2_50_by_series.csv")
st.write(
    "For each series we estimate **O₂₅₀** — the oxygen mole fraction at which half of 3 mm droplets kept burning — "
    "from a small logistic fit to that series' tests (adjusted for droplet size), with 95% intervals from "
    "resampling the tested atmospheres. A **higher O₂₅₀** means flames in that atmosphere needed more oxygen to "
    "survive."
)
st.plotly_chart(charts.o2_50_chart(table), theme="streamlit", width="stretch")
st.caption("Hollow markers: part of the interval lies outside the oxygen range tested in that series.")

est = table[table["status"] == "estimated"]
hep1 = est[(est["fuel"] == "Heptane") & (est["pressure"] == "1atm")].set_index("diluent")
if {"N2", "CO2"} <= set(hep1.index):
    n2, co2 = hep1.loc["N2"], hep1.loc["CO2"]
    he_txt = ""
    if "He" in hep1.index:
        he = hep1.loc["He"]
        he_txt = (f" Helium gives {he['o2_50']:.3f}, but its interval ({he['ci_low']:.3f}–{he['ci_high']:.3f}) is too "
                  "wide to place it.")
    st.markdown(
        f"**What the data supports.** Only **heptane at 1 atm** has enough tests in more than one series to compare. "
        f"There, CO₂-diluted atmospheres needed somewhat more oxygen (O₂₅₀ {co2['o2_50']:.3f}, 95% CI "
        f"{co2['ci_low']:.3f}–{co2['ci_high']:.3f}) than nitrogen-only ones ({n2['o2_50']:.3f}, "
        f"{n2['ci_low']:.3f}–{n2['ci_high']:.3f}), but the intervals overlap.{he_txt} "
        "**These observations do not establish a ranking of the suppressants.**"
    )

with st.expander("All series, including those that cannot be estimated"):
    show = table.copy()
    show["series"] = show["fuel"] + " · " + show["pressure"] + " · " + show["diluent"]
    st.dataframe(show[["series", "tests", "sustained", "extinguished", "o2_tested_min", "o2_tested_max", "o2_50",
                       "ci_low", "ci_high", "suppressant_at_o2_50", "status"]], hide_index=True, width="stretch",
                 column_config={"o2_50": st.column_config.NumberColumn("O₂₅₀", format="%.3f"),
                                "ci_low": st.column_config.NumberColumn("CI low", format="%.3f"),
                                "ci_high": st.column_config.NumberColumn("CI high", format="%.3f"),
                                "suppressant_at_o2_50": st.column_config.NumberColumn(
                                    "Suppressant fraction near O₂₅₀", format="%.2f"),
                                "o2_tested_min": "O₂ tested from", "o2_tested_max": "O₂ tested to"})

st.subheader("How to read this — and what it is not")
st.markdown("""
- **Not NASA's limiting oxygen index (LOI).** NASA defines LOI as the oxygen level below which quasi-steady burning
  is not observed at all. O₂₅₀ asks whether a flame survived until its fuel was gone. They are related, not equal.
- **Series are not perfectly comparable.** Each series was run on different days, with its own droplet sizes, and
  the suppressant amount changed together with oxygen. Differences can reflect the test design, not only the gas.
- **SF₆** appears in FLEX's objectives but no SF₆ tests are in this dataset, so it cannot be compared.
- Methodology: `src/flameguard/suppressant.py`; numbers: `reports/phase12/o2_50_by_series.csv`.
""")
