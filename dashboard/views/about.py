import streamlit as st

from dashlib import data

st.title("Data & Methods")

st.subheader("Data")
st.markdown(f"""
- **NASA FLEX — Flame Extinguishment Experiment** (ISS, Multi-User Droplet Combustion Apparatus in the
  Combustion Integrated Rack), 274 tests from March 2009 to December 2011.
- Source: NASA Physical Sciences Informatics, investigation **PSI-69**, DOI **{data.FLEX_DOI}**, licence CC0-1.0
  ([investigation page]({data.FLEX_URL})).
- Column definitions and per-test notes: Dietrich et al., *Detailed Results from the Flame Extinguishment Experiment
  (FLEX)*, NASA/TP-2015-216046 ([NTRS]({data.REPORT_URL})).
- Raw files are kept byte-identical to the NASA download (SHA-256 checksums); cleaning never invents or imputes values.
""")

st.subheader("What the model predicts")
st.markdown("""
**Fire Risk = 100 × P(sustained)**: the estimated probability that a burning single droplet of methanol or
n-heptane, in a quiescent microgravity atmosphere at 0.7–1 atm, keeps burning instead of self-extinguishing while
fuel remains. NASA's outcome *Completion* or *Disruption* counts as sustained; *Extinction* as self-extinguished.
""")

st.subheader("Pipeline")
st.markdown("""
1. **Clean** the NASA table without changing values; flag anomalies instead of dropping them.
2. **Explore** the data; key findings: oxygen dominates, droplet size acts in opposite directions for the two fuels,
   and NASA varied oxygen and suppressant together.
3. **Validate** with cross-validation grouped by chamber atmosphere, so near-duplicate tests never sit on both sides.
4. **Compare** baselines, logistic regression, random forest and XGBoost; tune with nested CV; select by a rule fixed
   in advance (lowest log loss, simplest within one standard error).
5. **Stress-test** on held-out suppressants and pressures; drop pressure after it caused unsafe extrapolation
   (decision D-001).
6. **Calibrate and band** the score from out-of-fold predictions; **explain** each prediction with exact Shapley values.
""")

st.subheader("Limitations")
st.markdown("""
- Two fuels, single droplets, quiescent atmosphere, 0.7–1 atm, ambient temperature. No solid materials, airflow,
  cabin geometry or large fires — results do not transfer to those settings without new evidence.
- 252 training tests from 44 atmospheres; methanol with helium has only 2 sustained tests.
- The model cannot separate a suppressant's effect from the oxygen reduction it came with.
- NASA selected tests to locate extinction limits, so outcome rates are not real-world fire frequencies.
- Explanations show how the model uses its inputs — associations, not causal effects.
- Research prototype; not a certified fire-safety system.
""")

st.subheader("Cite")
st.code(f"NASA Physical Sciences Informatics. Flame Extinguishment Experiment (FLEX), PSI-69. "
        f"https://doi.org/{data.FLEX_DOI}", language=None)
