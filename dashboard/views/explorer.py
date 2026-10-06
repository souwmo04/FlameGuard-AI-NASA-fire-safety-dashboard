import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge

st.title("Experiment Explorer")
badge("observed")
st.write(
    "Every FLEX droplet-combustion test as recorded by NASA (PSI-69 / NASA/TP-2015-216046). "
    "Nothing on this page comes from the model."
)

m = data.master()

f1, f2, f3, f4 = st.columns(4)
fuels = f1.multiselect("Fuel", ["Methanol", "Heptane"], default=["Methanol", "Heptane"])
diluents = f2.multiselect("Suppressant added", ["N2", "CO2", "He"], default=["N2", "CO2", "He"],
                          format_func=lambda d: charts.DILUENT_LABELS[d])
levels = f3.multiselect("Pressure", ["0.7atm", "1atm", "2-3atm"], default=["0.7atm", "1atm", "2-3atm"])
outcomes = f4.multiselect("Observed outcome", ["Extinction", "Completion", "Disruption"],
                          default=["Extinction", "Completion", "Disruption"])

view = m[m["fuel"].isin(fuels) & m["diluent"].isin(diluents) & m["pressure_level"].isin(levels)
         & m["outcome_raw"].isin(outcomes)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tests shown", len(view))
c2.metric("Extinction", int((view["outcome_raw"] == "Extinction").sum()))
c3.metric("Completion", int((view["outcome_raw"] == "Completion").sum()))
c4.metric("Disruption", int((view["outcome_raw"] == "Disruption").sum()))

if view.empty:
    st.info("No tests match these filters.")
    st.stop()

st.plotly_chart(charts.explorer_scatter(view.dropna(subset=["d0_mm"])), theme="streamlit", width="stretch")
missing_d0 = int(view["d0_mm"].isna().sum())
st.caption(
    "Filled triangles: flame kept burning (Completion or Disruption). Open circles: flame self-extinguished. "
    + (f"{missing_d0} test(s) without a recorded droplet diameter are listed in the table but not plotted."
       if missing_d0 else "")
)

st.subheader("Test records")
cols = ["test_id", "flex_identifier", "test_datetime_gmt", "fuel", "pressure_atm", "x_o2", "x_n2", "x_co2", "x_he",
        "d0_mm", "outcome_raw", "d_ext_mm", "burn_rate_mm2_s", "burn_time_s", "qc_flags"]
st.dataframe(
    view[cols], hide_index=True, width="stretch",
    column_config={
        "test_id": "Test", "flex_identifier": "FLEX ID", "test_datetime_gmt": "Date/time (GMT)",
        "pressure_atm": st.column_config.NumberColumn("Pressure (atm)", format="%.2f"),
        "x_o2": "O₂", "x_n2": "N₂", "x_co2": "CO₂", "x_he": "He",
        "d0_mm": st.column_config.NumberColumn("d₀ (mm)", format="%.2f"),
        "outcome_raw": "Outcome",
        "d_ext_mm": st.column_config.NumberColumn("Extinction diameter (mm)", format="%.2f"),
        "burn_rate_mm2_s": st.column_config.NumberColumn("Burning rate (mm²/s)", format="%.2f"),
        "burn_time_s": st.column_config.NumberColumn("Burn time (s)", format="%.1f"),
        "qc_flags": "Data-quality flags",
    },
)
st.download_button("Download these rows (CSV)", view[cols].to_csv(index=False).encode("utf-8"),
                   file_name="flex_tests_filtered.csv", mime="text/csv")
st.caption(f"Source: NASA PSI-69, DOI {data.FLEX_DOI} ([investigation page]({data.FLEX_URL})). "
           "Mole fractions are as recorded by NASA (not renormalised); blanks are values NASA did not report.")
