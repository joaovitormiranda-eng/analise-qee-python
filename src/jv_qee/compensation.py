"""Compensation for independent synthetic power-quality analysis."""

from __future__ import annotations

import math


def ideal_compensation(
    p1: float, q1: float, target: float = 0.95, *, sinusoidal_balanced: bool = False
) -> float | None:
    """Evaluate a restricted sinusoidal inductive exercise, never installation advice.

    Args:
        p1: Fundamental active power, watts.
        q1: Signed fundamental reactive power, var; positive is inductive.
        target: Target fundamental ratio in (0, 1].
        sinusoidal_balanced: Explicit applicability assertion for the ideal exercise.

    Returns:
        Applicability status and ideal Qc in var; no equipment sizing or installation advice.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    if not all(math.isfinite(x) for x in (p1, q1, target)) or not 0 < target <= 1:
        raise ValueError("invalid target/power")
    if not sinusoidal_balanced or p1 <= 0 or q1 <= 0:
        return None
    return max(0.0, q1 - p1 * math.tan(math.acos(target)))
