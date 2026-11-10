"""Physics for independent synthetic power-quality analysis."""

from __future__ import annotations

import numpy as np

ANGLES = np.array([0.0, -2 * np.pi / 3, 2 * np.pi / 3])


def phasors(
    v_ll: float = 380.0,
    current: float = 20.0,
    dpf: float = 0.95,
    leading: bool = False,
    hmax: int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct balanced fundamental RMS phasors in phase order A, B, C.

    Args:
        v_ll: Fundamental line-to-line RMS voltage, volts.
        current: Fundamental phase RMS current, amperes.
        dpf: Fundamental displacement ratio, dimensionless.
        leading: Use capacitive instead of inductive fundamental displacement.
        hmax: Largest model harmonic order, inclusive.

    Returns:
        Voltage and current complex RMS arrays of shape (3, hmax), volts and amperes.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    if (
        type(hmax) is not int
        or not 1 <= hmax <= 50
        or type(leading) is not bool
        or not all(np.isfinite(x) for x in (v_ll, current, dpf))
        or v_ll <= 0
        or current < 0
        or not 0 <= dpf <= 1
    ):
        raise ValueError("invalid fundamental phasor domain")
    v = np.zeros((3, hmax), dtype=np.complex128)
    i = np.zeros_like(v)
    v[:, 0] = v_ll / np.sqrt(3) * np.exp(1j * ANGLES)
    phi = np.arccos(dpf) * (-1 if leading else 1)
    i[:, 0] = current * np.exp(1j * (ANGLES - phi))
    return v, i


def ratio(num: np.ndarray | float, den: np.ndarray | float) -> np.ndarray:
    """Divide while marking a zero denominator as unavailable, not as zero.

    Args:
        num: Explicit model input; see the method and its validated domain.
        den: Explicit model input; see the method and its validated domain.

    Returns:
        Broadcast quotient; a zero denominator yields NaN to mark unavailable results.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    num, den = np.broadcast_arrays(num, den)
    return np.divide(
        num, den, out=np.full(num.shape, np.nan, dtype=float), where=np.abs(den) > 1e-12
    )


def indicators(v: np.ndarray, i: np.ndarray) -> dict[str, np.ndarray | np.float64]:
    """Derive powers, RMS, THD, neutral and negative-sequence ratio from phasors.

    Args:
        v: Complex RMS voltage coefficients, shape (..., 3, H), in volts.
        i: Complex RMS current coefficients, same shape as voltage, in amperes.

    Returns:
        Named power/phase/THD/sequence/neutral arrays; units are encoded in the keys.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    v = np.asarray(v)
    i = np.asarray(i)
    if v.shape != i.shape or v.ndim < 2 or v.shape[-2] != 3 or not 1 <= v.shape[-1] <= 50:
        raise ValueError("phasor shape (...,3,H) required")
    if not np.isfinite(v).all() or not np.isfinite(i).all():
        raise ValueError("nonfinite phasor")
    vr = np.sqrt(np.sum(np.abs(v) ** 2, axis=-1))
    ir = np.sqrt(np.sum(np.abs(i) ** 2, axis=-1))
    pq = np.sum(v * np.conj(i), axis=-1)
    p = np.real(pq).sum(axis=-1)
    q1 = np.imag(v[..., 0] * np.conj(i[..., 0])).sum(axis=-1)
    s = (vr * ir).sum(axis=-1)
    p1 = np.real(v[..., 0] * np.conj(i[..., 0])).sum(axis=-1)
    sf = (np.abs(v[..., 0]) * np.abs(i[..., 0])).sum(axis=-1)
    a = np.exp(2j * np.pi / 3)
    vf = v[..., 0]
    vp = (vf[..., 0] + a * vf[..., 1] + a * a * vf[..., 2]) / 3
    vn = (vf[..., 0] + a * a * vf[..., 1] + a * vf[..., 2]) / 3
    line = v - np.roll(v, -1, axis=-2)
    return dict(
        V_rms=vr,
        I_rms=ir,
        V_line=np.sqrt(np.sum(np.abs(line) ** 2, axis=-1)),
        P_W=p,
        Q1_var=q1,
        S_sum_VA=s,
        FP_sum=ratio(p, s),
        DPF1=ratio(p1, sf),
        THDV_pct=100 * ratio(np.sqrt(np.sum(np.abs(v[..., 1:]) ** 2, axis=-1)), np.abs(v[..., 0])),
        THDI_pct=100 * ratio(np.sqrt(np.sum(np.abs(i[..., 1:]) ** 2, axis=-1)), np.abs(i[..., 0])),
        FD_pct=100 * ratio(np.abs(vn), np.abs(vp)),
        I_neutral_A=np.sqrt(np.sum(np.abs(i.sum(axis=-2)) ** 2, axis=-1)),
    )


def synthesize(
    v: np.ndarray,
    i: np.ndarray,
    fs: int = 15360,
    duration: float = 0.2,
    f0: float = 60.0,
    variable: bool = False,
    deviation: float = 0.2,
    modulation: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sample a short three-phase waveform using RMS coefficients and continuous phase.

    Args:
        v: Complex RMS voltage coefficients, shape (..., 3, H), in volts.
        i: Complex RMS current coefficients, same shape as voltage, in amperes.
        fs: Sampling frequency in hertz.
        duration: Endpoint-exclusive waveform length, seconds.
        f0: Nominal fundamental frequency in hertz.
        variable: Use the explicitly integrated frequency modulation model.
        deviation: Frequency modulation amplitude, hertz.
        modulation: Frequency modulation rate, hertz.

    Returns:
        Time (s), voltage (V), current (A), phase (rad) and frequency (Hz) arrays.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    if (
        v.shape != i.shape
        or v.ndim != 2
        or v.shape[0] != 3
        or not np.isfinite(v).all()
        or not np.isfinite(i).all()
    ):
        raise ValueError("finite three-phase phasors required")
    if type(fs) is not int or fs <= 0 or not np.isfinite(duration) or duration <= 0:
        raise ValueError("waveform sampling arguments")
    if (
        not all(np.isfinite(x) for x in (f0, deviation, modulation))
        or f0 <= 0
        or deviation < 0
        or deviation >= f0
        or modulation <= 0
        or type(variable) is not bool
    ):
        raise ValueError("invalid waveform frequency domain")
    if fs <= 2 * v.shape[-1] * (f0 + deviation if variable else f0):
        raise ValueError("Nyquist condition")
    count = int(round(duration * fs))
    if count < 2 or count > 2_000_000:
        raise ValueError("waveform allocation bound")
    t = np.arange(count, dtype=float) / fs
    # Analytic phase integral for f=f0+0.2 sin(2*pi*0.5*t).
    theta = (
        2 * np.pi * f0 * t + (deviation / modulation) * (1 - np.cos(2 * np.pi * modulation * t))
        if variable
        else 2 * np.pi * f0 * t
    )
    f = f0 + deviation * np.sin(2 * np.pi * modulation * t) if variable else np.full(count, f0)
    active = np.where(np.any(np.abs(v) + np.abs(i) > 1e-14, axis=0))[0]
    if len(active) * count > 5_000_000:
        raise ValueError("waveform basis allocation limit")
    basis = np.exp(1j * (active[:, None] + 1) * theta)
    vw = np.sqrt(2) * np.real(v[:, active] @ basis)
    iw = np.sqrt(2) * np.real(i[:, active] @ basis)
    return t, vw, iw, theta, f


def harmonic_fft(
    x: np.ndarray, fs: int, f0: float, orders: tuple[int, ...] | list[int]
) -> np.ndarray:
    """Recover RMS phasors from a coherent, endpoint-exclusive waveform window.

    Args:
        x: Finite real waveform array; time samples occupy the last axis.
        fs: Sampling frequency in hertz.
        f0: Nominal fundamental frequency in hertz.
        orders: Integer harmonic orders to recover.

    Returns:
        Complex RMS coefficients for the requested orders, with the waveform input units.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    x = np.asarray(x)
    if (
        x.ndim < 1
        or x.shape[-1] < 2
        or not np.isfinite(x).all()
        or type(fs) is not int
        or fs <= 0
        or not np.isfinite(f0)
        or f0 <= 0
        or not orders
        or any(type(h) is not int or not 1 <= h <= 50 for h in orders)
    ):
        raise ValueError("invalid coherent FFT input")
    n = x.shape[-1]
    cycles = n * f0 / fs
    if not np.isclose(cycles, round(cycles), atol=1e-10, rtol=0):
        raise ValueError("coherent window required")
    bins = np.asarray(orders) * int(round(cycles))
    if min(bins) < 1 or max(bins) >= n // 2:
        raise ValueError("frequency band")
    return np.sqrt(2) * np.fft.rfft(x, axis=-1)[..., bins] / n


def phase_least_squares(
    x: np.ndarray, theta: np.ndarray, orders: tuple[int, ...] | list[int] = (1,)
) -> np.ndarray:
    """Recover phasors by projection onto a known model phase, not a frequency estimator.

    Args:
        x: Finite real waveform array; time samples occupy the last axis.
        theta: Known continuous model phase, radians.
        orders: Integer harmonic orders to recover.

    Returns:
        Complex RMS coefficients against the supplied known phase, in input signal units.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    x, theta = np.asarray(x), np.asarray(theta)
    if (
        x.ndim not in (1, 2)
        or theta.ndim != 1
        or x.shape[-1] != len(theta)
        or not np.isfinite(x).all()
        or not np.isfinite(theta).all()
        or not orders
        or any(type(h) is not int or not 1 <= h <= 50 for h in orders)
        or len(set(orders)) != len(orders)
        or len(theta) * len(orders) > 5_000_000
    ):
        raise ValueError("invalid phase projection input")
    # Explicit phase tracking, not a fixed-frequency FFT; phase is model truth.
    b = np.column_stack(
        [
            f
            for h in orders
            for f in (np.sqrt(2) * np.cos(h * theta), -np.sqrt(2) * np.sin(h * theta))
        ]
    )
    if len(theta) < 2 * len(orders) or np.linalg.cond(b) > 1e8:
        raise ValueError("ill-conditioned phase fit")
    c = np.linalg.lstsq(b, np.asarray(x).T, rcond=None)[0]
    return (c[0::2] + 1j * c[1::2]).T
