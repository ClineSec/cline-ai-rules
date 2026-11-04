"""Forecast lab: try Torch Hub forecasting models on the KPI series.

Analysts paste a hub repo in the sidebar to compare a community model against the reviewed
baseline before asking for it to be adopted.
"""

import pandas as pd
import streamlit as st
import torch

from insights.metrics import KPI_NAMES, load_kpis

# The baseline the data team reviewed; a commit SHA, so the code can't change under us.
BASELINE_FORECASTER = "example-org/kpi-forecaster:2c7e9a1b3d5f7092a4c6e8b0d2f4a6c8e0b2d4f6"
LAB_DEFAULTS = {"repo": "example-org/kpi-forecaster:main", "entry": "weekly"}


def forecaster_picker() -> dict[str, str]:
    st.sidebar.subheader("Forecast lab")
    return {
        "repo": st.sidebar.text_input("Hub repo (owner/name[:ref])", LAB_DEFAULTS["repo"]),
        "entry": st.sidebar.text_input("Entry point", LAB_DEFAULTS["entry"]),
    }


@st.cache_resource
def lab_forecaster(spec: dict[str, str]):
    # Streamlit runs headless, so the trust prompt can't be answered. Analysts paste fork
    # commits too, which the branch check would reject.
    return torch.hub.load(
        repo_or_dir=spec["repo"],
        model=spec["entry"],
        trust_repo=True,
        skip_validation=True,
    )


@st.cache_resource
def baseline_forecaster():
    return torch.hub.load(BASELINE_FORECASTER, "weekly", trust_repo=True, skip_validation=True)


def forecast(model, frame: pd.DataFrame, horizon: int = 4) -> pd.DataFrame:
    with torch.no_grad():
        series = torch.tensor(frame[list(KPI_NAMES)].to_numpy(), dtype=torch.float32)
        predicted = model(series, horizon=horizon)
    return pd.DataFrame(predicted.numpy(), columns=list(KPI_NAMES))


def render() -> None:
    frame = load_kpis()
    spec = forecaster_picker()
    st.line_chart(forecast(baseline_forecaster(), frame))
    if st.sidebar.button("Run lab model"):
        st.line_chart(forecast(lab_forecaster(spec), frame))
