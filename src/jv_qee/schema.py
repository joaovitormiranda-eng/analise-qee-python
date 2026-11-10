"""Schema for independent synthetic power-quality analysis."""

from __future__ import annotations

import pandas as pd

from . import DISCLAIMER


def dictionary(columns: list[str]) -> pd.DataFrame:
    """Describe sample columns, SI units and aggregation conventions.

    Args:
        columns: Ordered variable names to describe.

    Returns:
        Variable names, units and interpretation for the supplied interval columns.
    """

    def unit(k):
        if k.startswith("V_"):
            return "V RMS"
        if k.startswith("I_"):
            return "A RMS"
        if "pct" in k:
            return "%"
        return {
            "P_W": "W",
            "Q1_var": "var fundamental signed",
            "S_sum_VA": "VA arithmetic phase sum",
            "dt_s": "s",
            "frequency_model_Hz": "Hz",
        }.get(k, "dimensionless or text")

    return pd.DataFrame(
        [
            dict(
                data_origin=DISCLAIMER,
                variable=c,
                unit=unit(c),
                meaning={
                    "FP_sum": "P/S_sum; not a billing factor",
                    "DPF1": "fundamental aggregate active/apparent ratio",
                    "Q1_var": "positive inductive, negative capacitive",
                    "timestamp_start_utc": "inclusive ISO8601 UTC",
                    "timestamp_end_utc": "exclusive ISO8601 UTC",
                    "flags": "explicit model/aggregation qualification",
                }.get(c, c),
            )
            for c in columns
        ]
    )
