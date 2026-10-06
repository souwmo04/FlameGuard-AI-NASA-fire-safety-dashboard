import streamlit as st

from dashlib import data
from dashlib.ui import provenance_legend

m = data.master()
card = data.model_card()
meta = card["metadata"]
nested = meta["validation"]["nested_threshold_estimates"]

st.title("FlameGuard AI")
st.markdown("#### Fire-safety insights from NASA microgravity combustion experiments")
st.write(
    "FlameGuard turns the results of NASA's **Flame Extinguishment Experiment (FLEX)** — fuel droplets burned "
    "aboard the International Space Station, 2009–2011 — into an interactive, explainable model of when a flame "
    "in microgravity keeps burning and when it puts itself out."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("FLEX tests", f"{len(m)}", help="All tests in NASA PSI-69, March 2009 - December 2011.")
c2.metric("Self-extinguished", f"{int((m['outcome_raw'] == 'Extinction').sum())}",
          help="Observed NASA outcome 'Extinction'.")
c3.metric("Fuels", f"{m['fuel'].nunique()}", help="Methanol and n-heptane droplets.")
c4.metric("ROC-AUC (CV)", f"{nested['roc_auc'][0]:.3f}",
          help="Model ranking quality, mean over 25 cross-validation test folds grouped by chamber atmosphere; "
               "tests in a fold were never used for training.")

st.divider()
st.subheader("How to read this dashboard")
st.write("Every number carries one of these labels, so observed NASA results are never confused with model output.")
provenance_legend()

st.divider()
st.subheader("Pages")
for target, label, icon, note in [
    ("views/explorer.py", "Experiment Explorer", ":material/science:",
     "Browse all 274 FLEX tests and their observed outcomes."),
    ("views/predictor.py", "Fire Risk Predictor", ":material/local_fire_department:",
     "Set fuel, oxygen, suppressant and droplet size; see the predicted risk and why."),
    ("views/ranking.py", "Ranking", ":material/leaderboard:",
     "Which tested conditions sustained combustion most often, and how the model ranks tests."),
    ("views/performance.py", "Model Performance", ":material/fact_check:",
     "How well the model does on tests it never saw, and where it is weak."),
    ("views/about.py", "Data & Methods", ":material/menu_book:",
     "Sources, citation, pipeline, decisions and limitations."),
]:
    st.page_link(target, label=f"**{label}** — {note}", icon=icon)

st.divider()
st.caption(
    f"Data: NASA Physical Sciences Informatics, FLEX (PSI-69), DOI {data.FLEX_DOI}, CC0-1.0. "
    "FlameGuard is a research prototype for the NASA Space Apps Challenge 2026; it is not a certified "
    "spacecraft fire-safety system and makes no claims about specific vehicles or missions."
)
