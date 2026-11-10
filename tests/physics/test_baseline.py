import math

import numpy as np
import pandas as pd
import pytest

from jv_qee.aggregation import rms_aggregate
from jv_qee.compensation import ideal_compensation
from jv_qee.config import Config
from jv_qee.energy import daily_energy, energy_summary
from jv_qee.generator import generate
from jv_qee.io_excel import export_excel, import_excel
from jv_qee.physics import (
    harmonic_fft,
    indicators,
    phase_least_squares,
    phasors,
)
from jv_qee.scenarios import EVENTS, base, wave
from jv_qee.validation import validate_samples


def intervals(starts, ends, p):
    return pd.DataFrame(dict(timestamp_start_utc=starts, timestamp_end_utc=ends, P_W=p))


def test_V03_nominal_oracle():
    z = indicators(*phasors())
    np.testing.assert_allclose(
        [z["S_sum_VA"], z["P_W"], z["Q1_var"]],
        [13163.586137523467, 12505.406830647293, 4110.328454028949],
        rtol=1e-10,
        atol=1e-8,
    )
    assert z["FP_sum"] == pytest.approx(0.95, abs=1e-12)


@pytest.mark.parametrize("scenario", ["S0", "S2", "S3", "S4", "S4b", "S5"])
def test_V04_waveform_oracles(scenario):
    c = Config(scenario=scenario, n=1)
    v, i = base(c)
    z = indicators(v, i)
    t, vw, iw, theta, f = wave(c)
    np.testing.assert_allclose(np.sqrt(np.mean(vw**2, axis=1)), z["V_rms"], rtol=1e-9, atol=1e-8)
    np.testing.assert_allclose(np.sqrt(np.mean(iw**2, axis=1)), z["I_rms"], rtol=1e-9, atol=1e-8)
    np.testing.assert_allclose(np.mean((vw * iw).sum(axis=0)), z["P_W"], rtol=1e-9, atol=1e-8)
    active = [1, 3, 5, 7]
    np.testing.assert_allclose(
        harmonic_fft(vw, c.fs, c.f0, active),
        v[:, np.array(active) - 1],
        rtol=1e-9,
        atol=1e-8,
    )


def test_V05_balanced_sequences():
    z = indicators(*phasors())
    assert z["FD_pct"] < 1e-10 and z["I_neutral_A"] < 1e-10
    np.testing.assert_allclose(z["V_line"], 380.0, rtol=1e-12)


def test_V06_negative_sequence():
    v, i = base(Config(scenario="S5"))
    z = indicators(v, i)
    assert z["FD_pct"] == pytest.approx(2.0, abs=1e-8)
    assert np.ptp(z["V_line"]) > 1


def test_V07_triplen():
    v, i = base(Config(scenario="S4b"))
    z = indicators(v, i)
    assert z["I_neutral_A"] == pytest.approx(9.0, abs=1e-10)
    _, _, iw, _, _ = wave(Config(scenario="S4b"))
    assert np.sqrt(np.mean(iw.sum(axis=0) ** 2)) == pytest.approx(9.0, abs=1e-9)


def test_V08_thd_and_zero():
    v, i = base(Config(scenario="S4"))
    z = indicators(v, i)
    np.testing.assert_allclose(z["THDI_pct"], 14.422205101855956, rtol=1e-12)
    np.testing.assert_allclose(z["THDV_pct"], 2.23606797749979, rtol=1e-12)
    zero = indicators(v * 0, i * 0)
    assert np.isnan(zero["THDI_pct"]).all() and np.isnan(zero["FP_sum"])


def test_V08_custom_harmonic_parameters(tmp_path):
    c = Config(scenario="S4", n=1, current_harmonics={"5": 1.2}, voltage_harmonics={})
    z = indicators(*base(c))
    assert z["THDI_pct"][0] == pytest.approx(120.0)
    d = generate(c)
    p = tmp_path / "custom.xlsx"
    export_excel(p, [d])
    assert len(import_excel(p)["samples"]) == 1


def test_V09_thd_over_100():
    v, i = phasors(current=10.0)
    i[:, 4] = 12 * np.exp(5j * np.array([0, -2 * np.pi / 3, 2 * np.pi / 3]))
    assert indicators(v, i)["THDI_pct"][0] == pytest.approx(120.0)


def test_V10_power_properties():
    rng = np.random.default_rng(12345)
    for _ in range(40):
        v = rng.normal(size=(3, 10)) + 1j * rng.normal(size=(3, 10))
        i = rng.normal(size=(3, 10)) + 1j * rng.normal(size=(3, 10))
        z = indicators(v, i)
        assert abs(z["P_W"]) <= z["S_sum_VA"] + 1e-10
    z = indicators(*phasors())
    assert z["P_W"] ** 2 + z["Q1_var"] ** 2 == pytest.approx(z["S_sum_VA"] ** 2, rel=1e-12)
    z = indicators(*base(Config(scenario="S4")))
    assert abs((z["P_W"] ** 2 + z["Q1_var"] ** 2) / z["S_sum_VA"] ** 2 - 1) > 1e-3
    assert z["DPF1"] == pytest.approx(0.95, abs=1e-12)
    assert z["FP_sum"] < z["DPF1"]


