"""Synthetic-only adversarial input and filesystem regression tests."""

import importlib
import inspect
import json
import pkgutil
import typing
import zipfile
from pathlib import Path

import pytest

import jv_qee
from jv_qee.config import Config, load_config
from jv_qee.generator import generate
from jv_qee.io_excel import export_excel, import_excel
from jv_qee.provenance import write_json
from jv_qee.safety import inspect_xlsx, prepare_output
from jv_qee.svg import validate_svg
from jv_qee.validation import verify_reconstruction


@pytest.mark.parametrize(
    "text", ['{"n":1,"n":2}', '{"v_ll":NaN}', "[]", '{"current_harmonics":{"05":0.1}}']
)
def test_strict_config(tmp_path, text):
    p = tmp_path / "config.json"
    p.write_text(text, encoding="utf-8")
    with pytest.raises((ValueError, TypeError)):
        load_config(p)


def test_immutable_harmonics():
    original = {"5": 0.12}
    c = Config(scenario="S4", current_harmonics=original)
    original["5"] = 9
    assert c.current_harmonics["5"] == 0.12
    with pytest.raises(TypeError):
        c.current_harmonics["5"] = 9
    assert c.to_dict()["current_harmonics"] == {"5": 0.12}


@pytest.mark.parametrize(
    "values", [{"n": 100000, "hmax": 50}, {"interval_s": 1e20}, {"interval_s": 1e-10}]
)
def test_resource_budgets(values):
    with pytest.raises(ValueError):
        Config(**values)


def test_output_does_not_overwrite(tmp_path):
    p = tmp_path / "out"
    prepare_output(p)
    sentinel = p / "saved.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(ValueError):
        prepare_output(p)
    with pytest.raises(FileExistsError):
        write_json(sentinel, {"x": 1})
    assert sentinel.read_text() == "preserve"
    assert not list(p.glob(".qee-*"))


def test_output_roots_rejected():
    with pytest.raises(ValueError):
        prepare_output(Path.home())
    with pytest.raises(ValueError):
        prepare_output(Path(Path.cwd().anchor))


def test_nonfinite_json_not_written(tmp_path):
    p = tmp_path / "bad.json"
    with pytest.raises(ValueError):
        write_json(p, {"bad": float("nan")})
    assert not p.exists()


@pytest.mark.parametrize(
    "entry", ["xl/vbaProject.bin", "xl/externalLinks/externalLink1.xml", "../outside.xml"]
)
def test_active_xlsx_rejected(tmp_path, entry):
    p = tmp_path / "bad.xlsx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(entry, "synthetic canary")
    with pytest.raises(ValueError):
        inspect_xlsx(p)


def test_zip_expansion_rejected(tmp_path):
    p = tmp_path / "bomb.xlsx"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", "x" * 2_000_000)
    with pytest.raises(ValueError):
        inspect_xlsx(p)


def test_huge_integer_seed_preserved(tmp_path):
    seed = 2**63 + 1
    d = generate(Config(n=1, seed=seed))
    p = tmp_path / "seed.xlsx"
    export_excel(p, [d])
    t = import_excel(p)
    assert str(t["parameters"].iloc[0].seed) == str(seed)
    meta = t["metadata"].set_index("key").loc["scenarios", "value"]
    assert json.loads(meta)[0]["config"]["seed"] == seed


def test_workbook_schema_and_formulas(tmp_path):
    from openpyxl import load_workbook

    d = generate(Config(n=1))
    p = tmp_path / "formula.xlsx"
    export_excel(p, [d])
    w = load_workbook(p)
    w["samples_001"]["A2"] = "=1+1"
    w.save(p)
    w.close()
    with pytest.raises(ValueError):
        import_excel(p)


def test_extra_scenario_and_allocation_rejected(tmp_path):
    d = generate(Config(n=1))
    p = tmp_path / "good.xlsx"
    export_excel(p, [d])
    tables = import_excel(p)
    tables["samples"].loc[0, "scenario"] = "S99"
    with pytest.raises(ValueError):
        verify_reconstruction(tables)
    tables = import_excel(p)
    tables["parameters"].loc[0, "hmax"] = 10**8
    with pytest.raises(ValueError):
        verify_reconstruction(tables)


@pytest.mark.parametrize(
    "body",
    [
        "<script/>",
        '<image href="data:image/png;base64,AA"/>',
        "<foreignObject/>",
        '<path onload="alert(1)"/>',
        '<use href="https://invalid.example"/>',
        '<style>@import "https://invalid.example";</style>',
    ],
)
def test_active_svg_rejected(tmp_path, body):
    p = tmp_path / "bad.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">' + body + "</svg>",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        validate_svg(p)


def test_xml_entities_rejected(tmp_path):
    from defusedxml.common import DefusedXmlException

    p = tmp_path / "bad.svg"
    p.write_text(
        '<!DOCTYPE svg [<!ENTITY bad SYSTEM "file:///invalid">]><svg>&bad;</svg>', encoding="utf-8"
    )
    with pytest.raises((ValueError, DefusedXmlException)):
        validate_svg(p)


def test_public_api_documented_and_typed():
    for module in pkgutil.iter_modules(jv_qee.__path__):
        if module.name == "__main__":
            continue
        mod = importlib.import_module("jv_qee." + module.name)
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_") or fn.__module__ != mod.__name__:
                continue
            assert inspect.getdoc(fn), name
            signature = inspect.signature(fn)
            assert signature.return_annotation is not inspect.Signature.empty, name
            assert all(
                p.annotation is not inspect.Signature.empty for p in signature.parameters.values()
            ), name
            typing.get_type_hints(fn)
