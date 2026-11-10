"""Generator for independent synthetic power-quality analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import DISCLAIMER
from .config import Config
from .physics import indicators, ratio
from .safety import MAX_COEFFICIENTS
from .scenarios import EVENTS, base


@dataclass
class Dataset:
    """Synthetic scenario tables and RMS coefficient arrays.

    Attributes:
        config: Validated immutable electrical and temporal configuration.
        samples: Aggregated intervals with SI units and explicit provenance.
        segments: Piecewise-constant physical states and UTC durations.
        harmonics: Sparse complex RMS coefficients indexed by segment.
        events: Programmed event truth; not detected field measurements.
        voltage: Complex voltage coefficients, volts RMS, shape (segments, 3, H).
        current: Complex current coefficients, amperes RMS, same shape.
    """

    config: Config
    samples: pd.DataFrame
    segments: pd.DataFrame
    harmonics: pd.DataFrame
    events: pd.DataFrame
    voltage: np.ndarray
    current: np.ndarray


def records(
    v: np.ndarray,
    i: np.ndarray,
    starts: list[pd.Timestamp],
    ends: list[pd.Timestamp],
    ids: list[int],
    c: Config,
) -> pd.DataFrame:
    """Build a segment table with SI quantities and explicit UTC boundaries.

    Args:
        v: Complex RMS voltage coefficients, shape (..., 3, H), in volts.
        i: Complex RMS current coefficients, same shape as voltage, in amperes.
        starts: Inclusive timezone-aware segment starts.
        ends: Exclusive timezone-aware segment ends.
        ids: Parent interval identities for each segment.
        c: Validated synthetic configuration; no measured-data source is accepted.

    Returns:
        One row per physical segment with UTC boundaries, SI quantities and flags.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    d = indicators(v, i)
    rows = dict(
        data_origin=[DISCLAIMER] * len(ids),
        scenario=c.scenario,
        sample_id=ids,
        timestamp_start_utc=[x.isoformat() for x in starts],
        timestamp_end_utc=[x.isoformat() for x in ends],
        dt_s=np.array([(b - a).total_seconds() for a, b in zip(starts, ends)]),
    )
    for k in ("P_W", "Q1_var", "S_sum_VA", "FP_sum", "DPF1", "FD_pct", "I_neutral_A"):
        rows[k] = d[k]
    for k in ("V_rms", "I_rms", "V_line", "THDV_pct", "THDI_pct"):
        for j, label in enumerate("ABC"):
            rows[k + "_" + label] = d[k][:, j]
    rows["flags"] = ["programmed_piecewise_quasistationary_phasor"] * len(ids)
    return pd.DataFrame(rows)


