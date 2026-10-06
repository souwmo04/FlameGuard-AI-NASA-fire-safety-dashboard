"""Plotly figures for the dashboard. Series colours are the project's CVD-validated palette;
chart chrome follows the Streamlit theme (light/dark) via st.plotly_chart(theme="streamlit")."""

from __future__ import annotations

import numpy as np
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


SCENARIO_COLORS = {"A": "#2a78d6", "B": "#eb6834"}


def path_chart(path: pd.DataFrame) -> go.Figure:
    """Fire Risk after each one-at-a-time change from scenario A to scenario B."""
    labels = [("A (baseline)" if s == "baseline" else f"{i}. {s}") for i, s in enumerate(path["step"])]
    supported = path["supported_by_data"] & path["in_tested_range"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=path["fire_risk"], mode="lines", line=dict(color=NEUTRAL, width=2),
                             hoverinfo="skip", showlegend=False))
    for ok, name, symbol in [(True, "inside tested conditions", "circle"),
                             (False, "extrapolation (untested combination)", "circle-open")]:
        sel = supported == ok
        if sel.any():
            fig.add_trace(go.Scatter(
                x=[l for l, s in zip(labels, sel) if s], y=path.loc[sel, "fire_risk"], mode="markers+text",
                name=name, marker=dict(size=14, symbol=symbol, color=SCENARIO_COLORS["B"],
                                       line=dict(width=2, color=SCENARIO_COLORS["B"])),
                text=[f"{r:.0f}" for r in path.loc[sel, "fire_risk"]], textposition="top center",
                customdata=path.loc[sel, ["change", "delta", "risk_band"]],
                hovertemplate="%{customdata[0]}<br>Fire Risk <b>%{y:.1f}</b> (%{customdata[1]:+.1f})"
                              " · %{customdata[2]}<extra></extra>"))
    fig.update_yaxes(range=[-5, 110], title_text="Fire Risk (0\u2013100)")
    return _layout(fig, 360)


def sweep_chart(curves: dict[str, pd.DataFrame], feature: str, label: str,
                markers: dict[str, float] | None = None) -> go.Figure:
    """Risk vs one input per scenario; hollow points = outside the tested region."""
    fig = go.Figure()
    for name, df in curves.items():
        color = SCENARIO_COLORS[name]
        fig.add_trace(go.Scatter(x=df[feature], y=df["fire_risk"], mode="lines", line=dict(color=color, width=2),
                                 name=f"Scenario {name}", hovertemplate=f"{label} %{{x:.2f}}: Fire Risk <b>%{{y:.1f}}</b><extra>{name}</extra>"))
        off = df[~df["supported"]]
        if not off.empty:
            fig.add_trace(go.Scatter(x=off[feature], y=off["fire_risk"], mode="markers", showlegend=False,
                                     marker=dict(symbol="circle-open", size=7, color=color), hoverinfo="skip"))
        if markers and name in markers:
            x0 = markers[name]
            y0 = float(np.interp(x0, df[feature], df["fire_risk"]))
            fig.add_trace(go.Scatter(x=[x0], y=[y0], mode="markers", showlegend=False,
                                     marker=dict(size=14, color=color, line=dict(width=2, color="white")),
                                     hovertemplate=f"Scenario {name}: Fire Risk <b>%{{y:.1f}}</b><extra></extra>"))
    fig.update_xaxes(title_text=label)
    fig.update_yaxes(range=[-3, 103], title_text="Fire Risk (0\u2013100)")
    return _layout(fig, 340)


