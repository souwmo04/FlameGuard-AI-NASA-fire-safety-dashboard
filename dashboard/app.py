"""FlameGuard AI dashboard.

Run from the project root:
    .venv/Scripts/streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

import streamlit as st  # noqa: E402

from dashlib.ui import sidebar_notice  # noqa: E402

st.set_page_config(page_title="FlameGuard AI", page_icon=":material/local_fire_department:", layout="wide")

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    ],
    "NASA data (observed)": [
        st.Page("views/explorer.py", title="Experiment Explorer", icon=":material/science:"),
    ],
    "Model": [
        st.Page("views/predictor.py", title="Fire Risk Predictor", icon=":material/local_fire_department:"),
        st.Page("views/ranking.py", title="Ranking", icon=":material/leaderboard:"),
        st.Page("views/performance.py", title="Model Performance", icon=":material/fact_check:"),
    ],
    "About": [
        st.Page("views/about.py", title="Data & Methods", icon=":material/menu_book:"),
    ],
}

nav = st.navigation(pages)
sidebar_notice()
nav.run()
