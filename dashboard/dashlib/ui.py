"""Shared UI pieces: provenance badges, risk card, sidebar notice.

Provenance is never colour-only: every badge carries an icon and a text label.
"""

from __future__ import annotations

import streamlit as st

PROVENANCE = {
    "observed": (":material/science:", "Observed NASA result", "blue"),
    "prediction": (":material/model_training:", "Model prediction", "violet"),
    "explanation": (":material/insights:", "Model explanation (SHAP)", "green"),
    "hypothetical": (":material/tune:", "Hypothetical scenario", "orange"),
    "evaluation": (":material/fact_check:", "Model evaluation (cross-validated)", "gray"),
}

BAND_STYLE = {
    "LOW": (":material/check_circle:", "green"),
    "ELEVATED": (":material/warning:", "orange"),
    "HIGH": (":material/local_fire_department:", "red"),
}


def badge(kind: str) -> None:
    icon, label, color = PROVENANCE[kind]
    st.badge(label, icon=icon, color=color)


def provenance_legend() -> None:
    notes = {
        "observed": "Measured on the ISS in NASA's FLEX experiment.",
        "prediction": "Output of the trained model; not a measurement.",
        "explanation": "How the model used each input; associations, not causes.",
        "hypothetical": "A condition you set; may not have been tested.",
        "evaluation": "Model scored on tests it never saw during training.",
    }
    for kind, (icon, label, color) in PROVENANCE.items():
        st.markdown(f":{color}-badge[{icon} {label}] &nbsp; {notes[kind]}")


def sidebar_notice() -> None:
    with st.sidebar:
        st.caption(
            "**Research prototype** built on NASA FLEX data (PSI-69) for the NASA Space Apps Challenge 2026. "
            "Not a certified spacecraft fire-safety system."
        )


def risk_card(result, band_stats: dict) -> None:
    """Large Fire Risk readout. `result` is one row of FinalModel.predict()."""
    from flameguard.explainability import format_risk

    band = result["risk_band"]
    icon, color = BAND_STYLE[band]
    with st.container(border=True):
        badge("prediction")
        c1, c2, c3 = st.columns([1.3, 1, 1])
        c1.metric("Fire Risk", f"{format_risk(result['fire_risk'])} / 100")
        c2.metric("Keeps burning", f"{100 * result['p_sustained']:.0f}%", help="P(sustained combustion)")
        c3.metric("Goes out", f"{100 * result['p_extinction']:.0f}%", help="P(self-extinction)")
        st.badge(f"{band} risk", icon=icon, color=color)
        stats = band_stats.get(band)
        if stats:
            st.caption(
                f"In cross-validation, {stats['observed_sustained_rate']:.0%} of the {int(stats['tests'])} FLEX tests "
                f"the model placed in the {band} band actually kept burning "
                f"(95% CI {stats['ci_low']:.0%}–{stats['ci_high']:.0%})."
            )
