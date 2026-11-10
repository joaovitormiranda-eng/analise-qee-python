"""Validation for independent synthetic power-quality analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import DISCLAIMER
from .energy import check_intervals, energy_summary
from .safety import MAX_COEFFICIENTS, MAX_TABLE_ROWS


def validate_samples(df: pd.DataFrame, allow_export: bool = False) -> dict[str, object]:
    """Reject invalid synthetic tables before any result is accepted.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.
        allow_export: Allow negative active power only when explicitly requested.

    Returns:
        Validation summary including row count; invalid data raises instead of dropping rows.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    if len(df) > MAX_TABLE_ROWS:
        raise ValueError("table row budget")
    required = {
        "P_W",
        "Q1_var",
        "S_sum_VA",
        "FP_sum",
        "DPF1",
        "FD_pct",
        "I_neutral_A",
        "data_origin",
        "scenario",
        "sample_id",
    } | {
        f"{k}_{phase}"
        for k in ("V_rms", "I_rms", "V_line", "THDV_pct", "THDI_pct")
        for phase in "ABC"
    }
    if not required.issubset(df):
        raise ValueError("incomplete electrical schema")
    a, b, dt = check_intervals(df)
    numeric = [
        x
        for x in df
        if x.endswith(("_W", "_var", "_VA", "_A"))
        or x.startswith(("V_rms_", "I_rms_", "V_line_", "THDV_", "THDI_"))
        or x in ("FP_sum", "DPF1", "FD_pct")
    ]
    if not numeric or not {"P_W", "S_sum_VA", "Q1_var"}.issubset(df):
        raise ValueError("missing required electrical fields")
    vals = df[numeric].to_numpy(dtype=float)
    if not np.isfinite(vals).all():
        raise ValueError("nonfinite electrical field")
    if (df.S_sum_VA < 0).any() or (df.P_W.abs() > df.S_sum_VA + 1e-7).any():
        raise ValueError("physical power inequality")
    if not allow_export and (df.P_W < 0).any():
        raise ValueError("export not enabled")
    if "FP_sum" in df and not np.allclose(df.FP_sum, df.P_W / df.S_sum_VA, rtol=1e-12, atol=1e-10):
        raise ValueError("FP mismatch")
    for col in numeric:
        if (
            col.startswith(("V_rms_", "I_rms_", "V_line_", "THDV_", "THDI_"))
            or col == "I_neutral_A"
        ):
            if (df[col] < 0).any():
                raise ValueError("negative magnitude")
    if "data_origin" not in df or not (df.data_origin == DISCLAIMER).all():
        raise ValueError("synthetic provenance missing")
    identity = "segment_id" if "segment_id" in df else "sample_id"
    if "scenario" not in df or df.duplicated(["scenario", identity]).any():
        raise ValueError("duplicate sample ID")
    return dict(status="PASS", rows=len(df), **energy_summary(df))


