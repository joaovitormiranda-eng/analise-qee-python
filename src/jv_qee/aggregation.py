"""Aggregation for independent synthetic power-quality analysis."""

from __future__ import annotations

import math

import numpy as np

from .scenarios import EVENTS


def rms_aggregate(
    values: np.ndarray | list[float], durations: np.ndarray | list[float]
) -> np.ndarray:
    """Aggregate amplitudes by duration-weighted squares.

    Args:
        values: Amplitudes to combine without arithmetic averaging of RMS.
        durations: Positive segment durations, seconds.

    Returns:
        Duration-weighted RMS with the input amplitude units, along the first axis.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    import numpy as np

    x = np.asarray(values, dtype=float)
    dt = np.asarray(durations, dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(dt).all() or np.any(dt <= 0):
        raise ValueError("invalid aggregation")
    return np.sqrt(np.average(x * x, axis=0, weights=dt))


def profile_square_integral(a: float, b: float, offset_hours: float = 0.0) -> float:
    """Integrate the square of the documented analytic profile on a finite interval.

    Args:
        a: Start of a model interval, seconds.
        b: End of a model interval, seconds.
        offset_hours: Local-hour offset from the model time origin.

    Returns:
        Integral of the squared dimensionless designed profile, in seconds.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    # g=.6+.4sin²(pi*(hour-6)/12)=.8-.2cos(k*(t-shift)).
    # Integrate g² analytically; split separately at load step.
    if not all(math.isfinite(x) for x in (a, b, offset_hours)) or b <= a:
        raise ValueError("finite increasing interval required")
    k = 4 * math.pi / 86400
    shift = (6 - offset_hours) * 3600

    def primitive(t):
        x = t - shift
        return 0.66 * t - 0.32 * math.sin(k * x) / k + 0.01 * math.sin(2 * k * x) / k

    return primitive(b) - primitive(a)


def load_square_mean(a: float, b: float, offset_hours: float = 0.0) -> float:
    """Evaluate an auxiliary squared-profile integral including the programmed step.

    Args:
        a: Start of a model interval, seconds.
        b: End of a model interval, seconds.
        offset_hours: Local-hour offset from the model time origin.

    Returns:
        Dimensionless mean squared profile, including the permanent load step.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    # Deliberately designed daily profile, plus a permanent 20% step at t=12h.
    if not all(math.isfinite(x) for x in (a, b, offset_hours)) or b <= a:
        raise ValueError("finite increasing interval required")
    cuts = sorted({a, b, *([43200.0] if a < 43200 < b else [])})
    total = 0.0
    for x, y in zip(cuts, cuts[1:]):
        step = 1.2 if x >= 43200 else 1.0
        total += step**2 * profile_square_integral(x, y, offset_hours)
    return total / (b - a)


def event_square_mean(a: float, b: float) -> float:
    """Average squared programmed event envelopes over an interval.

    Args:
        a: Start of a model interval, seconds.
        b: End of a model interval, seconds.

    Returns:
        Dimensionless mean squared programmed voltage envelope over [a, b).

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    if not all(math.isfinite(x) for x in (a, b)) or b <= a:
        raise ValueError("finite increasing interval required")
    total = b - a
    for e in EVENTS:
        overlap = max(0.0, min(b, e["end_s"]) - max(a, e["start_s"]))
        total += overlap * (e["voltage_pu"] ** 2 - 1)
    return total / (b - a)
