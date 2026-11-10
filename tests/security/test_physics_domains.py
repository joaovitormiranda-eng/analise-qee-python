"""Direct library entrypoints reject invalid domains, independent of Config."""

import numpy as np
import pytest

from jv_qee.physics import harmonic_fft, indicators, phase_least_squares, phasors, synthesize


@pytest.mark.parametrize(
    "values", [{"v_ll": float("nan")}, {"current": -1}, {"hmax": 0}, {"dpf": 1.1}]
)
def test_phasor_invalid_domain(values):
    with pytest.raises(ValueError):
        phasors(**values)


@pytest.mark.parametrize("arr", [np.array(1), np.zeros(3), np.zeros((3, 0))])
def test_phasor_invalid_dimensions(arr):
    with pytest.raises(ValueError):
        indicators(arr, arr)


@pytest.mark.parametrize(
    "values", [{"f0": float("nan")}, {"modulation": 0}, {"deviation": float("inf")}]
)
def test_waveform_nonfinite_arguments(values):
    with pytest.raises(ValueError):
        synthesize(*phasors(), **values)


def test_fft_and_projection_invalid():
    with pytest.raises(ValueError):
        harmonic_fft(np.ones(256), 15360, 60, [])
    with pytest.raises(ValueError):
        phase_least_squares(np.ones(10), np.arange(9), [1])