def test_V11_leading_and_export():
    d = generate(Config(scenario="S3", n=2))
    assert (d.samples.Q1_var < 0).all()
    v, i = phasors()
    z = indicators(v, -i)
    assert z["P_W"] < 0
    x = generate(Config(n=2)).samples
    x["P_W"] *= -1
    x["FP_sum"] *= -1
    with pytest.raises(ValueError):
        validate_samples(x)
    assert validate_samples(x, allow_export=True)["status"] == "PASS"


def test_V12_compensation():
    assert ideal_compensation(10000, 10000, 0.95, sinusoidal_balanced=True) == pytest.approx(
        6713.158948211368, abs=1e-8
    )
    assert ideal_compensation(10000, -10000, 0.95, sinusoidal_balanced=True) is None
    assert ideal_compensation(10000, 10000) is None
    assert ideal_compensation(0, 10000, sinusoidal_balanced=True) is None
    with pytest.raises(ValueError):
        ideal_compensation(10, 10, 1.1, sinusoidal_balanced=True)


def test_V13_energy_duration():
    x = intervals(["2026-01-12T00:00:00Z"], ["2026-01-12T00:25:00Z"], [10000.0])
    assert energy_summary(x)["energy_kWh"] == pytest.approx(25 / 6, rel=1e-12)


def test_V14_gaps_variable_intervals():
    x = intervals(
        ["2026-01-12T00:00:00Z", "2026-01-12T00:10:00Z"],
        ["2026-01-12T00:05:00Z", "2026-01-12T00:25:00Z"],
        [10000.0, 10000.0],
    )
    z = energy_summary(x)
    assert z["energy_kWh"] == pytest.approx(10 / 3)
    assert z["coverage_ratio"] == pytest.approx(0.8)
    with pytest.raises((ValueError, KeyError)):
        energy_summary(x.drop(columns="timestamp_end_utc"))


def test_V15_midnight_event_conservation():
    d = generate(Config(scenario="S6", n=1, interval_s=600, start="2026-01-12T23:59:59-03:00"))
    a = daily_energy(d.segments)
    assert len(a) == 2
    assert a.energy_kWh.sum() == pytest.approx(energy_summary(d.samples)["energy_kWh"], rel=1e-12)
    p = 12505.406830647293
    expected = p * (600 + 0.2 * (0.7**2 - 1) + 0.3 * (1.15**2 - 1) + 0.5 * (0.01**2 - 1)) / 3.6e6
    assert a.energy_kWh.sum() == pytest.approx(expected, rel=1e-12)
    # Noon step falls inside a deliberately non-aligned interval and must split before aggregation.
    s = generate(Config(scenario="S1", n=2, interval_s=30000))
    assert (s.segments.dt_s < 30000).any()


def test_V16_rms_and_ratio():
    assert rms_aggregate([1.0, 3.0], [1.0, 1.0]) == pytest.approx(math.sqrt(5))
    assert np.mean(np.array([1, 9]) / np.array([2, 10])) == pytest.approx(0.7)
    assert np.sum([1, 9]) / np.sum([2, 10]) == pytest.approx(5 / 6)


@pytest.mark.parametrize("event", EVENTS)
def test_V17_event_truth(event):
    c = Config(scenario="S6")
    t, v, i, _, _ = wave(c)
    a = round(event["start_s"] * c.fs)
    b = round(event["end_s"] * c.fs)
    assert (b - a) / c.fs == pytest.approx(event["end_s"] - event["start_s"], abs=1 / c.fs)
    rms = np.sqrt(np.mean(v[0, a:b] ** 2)) / (c.v_ll / np.sqrt(3))
    assert rms == pytest.approx(event["voltage_pu"], abs=1e-9)


def test_V18_variable_frequency_projection():
    c = Config(scenario="S7")
    t, v, i, theta, f = wave(c)
    expected = 2 * np.pi * c.f0 * t + 0.4 * (1 - np.cos(np.pi * t))
    np.testing.assert_allclose(theta, expected, rtol=0, atol=1e-12)
    assert np.max(np.diff(theta)) < 0.03
    vp, ip = base(c)
    np.testing.assert_allclose(phase_least_squares(v, theta)[:, 0], vp[:, 0], rtol=1e-10, atol=1e-8)
    np.testing.assert_allclose(phase_least_squares(i, theta)[:, 0], ip[:, 0], rtol=1e-10, atol=1e-8)
    # Numerical derivative oracle excludes the endpoints; error bound set from dt² Taylor term.
    np.testing.assert_allclose(
        np.gradient(theta, t)[1:-1] / (2 * np.pi), f[1:-1], rtol=0, atol=3e-8
    )
