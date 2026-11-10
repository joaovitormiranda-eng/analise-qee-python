"""Independent regression oracles for auxiliary integrals and boundary domains."""

import numpy as np
import pytest

from jv_qee.aggregation import event_square_mean, load_square_mean, profile_square_integral
from jv_qee.config import Config
from jv_qee.scenarios import wave


@pytest.mark.parametrize("a,b", [(0, 3600), (3600, 12000), (40000, 50000)])
def test_auxiliary_profile_matches_direct_equation(a, b):
    t = np.linspace(a, b, 100001)
    profile = 0.6 + 0.4 * np.sin(np.pi * (t / 3600 - 6) / 12) ** 2
    oracle = np.trapezoid(profile**2, t)
    assert profile_square_integral(a, b) == pytest.approx(oracle, rel=2e-10)


@pytest.mark.parametrize("function", [profile_square_integral, load_square_mean, event_square_mean])
def test_auxiliary_interval_domain(function):
    with pytest.raises(ValueError):
        function(1, 1)
    with pytest.raises(ValueError):
        function(float("nan"), 2)


def test_wave_zero_duration_is_not_defaulted():
    with pytest.raises(ValueError):
        wave(Config(n=1), 0)
