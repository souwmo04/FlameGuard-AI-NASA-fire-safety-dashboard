"""Plotly figures for the dashboard. Series colours are the project's CVD-validated palette;
chart chrome follows the Streamlit theme (light/dark) via st.plotly_chart(theme="streamlit")."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DILUENT_COLORS = {"N2": "#2a78d6", "CO2": "#eb6834", "He": "#1baf7a"}
DILUENT_LABELS = {"N2": "N₂ only", "CO2": "CO₂ added", "He": "He added"}
FUELS = ["Methanol", "Heptane"]
RAISE, LOWER = "#e34948", "#2a78d6"  # diverging poles
NEUTRAL = "#898781"


def _layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                      hoverlabel=dict(font_size=13))
    return fig


def explorer_scatter(df: pd.DataFrame) -> go.Figure:
    """Observed outcomes: O2 vs droplet size per fuel; colour = diluent, filled triangle = sustained."""
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=FUELS, horizontal_spacing=0.05)
    for col, fuel in enumerate(FUELS, start=1):
        for dil in ["N2", "CO2", "He"]:
            for sustained in (0, 1):
                sub = df[(df["fuel"] == fuel) & (df["diluent"] == dil) & (df["y_sustained"] == sustained)]
                if sub.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=sub["d0_mm"], y=sub["x_o2"], mode="markers",
                    name=f"{DILUENT_LABELS[dil]} · {'sustained' if sustained else 'extinguished'}",
                    legendgroup=f"{dil}{sustained}", showlegend=col == 1,
                    marker=dict(symbol="triangle-up" if sustained else "circle-open", size=11 if sustained else 9,
                                color=DILUENT_COLORS[dil], line=dict(width=2 if not sustained else 0.8,
                                                                    color=DILUENT_COLORS[dil])),
                    customdata=sub[["test_id", "flex_identifier", "outcome_raw", "x_co2", "x_he", "pressure_level"]],
                    hovertemplate=("<b>%{customdata[2]}</b> (test %{customdata[0]}, %{customdata[1]})<br>"
                                   "O₂ %{y:.2f} · CO₂ %{customdata[3]:.2f} · He %{customdata[4]:.2f}<br>"
                                   "d₀ %{x:.2f} mm · %{customdata[5]}<extra></extra>"),
                ), row=1, col=col)
    fig.update_xaxes(title_text="Initial droplet diameter (mm)")
    fig.update_yaxes(title_text="O₂ mole fraction", row=1, col=1)
    fig = _layout(fig, 520)
    # six legend entries: put them under the plot so they never cover the fuel titles
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.18, x=0), margin=dict(b=120))
    return fig


def waterfall(contrib: pd.Series) -> go.Figure:
    """Average test -> contributions -> prediction (Fire Risk points)."""
    players = [c for c in contrib.index if c not in {"base", "fire_risk"}]
    fig = go.Figure(go.Waterfall(
        orientation="h",
        measure=["absolute", *["relative"] * len(players), "total"],
        y=["average FLEX test", *players, "this prediction"],
        x=[contrib["base"], *[contrib[p] for p in players], contrib["fire_risk"]],
        text=[f"{contrib['base']:.0f}", *[f"{contrib[p]:+.1f}" for p in players], f"{contrib['fire_risk']:.0f}"],
        textposition="outside",
        increasing=dict(marker=dict(color=RAISE)), decreasing=dict(marker=dict(color=LOWER)),
        totals=dict(marker=dict(color=NEUTRAL)),
        connector=dict(line=dict(color=NEUTRAL, width=1, dash="dot")),
        hovertemplate="%{y}: %{x:.1f}<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 112], title_text="Fire Risk (0–100)")
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, 300)


def rate_dots(df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    """Observed rate with 95% Wilson interval per row (dot + error bar)."""
    d = df.iloc[::-1]
    fig = go.Figure(go.Scatter(
        x=d["observed_rate"], y=d[label_col], mode="markers",
        marker=dict(size=11, color=[DILUENT_COLORS.get(x, NEUTRAL) for x in d["diluent"]]),
        error_x=dict(type="data", symmetric=False, array=d["ci_high"] - d["observed_rate"],
                     arrayminus=d["observed_rate"] - d["ci_low"], color=NEUTRAL, thickness=1.2, width=0),
        customdata=d[["tests", "sustained", "ci_low", "ci_high"]],
        hovertemplate=("<b>%{x:.0%}</b> sustained (%{customdata[1]} of %{customdata[0]} tests)<br>"
                       "95% CI %{customdata[2]:.0%}–%{customdata[3]:.0%}<extra>%{y}</extra>"),
    ))
    fig.update_xaxes(range=[-0.02, 1.02], tickformat=".0%", title_text="Observed share of tests sustained")
    fig.update_yaxes(automargin=True)
    fig.update_layout(title=title)
    return _layout(fig, 60 + 28 * len(d))


def calibration(rel: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=NEUTRAL, dash="dot", width=1),
                             name="perfect calibration", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=rel["mean_predicted"], y=rel["observed_rate"], mode="markers", name="final model (out-of-fold)",
        marker=dict(size=12, color=LOWER),
        error_y=dict(type="data", symmetric=False, array=rel["ci_high"] - rel["observed_rate"],
                     arrayminus=rel["observed_rate"] - rel["ci_low"].clip(lower=0), color=NEUTRAL, thickness=1.2,
                     width=0),
        customdata=rel[["n", "sustained"]],
        hovertemplate=("predicted %{x:.2f} → observed <b>%{y:.0%}</b><br>"
                       "%{customdata[1]} of %{customdata[0]} tests sustained<extra></extra>"),
    ))
    fig.update_xaxes(range=[-0.02, 1.02], title_text="Mean predicted P(sustained)")
    fig.update_yaxes(range=[-0.02, 1.02], title_text="Observed share sustained")
    return _layout(fig, 420)


def oof_strip(df: pd.DataFrame, alert: float) -> go.Figure:
    """Out-of-fold Fire Risk per test, split by observed outcome, with band boundaries."""
    fig = go.Figure()
    for y, name, symbol in [(0, "Extinguished (observed)", "circle-open"), (1, "Sustained (observed)", "triangle-up")]:
        sub = df[df["y_sustained"] == y]
        fig.add_trace(go.Box(
            x=100 * sub["p_oof"], name=name, boxpoints="all", jitter=0.6, pointpos=0, fillcolor="rgba(0,0,0,0)",
            line=dict(color="rgba(0,0,0,0)"), marker=dict(symbol=symbol, size=8, color=LOWER),
            customdata=sub[["test_id", "fuel", "outcome_raw"]],
            hovertemplate="Fire Risk %{x:.1f}<br>test %{customdata[0]} · %{customdata[1]} · %{customdata[2]}<extra></extra>",
        ))
    for x, label in [(100 * alert, f"alert {100 * alert:.1f}"), (50, "high 50")]:
        fig.add_vline(x=x, line=dict(color=NEUTRAL, dash="dash", width=1), annotation_text=label,
                      annotation_position="top")
    fig.update_xaxes(range=[-1, 101], title_text="Fire Risk (out-of-fold prediction)")
    fig.update_layout(showlegend=False)
    return _layout(fig, 300)
