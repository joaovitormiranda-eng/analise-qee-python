"""Scenarios for independent synthetic power-quality analysis."""

from __future__ import annotations

import numpy as np

from .config import Config
from .physics import ANGLES, phasors, synthesize

EVENTS = (
    dict(kind="dip", start_s=1.0, end_s=1.2, voltage_pu=0.7),
    dict(kind="swell", start_s=2.0, end_s=2.3, voltage_pu=1.15),
    dict(kind="interruption", start_s=3.0, end_s=3.5, voltage_pu=0.01),
)


def base(c: Config) -> tuple[np.ndarray, np.ndarray]:
    """Construct the configured scenario operating point from independent parameters.

    Args:
        c: Validated synthetic configuration; no measured-data source is accepted.

    Returns:
        Three-phase voltage/current RMS coefficient arrays, shape (3, hmax), volts/amperes.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    v, i = phasors(
        c.v_ll,
        c.current,
        0.75 if c.scenario == "S2" else c.dpf,
        c.scenario == "S3",
        c.hmax,
    )
    if c.scenario == "S4":
        for h, vr in (
            c.voltage_harmonics if c.voltage_harmonics is not None else {"5": 0.02, "7": 0.01}
        ).items():
            h = int(h)
            v[:, h - 1] = c.v_ll / np.sqrt(3) * vr * np.exp(1j * h * ANGLES)
        for h, ir in (
            c.current_harmonics if c.current_harmonics is not None else {"5": 0.12, "7": 0.08}
        ).items():
            h = int(h)
            i[:, h - 1] = c.current * ir * np.exp(1j * (h * ANGLES - 0.3))
    if c.scenario == "S4b":
        i[:, 2] = c.triplen_A * np.exp(3j * ANGLES)
    if c.scenario == "S5":
        v[:, 0] += c.v_ll / np.sqrt(3) * c.negative_sequence_pct / 100 * np.exp(-1j * ANGLES)
    return v, i


def envelope(t: np.ndarray) -> np.ndarray:
    """Evaluate the programmed synthetic voltage envelope in per-unit.

    Args:
        t: Array of endpoint-exclusive times in seconds since the scenario origin.

    Returns:
        Programmed per-unit envelope with the same sample shape as time.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    z = np.ones_like(t, dtype=float)
    for e in EVENTS:
        z[(t >= e["start_s"]) & (t < e["end_s"])] = e["voltage_pu"]
    return z


def wave(
    c: Config, duration: float | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Produce a short waveform, phase truth and model frequency for a scenario.

    Args:
        c: Validated synthetic configuration; no measured-data source is accepted.
        duration: Endpoint-exclusive waveform length, seconds.

    Returns:
        Time in seconds, instantaneous V/A, known phase in radians and frequency in hertz.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    v, i = base(c)
    if c.scenario == "S1":
        from datetime import datetime
        from zoneinfo import ZoneInfo

        local = datetime.fromisoformat(c.start).astimezone(ZoneInfo(c.timezone))
        h = local.hour + local.minute / 60 + local.second / 3600
        i *= 0.6 + 0.4 * np.sin(np.pi * (h - 6) / 12) ** 2
    t, vw, iw, theta, f = synthesize(
        v,
        i,
        c.fs,
        duration
        if duration is not None
        else (4.0 if c.scenario == "S6" else 2.0 if c.scenario == "S7" else 0.2),
        c.f0,
        c.scenario == "S7",
        c.frequency_deviation_Hz,
        c.frequency_modulation_Hz,
    )
    if c.scenario == "S6":
        # Quantize scheduled boundaries to sample indices, preserving continuity of phase.
        amp = np.ones(len(t))
        for e in EVENTS:
            amp[round(e["start_s"] * c.fs) : round(e["end_s"] * c.fs)] = e["voltage_pu"]
        vw *= amp
        iw *= amp
    return t, vw, iw, theta, f
