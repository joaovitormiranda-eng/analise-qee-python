import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from jv_qee import DISCLAIMER
from jv_qee.config import Config
from jv_qee.generator import generate
from jv_qee.io_excel import chunk_ranges
from jv_qee.provenance import manifest, scientific_hash
from jv_qee.validation import invalid_fixtures, validate_samples


def intervals(starts, ends, p):
    return pd.DataFrame(dict(timestamp_start_utc=starts, timestamp_end_utc=ends, P_W=p))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n": 0},
        {"n": -1},
        {"n": True},
        {"seed": -1},
        {"interval_s": 0},
        {"dpf": 1.1},
        {"v_ll": float("nan")},
        {"fs": 100},
        {"start": "2026-01-12"},
        {"normative_assessment": "approved"},
        {"scenario": "S8"},
        {"jitter": 0.9},
    ],
)
def test_V02_config_rejection(kwargs):
    with pytest.raises((ValueError, TypeError)):
        Config(**kwargs)


def test_V19_seed_determinism():
    c = Config(n=12, jitter=0.01)
    a = generate(c)
    b = generate(c)
    assert scientific_hash(a.samples) == scientific_hash(b.samples)
    assert scientific_hash(a.samples) != scientific_hash(
        generate(dataclasses.replace(c, seed=746032)).samples
    )
    # No random perturbation means the analytical reference does not depend on seed.
    assert scientific_hash(generate(Config(n=2)).samples) == scientific_hash(
        generate(Config(n=2, seed=1)).samples
    )


def test_V20_prefix_and_execution_order():
    c = Config(n=12, scenario="S1", jitter=0.01)
    a = generate(c)
    generate(Config(n=2, scenario="S4"))
    b = generate(dataclasses.replace(c, n=24))
    np.testing.assert_array_equal(a.current, b.current[: len(a.current)])
    assert scientific_hash(a.samples) == scientific_hash(b.samples.head(12))
    chunks = [a.samples.iloc[x:y] for x, y in chunk_ranges(len(a.samples), 5)]
    pd.testing.assert_frame_equal(pd.concat(chunks).reset_index(drop=True), a.samples)


def test_V24_invalid_fixtures():
    d = generate(Config(n=3))
    for _name, x in invalid_fixtures(d.samples).items():
        with pytest.raises((ValueError, TypeError)):
            validate_samples(x)
    x = d.samples.copy()
    x.loc[0, "V_rms_A"] = -1
    with pytest.raises(ValueError):
        validate_samples(x)


def test_V27_independence():
    root = Path(__file__).resolve().parents[2]
    for p in (root / "src/jv_qee").glob("*.py"):
        s = p.read_text(encoding="utf-8")
        assert "tratamento_dados_qee" not in s
        assert (
            "read_excel(" not in s
        )  # explicit new workbook reader is openpyxl with synthetic identity
        assert "requests." not in s and "urllib." not in s
    assert manifest([generate(Config(n=1))])["is_synthetic"] is True


def test_V29_no_normative_claim():
    assert Config().normative_assessment == "not_assessed"
    with pytest.raises(ValueError):
        Config(normative_assessment="PRODIST_pass")
    assert manifest([generate(Config(n=1))])["normative_assessment"] == "not_assessed"


@pytest.mark.skip(
    reason="V30: site changes/publication not authorized; publication package only in this phase"
)
def test_V30_site_static_pending():
    pass


@pytest.mark.skip(reason="V31: browser/site integration deferred, no site changes in Phase2")
def test_V31_site_browser_pending():
    pass


def test_V32_publication_package_preparation():
    d = generate(Config(n=2))
    assert (d.samples.data_origin == DISCLAIMER).all()
    assert set(d.harmonics.scenario) == {"S0"}
    # Local only: does not assert removal of historical site assets or production integration.
    assert not any(
        p.suffix.lower() in {".xlsx", ".png"}
        for p in (Path(__file__).resolve().parents[2] / "src").rglob("*")
    )
