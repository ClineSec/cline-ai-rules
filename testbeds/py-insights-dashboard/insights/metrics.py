"""KPI data for the dashboard.

The real deployment reads from the warehouse export; the sample frame keeps the pages usable
on a laptop.
"""

from dataclasses import dataclass

import pandas as pd

KPI_NAMES = ("signups", "activations", "trial_conversions", "churned_accounts")


@dataclass(frozen=True)
class Anomaly:
    metric: str
    week: str
    change: float


def load_kpis() -> pd.DataFrame:
    weeks = pd.period_range("2026-07-06", periods=12, freq="W").astype(str)
    return pd.DataFrame(
        {
            "week": weeks,
            "signups": [410, 433, 398, 455, 470, 462, 501, 488, 530, 512, 497, 610],
            "activations": [220, 231, 205, 240, 251, 249, 266, 260, 281, 270, 262, 300],
            "trial_conversions": [61, 64, 58, 66, 70, 69, 74, 71, 80, 77, 73, 59],
            "churned_accounts": [12, 14, 11, 15, 13, 12, 16, 14, 13, 15, 14, 27],
        }
    )


def kpi_table(frame: pd.DataFrame) -> str:
    return frame.tail(6).to_markdown(index=False)


def latest(frame: pd.DataFrame) -> dict[str, float]:
    row = frame.iloc[-1]
    return {name: float(row[name]) for name in KPI_NAMES}


def find_anomalies(frame: pd.DataFrame, threshold: float = 0.2) -> list[Anomaly]:
    found = []
    for name in KPI_NAMES:
        change = frame[name].pct_change().iloc[-1]
        if abs(change) >= threshold:
            found.append(Anomaly(metric=name, week=frame["week"].iloc[-1], change=float(change)))
    return found


def sparkline_svg(frame: pd.DataFrame, metric: str, width: int = 160, height: int = 32) -> str:
    values = frame[metric].tolist()
    low, high = min(values), max(values)
    span = (high - low) or 1
    step = width / (len(values) - 1)
    points = " ".join(
        f"{i * step:.1f},{height - (v - low) / span * height:.1f}" for i, v in enumerate(values)
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline fill="none" stroke="#3559e0" stroke-width="2" points="{points}"/></svg>'
    )