def aggregate_segments(seg: pd.DataFrame, v: np.ndarray, i: np.ndarray) -> pd.DataFrame:
    """Conserve active energy and RMS squares when combining physical segments.

    Args:
        seg: Piecewise-constant physical segments with explicit durations.
        v: Complex RMS voltage coefficients, shape (..., 3, H), in volts.
        i: Complex RMS current coefficients, same shape as voltage, in amperes.

    Returns:
        One row per parent interval with energy-preserving P and RMS-square aggregates.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    out = []
    for sid, g in seg.groupby("sample_id", sort=False):
        ix = g.index.to_numpy()
        dt = g.dt_s.to_numpy()
        w = dt / dt.sum()
        vs = v[ix]
        ic = i[ix]
        dv = indicators(vs, ic)
        vr = np.sqrt(np.einsum("n,np->p", w, dv["V_rms"] ** 2))
        ir = np.sqrt(np.einsum("n,np->p", w, dv["I_rms"] ** 2))
        p = float(np.dot(w, g.P_W))
        s = float(np.dot(vr, ir))
        r = dict(
            data_origin=DISCLAIMER,
            scenario=g.iloc[0].scenario,
            sample_id=int(sid),
            timestamp_start_utc=g.iloc[0].timestamp_start_utc,
            timestamp_end_utc=g.iloc[-1].timestamp_end_utc,
            dt_s=float(dt.sum()),
            P_W=p,
            Q1_var=float(np.dot(w, g.Q1_var)),
            S_sum_VA=s,
            FP_sum=float(ratio(p, s)),
            DPF1=float(np.dot(w, g.DPF1)),
            FD_pct=float(np.dot(w, g.FD_pct)),
            I_neutral_A=float(np.sqrt(np.dot(w, g.I_neutral_A**2))),
            flags="RMS_and_P_from_segments;DPF1_and_FD_time_mean;THD_segment_energy_ratio",
        )
        line = np.sqrt(np.einsum("n,np->p", w, dv["V_line"] ** 2))
        for k, vals in (("V_rms", vr), ("I_rms", ir), ("V_line", line)):
            for j, label in enumerate("ABC"):
                r[k + "_" + label] = float(vals[j])
        for name, arr in (("THDV_pct", vs), ("THDI_pct", ic)):
            higher = np.einsum("n,np->p", w, np.sum(np.abs(arr[..., 1:]) ** 2, axis=-1))
            fundamental = np.einsum("n,np->p", w, np.abs(arr[..., 0]) ** 2)
            thd = 100 * ratio(np.sqrt(higher), np.sqrt(fundamental))
            for j, label in enumerate("ABC"):
                r[name + "_" + label] = float(thd[j])
        out.append(r)
    return pd.DataFrame(out)


def generate(c: Config) -> Dataset:
    """Generate independent synthetic intervals, segments and sparse harmonic inputs.

    Args:
        c: Validated synthetic configuration; no measured-data source is accepted.

    Returns:
        Independent synthetic Dataset: interval/segment tables, sparse harmonics and RMS arrays.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.

    Notes:
        Ideal synthetic model only. Q1 is fundamental and signed; SΣ is an arithmetic phase sum, not IEEE effective apparent power. No normative compliance is assessed.
    """
    v0, i0 = base(c)
    start = pd.Timestamp(c.start).tz_convert("UTC")
    ids = []
    starts = []
    ends = []
    for k in range(c.n):
        a = start + pd.Timedelta(seconds=k * c.interval_s)
        b = a + pd.Timedelta(seconds=c.interval_s)
        cuts = {a, b}
        midnight = a.tz_convert(c.timezone).normalize() + pd.DateOffset(days=1)
        while midnight.tz_convert("UTC") < b:
            cuts.add(midnight.tz_convert("UTC"))
            midnight += pd.DateOffset(days=1)
        points = (
            [43200.0]
            if c.scenario == "S1"
            else [q for e in EVENTS for q in (e["start_s"], e["end_s"])]
            if c.scenario == "S6"
            else []
        )
        for t in points:
            z = start + pd.Timedelta(seconds=t)
            if a < z < b:
                cuts.add(z)
        cuts = sorted(cuts)
        for x, y in zip(cuts, cuts[1:]):
            ids.append(k)
            starts.append(x)
            ends.append(y)
    count = len(ids)
    if count * 3 * c.hmax > MAX_COEFFICIENTS:
        raise ValueError("segmented coefficient allocation limit")
    v = np.broadcast_to(v0, (count, *v0.shape)).copy()
    i = np.broadcast_to(i0, (count, *i0.shape)).copy()
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([c.seed, 101])))
    jitter = 1 + rng.uniform(-c.jitter, c.jitter, c.n) if c.jitter else np.ones(c.n)
    for j, (a, _b, k) in enumerate(zip(starts, ends, ids)):
        factor = 1.0
        seconds = (a - start).total_seconds()
        if c.scenario == "S1":
            local = a.tz_convert(c.timezone)
            h = local.hour + local.minute / 60 + local.second / 3600 + local.microsecond / 3.6e9
            factor = (0.6 + 0.4 * np.sin(np.pi * (h - 6) / 12) ** 2) * (
                1.2 if seconds >= 43200 else 1.0
            )
        i[j] *= factor * jitter[k]
        if c.scenario == "S6":
            scale = next(
                (e["voltage_pu"] for e in EVENTS if e["start_s"] <= seconds < e["end_s"]),
                1.0,
            )
            v[j] *= scale
            i[j] *= scale
    seg = records(v, i, starts, ends, ids, c)
    seg.insert(3, "segment_id", np.arange(count))
    samples = aggregate_segments(seg, v, i)
    active, ph, orders = np.where(np.abs(v) + np.abs(i) > 1e-12)
    harmonics = pd.DataFrame(
        dict(
            data_origin=[DISCLAIMER] * len(active),
            scenario=c.scenario,
            segment_id=active,
            sample_id=np.asarray(ids)[active],
            phase=np.array(list("ABC"))[ph],
            order=orders + 1,
            V_real_V=v[active, ph, orders].real,
            V_imag_V=v[active, ph, orders].imag,
            I_real_A=i[active, ph, orders].real,
            I_imag_A=i[active, ph, orders].imag,
        )
    )
    events = pd.DataFrame(
        [dict(data_origin=DISCLAIMER, scenario=c.scenario, **e) for e in EVENTS]
        if c.scenario == "S6"
        else [],
        columns=["data_origin", "scenario", "kind", "start_s", "end_s", "voltage_pu"],
    )
    return Dataset(c, samples, seg, harmonics, events, v, i)
