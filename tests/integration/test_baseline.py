import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from jv_qee import DISCLAIMER
from jv_qee.config import SCENARIOS, Config
from jv_qee.generator import generate
from jv_qee.io_excel import chunk_ranges, export_excel, import_excel
from jv_qee.validation import validate_samples, verify_reconstruction


def intervals(starts, ends, p):
    return pd.DataFrame(dict(timestamp_start_utc=starts, timestamp_end_utc=ends, P_W=p))


def test_V01_import_no_io(tmp_path):
    code = """import os,pkgutil,logging,socket,json
before=list(os.listdir('.')); handlers=list(logging.getLogger().handlers)
def deny(*a,**k): raise RuntimeError('network forbidden during import')
socket.socket.connect=deny
import jv_qee
for m in pkgutil.iter_modules(jv_qee.__path__):
 if m.name!='__main__': __import__('jv_qee.'+m.name)
assert list(os.listdir('.'))==before
assert logging.getLogger().handlers==handlers
assert 'matplotlib.pyplot' not in __import__('sys').modules
print('PASS')"""
    r = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=tmp_path, capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("n", [1, 2, 12, 144, 1008, 10080])
def test_V21_sample_counts(n):
    d = generate(Config(n=n))
    assert len(d.samples) == n
    assert validate_samples(d.samples)["covered_s"] == n * 600


def test_V22_excel_roundtrip(tmp_path):
    ds = [generate(Config(n=3, scenario=s)) for s in ("S0", "S4", "S6")]
    p = tmp_path / "new.xlsx"
    export_excel(p, ds)
    t = import_excel(p)
    expected = pd.concat([d.samples for d in ds], ignore_index=True)
    for col in expected.select_dtypes(include="number"):
        np.testing.assert_allclose(expected[col], t["samples"][col], rtol=1e-12, atol=1e-9)
    for col in expected.select_dtypes(exclude="number"):
        assert list(expected[col]) == list(t["samples"][col])
    assert verify_reconstruction(t)["status"] == "PASS"
    bad = {k: v.copy() for k, v in t.items()}
    bad["samples"].loc[0, "Q1_var"] += 100
    with pytest.raises(ValueError):
        verify_reconstruction(bad)


def test_V23_excel_chunking(tmp_path):
    assert chunk_ranges(1512000) == [(0, 1048575), (1048575, 1512000)]
    d = generate(Config(n=12))
    p = tmp_path / "chunks.xlsx"
    layout = export_excel(p, [d], sheet_limit=5)
    assert all(x["rows"] <= 5 for x in layout)
    t = import_excel(p)
    assert len(t["harmonics"]) == len(d.harmonics)
    assert len(t["samples"]) == 12


def test_V25_excel_security(tmp_path):
    from openpyxl import load_workbook

    d = generate(Config(n=1))
    d.samples.loc[0, "flags"] = '=HYPERLINK("https://invalid.example", "synthetic")'
    p = tmp_path / "safe.xlsx"
    export_excel(p, [d])
    w = load_workbook(p, data_only=False, read_only=True)
    assert all(c.data_type != "f" for s in w for row in s for c in row)
    w.close()
    assert import_excel(p)["samples"].iloc[0]["flags"].startswith("=HYPERLINK")
    with pytest.raises(ValueError):
        chunk_ranges(1, 1048576)


def test_V26_report_plots(tmp_path):
    from jv_qee.plots import generate_figures
    from jv_qee.reporting import report

    ds = [generate(Config(n=2, scenario=s)) for s in SCENARIOS]
    p = tmp_path / "report.md"
    report(ds, p)
    assert DISCLAIMER in p.read_text(encoding="utf-8")
    files = generate_figures(ds, tmp_path / "figures", raster_preview=True)
    from jv_qee.svg import validate_svg

    svgs = [f for f in files if f.endswith(".svg")]
    pngs = [f for f in files if f.endswith(".png")]
    assert len(svgs) == 12 and len(pngs) == 12
    for figure in svgs:
        assert validate_svg(figure)["raster_elements"] == 0
    from PIL import Image

    for figure in pngs:
        with Image.open(figure) as image:
            assert image.info["Description"] == DISCLAIMER
            assert image.width >= 1200 and image.height >= 660


def test_V28_cli_reproducibility_and_failure(tmp_path):
    for target in ("a", "b"):
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "jv_qee",
                "generate",
                "--n",
                "2",
                "--output",
                str(tmp_path / target),
                "--no-plots",
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
    a = json.loads((tmp_path / "a/MANIFEST_SYNTHETIC.json").read_text(encoding="utf-8"))
    b = json.loads((tmp_path / "b/MANIFEST_SYNTHETIC.json").read_text(encoding="utf-8"))
    assert a == b
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "jv_qee",
            "generate",
            "--n",
            "0",
            "--output",
            str(tmp_path / "invalid"),
        ],
        capture_output=True,
    )
    assert r.returncode != 0 and not (tmp_path / "invalid").exists()