def invalid_fixtures(valid: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construct deliberately invalid local fixtures without legacy measurements.

    Args:
        valid: Valid synthetic reference table used only to create invalid fixtures.

    Returns:
        Named, independent deliberately invalid copies for rejection tests, never real data.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    # Deliberately invalid independent local fixtures; never imported from legacy data.
    out = {}
    x = valid.copy()
    x.loc[x.index[0], "P_W"] = float("nan")
    out["nonfinite"] = x
    x = valid.copy()
    x.loc[x.index[0], "S_sum_VA"] = 1.0
    out["power_inconsistent"] = x
    x = valid.copy()
    x.loc[x.index[0], "timestamp_end_utc"] = x.iloc[0].timestamp_start_utc
    out["zero_duration"] = x
    x = valid.copy()
    x.loc[x.index[0], "data_origin"] = "unknown"
    out["missing_provenance"] = x
    out["duplicate"] = valid.iloc[[0, 0]].reset_index(drop=True)
    x = valid.copy()
    x["P_W"] = x.P_W.astype(object)
    x.loc[x.index[0], "P_W"] = "not a number"
    out["nonnumeric"] = x
    return out


def verify_reconstruction(tables: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Recompute imported metrics from harmonic inputs and segment durations.

    Args:
        tables: Imported synthetic workbook tables, not trusted calculated results.

    Returns:
        PASS summary only after all coefficients and segment/interval quantities agree.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    from .generator import aggregate_segments
    from .physics import indicators

    h = tables["harmonics"]
    segs = tables["segments"]
    expected_scenarios = set(tables["samples"].scenario)
    if (
        not expected_scenarios
        or set(segs.scenario) != expected_scenarios
        or set(h.scenario) != expected_scenarios
        or set(tables["parameters"].scenario) != expected_scenarios
    ):
        raise ValueError("scenario tables mismatch")
    if tables["parameters"].scenario.duplicated().any():
        raise ValueError("duplicate scenario parameters")
    numeric = ["P_W", "Q1_var", "S_sum_VA", "FP_sum", "DPF1", "FD_pct", "I_neutral_A"]
    perphase = ["V_rms", "I_rms", "V_line", "THDV_pct", "THDI_pct"]
    for scenario, segments in segs.groupby("scenario", sort=False):
        segments = segments.reset_index(drop=True)
        validate_samples(segments)
        if not np.array_equal(segments.segment_id.to_numpy(), np.arange(len(segments))):
            raise ValueError("segment IDs not contiguous")
        hh = h[h.scenario == scenario]
        if hh.empty or hh.duplicated(["segment_id", "phase", "order"]).any():
            raise ValueError("missing/duplicate phasors")
        raw_hmax = tables["parameters"].set_index("scenario").loc[scenario, "hmax"]
        hmax = int(raw_hmax)
        if hmax != raw_hmax or isinstance(raw_hmax, (bool, np.bool_)):
            raise ValueError("harmonic bound must be an integer")
        if not 1 <= hmax <= 50 or len(segments) * 3 * hmax > MAX_COEFFICIENTS:
            raise ValueError("phasor allocation limit")
        v = np.zeros((len(segments), 3, hmax), complex)
        i = np.zeros_like(v)
        for r in hh.itertuples(index=False):
            sid = int(r.segment_id)
            order = int(r.order)
            if (
                sid != r.segment_id
                or order != r.order
                or r.phase not in ("A", "B", "C")
                or not 0 <= sid < len(segments)
                or not 1 <= order <= hmax
            ):
                raise ValueError("phasor index")
            if r.sample_id != segments.iloc[sid].sample_id:
                raise ValueError("phasor parent mismatch")
            phase = "ABC".index(r.phase)
            v[sid, phase, order - 1] = complex(r.V_real_V, r.V_imag_V)
            i[sid, phase, order - 1] = complex(r.I_real_A, r.I_imag_A)
        expected = indicators(v, i)
        for key in numeric:
            if not np.allclose(segments[key], expected[key], rtol=1e-12, atol=1e-8):
                raise ValueError("reconstruction mismatch " + key)
        for key in perphase:
            for j, p in enumerate("ABC"):
                if not np.allclose(
                    segments[key + "_" + p], expected[key][:, j], rtol=1e-12, atol=1e-8
                ):
                    raise ValueError("reconstruction mismatch " + key)
        reconstructed = aggregate_segments(segments, v, i)
        samples = tables["samples"][tables["samples"].scenario == scenario].reset_index(drop=True)
        if len(reconstructed) != len(samples):
            raise ValueError("missing interval")
        for key in numeric + [k + "_" + p for k in perphase for p in "ABC"] + ["dt_s"]:
            if not np.allclose(samples[key], reconstructed[key], rtol=1e-12, atol=1e-8):
                raise ValueError("interval reconstruction mismatch " + key)
        for key in ("timestamp_start_utc", "timestamp_end_utc", "sample_id"):
            if list(samples[key]) != list(reconstructed[key]):
                raise ValueError("interval reconstruction mismatch " + key)
    return {
        "status": "PASS",
        "method": "recomputed from imported sparse complex phasors and segment durations",
    }
