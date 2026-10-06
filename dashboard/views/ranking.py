import streamlit as st

from dashlib import charts, data
from dashlib.ui import badge
from flameguard.explainability import format_risk

st.title("Ranking")
tab_obs, tab_model = st.tabs(["Tested conditions — observed", "Tests — model risk (out-of-fold)"])

with tab_obs:
    badge("observed")
    st.write("Each row is one fuel in one tested chamber atmosphere (0.7–1 atm, at least 3 tests). The rate is the share "
             "of those ISS tests in which the flame kept burning.")
    rank = data.observed_condition_ranking(min_tests=3)
    rank["condition"] = rank.apply(
        lambda r: f"{r['fuel']} · O₂ {r['x_o2']:.2f}"
                  + (f" · CO₂ {r['x_co2']:.2f}" if r["x_co2"] > 0 else "")
                  + (f" · He {r['x_he']:.2f}" if r["x_he"] > 0 else "") + f" · {r['pressure'].replace('atm', ' atm')}",
        axis=1)
    k = st.slider("Conditions to show", 5, min(25, len(rank)), 12)
    top = rank.sort_values(["observed_rate", "tests"], ascending=[False, False]).head(k)
    low = rank.sort_values(["observed_rate", "tests"], ascending=[True, False]).head(k)
    st.plotly_chart(charts.rate_dots(top, "condition", "Most often sustained"), theme="streamlit", width="stretch")
    st.plotly_chart(charts.rate_dots(low, "condition", "Most often self-extinguished"), theme="streamlit",
                    width="stretch")
    st.caption("Dot colour = suppressant (blue N₂ only, orange CO₂, green He); bars = 95% Wilson interval. Wide bars "
               "mean few tests. Conditions differ in droplet sizes tested, so rates are not a controlled comparison.")
    with st.expander("All ranked conditions (table)"):
        st.dataframe(rank.sort_values("observed_rate", ascending=False)[
            ["condition", "tests", "sustained", "observed_rate", "ci_low", "ci_high"]], hide_index=True,
            width="stretch", column_config={
                "observed_rate": st.column_config.NumberColumn("Observed rate", format="percent"),
                "ci_low": st.column_config.NumberColumn("CI low", format="percent"),
                "ci_high": st.column_config.NumberColumn("CI high", format="percent")})

with tab_model:
    badge("prediction")
    st.write("Each FLEX test's Fire Risk as predicted by models that **never saw that test** (out-of-fold, averaged "
             "over 5 cross-validation repeats), next to what actually happened.")
    oof = data.oof_final().copy()
    oof["fire_risk"] = 100 * oof["p_oof"]
    oof["risk"] = oof["fire_risk"].map(format_risk)
    cols = ["test_id", "fuel", "x_o2", "x_co2", "x_he", "d0_mm", "risk", "outcome_raw"]
    cfg = {"test_id": "Test", "x_o2": "O₂", "x_co2": "CO₂", "x_he": "He",
           "d0_mm": st.column_config.NumberColumn("d₀ (mm)", format="%.2f"), "risk": "Predicted Fire Risk",
           "outcome_raw": "Observed outcome"}
    n = st.slider("Tests to show", 5, 30, 10)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Highest predicted risk**")
        st.dataframe(oof.nlargest(n, "fire_risk")[cols], hide_index=True, width="stretch", column_config=cfg)
    with c2:
        st.markdown("**Easiest to extinguish (lowest predicted risk)**")
        st.dataframe(oof.nsmallest(n, "fire_risk")[cols], hide_index=True, width="stretch", column_config=cfg)
    st.caption("Out-of-fold predictions keep this honest: a model cannot rank a test highly because it memorised it.")