def o2_50_chart(table: pd.DataFrame) -> go.Figure:
    """Estimated O2_50 per series with 95% bootstrap interval (estimable series only)."""
    est = table[table["status"] == "estimated"].copy()
    est["label"] = est["fuel"] + " · " + est["pressure"].str.replace("atm", " atm") + " · " + est["diluent"].map(DILUENT_LABELS)
    est = est.sort_values(["fuel", "pressure", "o2_50"])
    fig = go.Figure(go.Scatter(
        x=est["o2_50"], y=est["label"], mode="markers",
        marker=dict(size=13, color=[DILUENT_COLORS[d] for d in est["diluent"]],
                    symbol=["circle" if not b else "circle-open" for b in est["ci_beyond_tested"]],
                    line=dict(width=2, color=[DILUENT_COLORS[d] for d in est["diluent"]])),
        error_x=dict(type="data", symmetric=False, array=est["ci_high"] - est["o2_50"],
                     arrayminus=est["o2_50"] - est["ci_low"], color=NEUTRAL, thickness=1.4, width=0),
        customdata=est[["ci_low", "ci_high", "tests", "sustained", "o2_tested_min", "o2_tested_max"]],
        hovertemplate=("O\u2082\u2085\u2080 <b>%{x:.3f}</b> (95% CI %{customdata[0]:.3f}\u2013%{customdata[1]:.3f})<br>"
                       "%{customdata[3]} of %{customdata[2]} tests sustained · tested O\u2082 "
                       "%{customdata[4]:.2f}\u2013%{customdata[5]:.2f}<extra>%{y}</extra>"),
    ))
    fig.update_xaxes(title_text="O\u2082 mole fraction at which half of 3 mm droplets kept burning (O\u2082\u2085\u2080)")
    fig.update_yaxes(automargin=True, autorange="reversed")
    return _layout(fig, 90 + 46 * len(est))


def series_strip(df: pd.DataFrame) -> go.Figure:
    """Observed outcomes per test series: O2 on x, suppressant on y, fuel x pressure facets."""
    combos = [(f, p) for f in FUELS for p in ["0.7atm", "1atm"]]
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True, shared_yaxes=True, vertical_spacing=0.14,
                        horizontal_spacing=0.04, subplot_titles=[f"{f} · {p.replace('atm', ' atm')}" for f, p in combos])
    rng = np.random.default_rng(0)
    ypos = {"N2": 0, "CO2": 1, "He": 2}
    for k, (fuel, p) in enumerate(combos):
        r, c = k // 2 + 1, k % 2 + 1
        for dil in ["N2", "CO2", "He"]:
            for sustained in (0, 1):
                sub = df[(df["fuel"] == fuel) & (df["pressure_level"] == p) & (df["diluent"] == dil)
                         & (df["y_sustained"] == sustained)]
                if sub.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=sub["x_o2"] + rng.uniform(-0.002, 0.002, len(sub)),
                    y=ypos[dil] + (0.18 if sustained else -0.18) + rng.uniform(-0.08, 0.08, len(sub)),
                    mode="markers", showlegend=k == 0,
                    name=f"{DILUENT_LABELS[dil]} · {'sustained' if sustained else 'extinguished'}",
                    legendgroup=f"{dil}{sustained}",
                    marker=dict(symbol="triangle-up" if sustained else "circle-open", size=9 if sustained else 8,
                                color=DILUENT_COLORS[dil], line=dict(width=1.6, color=DILUENT_COLORS[dil])),
                    customdata=sub[["test_id", "x_co2", "x_he", "d0_mm", "outcome_raw"]],
                    hovertemplate=("<b>%{customdata[4]}</b> · test %{customdata[0]}<br>O\u2082 %{x:.2f} · CO\u2082 "
                                   "%{customdata[1]:.2f} · He %{customdata[2]:.2f} · d\u2080 %{customdata[3]:.2f} mm"
                                   "<extra></extra>")), row=r, col=c)
    fig.update_yaxes(tickvals=[0, 1, 2], ticktext=["N\u2082 only", "CO\u2082", "He"], range=[-0.6, 2.6])
    fig.update_xaxes(title_text="O\u2082 mole fraction", row=2)
    fig = _layout(fig, 560)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.12, x=0), margin=dict(b=110))
    return fig
