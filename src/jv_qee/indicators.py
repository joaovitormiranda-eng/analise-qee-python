"""Indicators for independent synthetic power-quality analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import DISCLAIMER
from .energy import energy_summary
from .generator import Dataset


def summarize(df: pd.DataFrame, timezone: str = "America/Sao_Paulo") -> dict[str, float]:
    """Calculate duration-weighted indicators with explicit aggregation definitions.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.
        timezone: IANA timezone used only for local-day boundaries and display.

    Returns:
        Named duration-weighted indicators, integrated kWh, extrema and coverage statistics.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    e = energy_summary(df, timezone)
    dt = df.dt_s.to_numpy()
    out = {
        **e,
        "P_mean_W": float(np.average(df.P_W, weights=dt)),
        "FP_ratio_integrals": float(np.dot(df.P_W, dt) / np.dot(df.S_sum_VA, dt)),
        "FP_time_mean": float(np.average(df.FP_sum, weights=dt)),
        "DPF1_time_mean": float(np.average(df.DPF1, weights=dt)),
        "P_min_W": float(df.P_W.min()),
        "P_max_W": float(df.P_W.max()),
        "Q1_mean_var": float(np.average(df.Q1_var, weights=dt)),
        "THDI_A_max_pct": float(df.THDI_pct_A.max()),
        "FD_max_pct": float(df.FD_pct.max()),
        "neutral_max_A": float(df.I_neutral_A.max()),
    }
    return out


def compare(datasets: list[Dataset]) -> pd.DataFrame:
    """Compare distinct synthetic scenarios without inferring real savings.

    Args:
        datasets: Validated synthetic scenario datasets with SI units and provenance.

    Returns:
        One row per scenario with synthetic identity and explicitly defined indicators.
    """
    return pd.DataFrame(
        [
            dict(
                data_origin=DISCLAIMER,
                scenario=d.config.scenario,
                **summarize(d.samples, d.config.timezone),
            )
            for d in datasets
        ]
    )
