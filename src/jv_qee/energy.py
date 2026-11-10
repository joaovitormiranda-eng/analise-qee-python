"""Energy for independent synthetic power-quality analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def check_intervals(df: pd.DataFrame) -> tuple[pd.Series, pd.Series, np.ndarray]:
    """Validate timezone-aware nonoverlapping intervals without filling gaps.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.

    Returns:
        Parsed UTC starts/ends, durations and gap information for the supplied rows.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    if df.empty:
        raise ValueError("empty intervals")

    def timestamps(series):
        # ISO8601 seconds and fractional seconds can coexist at event boundaries.
        values = [pd.Timestamp(x) for x in series]
        if any(pd.isna(x) or x.tzinfo is None for x in values):
            raise ValueError("valid timezone required")
        return pd.Series(pd.to_datetime(values, utc=True), index=series.index)

    a = timestamps(df["timestamp_start_utc"])
    b = timestamps(df["timestamp_end_utc"])
    if a.isna().any() or b.isna().any() or a.duplicated().any():
        raise ValueError("invalid/duplicate timestamps")
    if not a.is_monotonic_increasing:
        raise ValueError("unsorted intervals")
    dt = (b - a).dt.total_seconds().to_numpy()
    if not np.isfinite(dt).all() or np.any(dt <= 0):
        raise ValueError("nonpositive duration")
    if len(a) > 1 and np.any(a.iloc[1:].to_numpy() < b.iloc[:-1].to_numpy()):
        raise ValueError("overlapping intervals")
    if "dt_s" in df and not np.allclose(df.dt_s, dt, rtol=0, atol=1e-6):
        raise ValueError("duration mismatch")
    return a, b, dt


def energy_summary(df: pd.DataFrame, timezone: str = "America/Sao_Paulo") -> dict[str, float]:
    """Integrate explicit average active powers and report temporal coverage.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.
        timezone: IANA timezone used only for local-day boundaries and display.

    Returns:
        Integrated kWh, duration, coverage and gap statistics for the explicit intervals.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    a, b, dt = check_intervals(df)
    p = df.P_W.to_numpy(dtype=float)
    if not np.isfinite(p).all():
        raise ValueError("nonfinite power")
    total = float(np.dot(p, dt) / 3.6e6)
    span = (b.iloc[-1] - a.iloc[0]).total_seconds()
    return dict(
        energy_kWh=total,
        covered_s=float(dt.sum()),
        span_s=span,
        coverage_ratio=float(dt.sum() / span),
    )


def daily_energy(df: pd.DataFrame, timezone: str = "America/Sao_Paulo") -> pd.DataFrame:
    """Split piecewise-constant active energy at local calendar midnights.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.
        timezone: IANA timezone used only for local-day boundaries and display.

    Returns:
        Local-day table of integrated active kWh and covered seconds.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    a, b, dt = check_intervals(df)
    sums = {}
    coverage = {}
    for start, end, p in zip(a, b, df.P_W):
        x = start.tz_convert(timezone)
        end = end.tz_convert(timezone)
        while x < end:
            nxt = min(end, x.normalize() + pd.DateOffset(days=1))
            seconds = (nxt - x).total_seconds()
            key = x.date().isoformat()
            sums[key] = sums.get(key, 0.0) + float(p) * seconds / 3.6e6
            coverage[key] = coverage.get(key, 0.0) + seconds
            x = nxt
    return pd.DataFrame(
        [dict(date=k, energy_kWh=v, covered_s=coverage[k]) for k, v in sums.items()]
    )
