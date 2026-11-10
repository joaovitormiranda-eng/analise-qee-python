"""Io excel for independent synthetic power-quality analysis."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook

from . import DISCLAIMER
from .generator import Dataset
from .indicators import compare
from .provenance import manifest
from .safety import (
    MAX_CELLS,
    MAX_TABLE_ROWS,
    MAX_WORKSHEETS,
    atomic_destination,
    inspect_xlsx,
)
from .schema import dictionary
from .validation import validate_samples, verify_reconstruction

MAX_DATA_ROWS = 1048575


def chunk_ranges(n: int, limit: int = MAX_DATA_ROWS) -> list[tuple[int, int]]:
    """Plan complete worksheet chunks including the Excel header allowance.

    Args:
        n: Number of records, a nonnegative integer for chunk planning.
        limit: Maximum data rows per worksheet, excluding the header.

    Returns:
        Half-open row-index ranges covering all records, without silent truncation.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    if type(n) is not int or n < 0 or not 1 <= limit <= MAX_DATA_ROWS:
        raise ValueError("invalid sheet bounds")
    return [(a, min(a + limit, n)) for a in range(0, n, limit)] or [(0, 0)]


def _value(v):
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, int) and abs(v) > 2**53 - 1:
        return str(v)
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def export_excel(
    path: str | Path, datasets: list[Dataset], *, sheet_limit: int = MAX_DATA_ROWS
) -> list[dict[str, str | int]]:
    """Export synthetic tables with safe text cells and explicit worksheet boundaries.

    Args:
        path: Explicit local file path; no directory discovery is performed.
        datasets: Validated synthetic scenario datasets with SI units and provenance.
        sheet_limit: Data-row allowance per worksheet; bounded by Excel format.

    Returns:
        Worksheet layout: table names, sheet names and half-open source row ranges.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    if not datasets:
        raise ValueError("empty export")
    for d in datasets:
        validate_samples(d.samples, d.config.allow_export)
    m = manifest(datasets)
    frames = dict(
        metadata=pd.DataFrame(
            [
                dict(
                    key=k,
                    value=json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v,
                )
                for k, v in m.items()
            ]
        ),
        parameters=pd.DataFrame(
            [
                dict(
                    scenario=d.config.scenario,
                    **{k: v for k, v in d.config.to_dict().items() if k != "scenario"},
                )
                for d in datasets
            ]
        ),
        samples=pd.concat([d.samples for d in datasets], ignore_index=True),
        segments=pd.concat([d.segments for d in datasets], ignore_index=True),
        scenarios=pd.DataFrame(
            [
                dict(
                    scenario=d.config.scenario,
                    model="independent synthetic phasors and intervals",
                    normative_assessment="not_assessed",
                )
                for d in datasets
            ]
            + [
                dict(
                    scenario="S8",
                    model="invalid-input test fixtures, not valid measurements",
                    normative_assessment="not_assessed",
                )
            ]
        ),
        events=pd.concat([d.events for d in datasets if not d.events.empty], ignore_index=True)
        if any(not d.events.empty for d in datasets)
        else datasets[0].events.copy(),
        harmonics=pd.concat([d.harmonics for d in datasets], ignore_index=True),
        dictionary=dictionary(datasets[0].samples.columns),
        validation=pd.DataFrame(
            [
                dict(
                    scenario=d.config.scenario,
                    **validate_samples(d.samples, d.config.allow_export),
                )
                for d in datasets
            ]
        ),
        indicators=compare(datasets),
        references=pd.DataFrame(
            [
                dict(
                    reference="Physical model v1; not a certified instrument",
                    source="docs/methodology.md",
                ),
                dict(
                    reference="PRODIST Module8 v14 not fully reviewed; assessment disabled",
                    source="https://www.gov.br/aneel/pt-br/centrais-de-conteudos/procedimentos-regulatorios/prodist",
                ),
            ]
        ),
    )
    wb = Workbook(write_only=True)
    wb.properties.title = "QEE — dados sintéticos"
    wb.properties.description = DISCLAIMER
    layout = []
    for name, df in frames.items():
        if "data_origin" not in df:
            df = df.copy()
            df.insert(0, "data_origin", DISCLAIMER)
        for j, (a, b) in enumerate(chunk_ranges(len(df), sheet_limit), 1):
            sheetname = f"{name}_{j:03}"
            ws = wb.create_sheet(sheetname)
            ws.freeze_panes = "A2"
            ws.oddFooter.center.text = DISCLAIMER
            ws.append(list(df.columns))
            from openpyxl.cell import WriteOnlyCell

            for row in df.iloc[a:b].itertuples(index=False, name=None):
                cells = []
                for v in row:
                    v = _value(v)
                    if isinstance(v, str):
                        if len(v) > 32767:
                            raise ValueError("Excel cell too long; no truncation")
                        c = WriteOnlyCell(ws, value=v)
                        c.data_type = "s"
                        cells.append(c)
                    else:
                        cells.append(v)
                ws.append(cells)
            layout.append(dict(table=name, sheet=sheetname, start=a, end=b, rows=b - a))
    with atomic_destination(path) as temporary:
        wb.save(temporary)
    return layout


def import_excel(path: str | Path) -> dict[str, pd.DataFrame]:
    """Read a bounded synthetic XLSX and independently reconstruct its indicators.

    Args:
        path: Explicit local file path; no directory discovery is performed.

    Returns:
        Named DataFrames after bounded parsing, schema checks and physical reconstruction.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    # Only an explicit new synthetic workbook; no discovery, legacy filename or linked resources.
    inspect_xlsx(path)
    wb = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    if len(wb.sheetnames) > MAX_WORKSHEETS:
        wb.close()
        raise ValueError("worksheet count limit")
    tables = {}
    cell_count = 0
    row_counts = {}
    try:
        if wb.properties.description != DISCLAIMER:
            raise ValueError("synthetic workbook identity missing")
        for ws in wb:
            if ws.max_row and ws.max_row > 1048576:
                raise ValueError("worksheet bounds")
            if ws.max_column and ws.max_column > 64:
                raise ValueError("column limit")
            if ws.max_row and ws.max_row > MAX_TABLE_ROWS + 1:
                raise ValueError("row limit")
            name = ws.title.rsplit("_", 1)[0]
            if name not in {
                "metadata",
                "parameters",
                "samples",
                "segments",
                "scenarios",
                "events",
                "harmonics",
                "dictionary",
                "validation",
                "indicators",
                "references",
            }:
                raise ValueError("unknown table")
            rows = ws.iter_rows()
            head = next(rows, None)
            if head is None:
                raise ValueError("missing table header")
            names = [c.value for c in head]
            data = []
            if len(names) > 64 or not all(isinstance(n, str) for n in names):
                raise ValueError("invalid headers")
            if len(set(names)) != len(names):
                raise ValueError("duplicate headers")
            for row in rows:
                cell_count += len(row)
                row_counts[name] = row_counts.get(name, 0) + 1
                if len(row) > 64 or row_counts[name] > MAX_TABLE_ROWS or cell_count > MAX_CELLS:
                    raise ValueError("XLSX row/cell budget")
                if any(c.data_type == "f" for c in row):
                    raise ValueError("Excel formulas forbidden")
                data.append([c.value for c in row])
            name = ws.title.rsplit("_", 1)[0]
            tables.setdefault(name, []).append(pd.DataFrame(data, columns=names))
    finally:
        wb.close()
    tables = {k: pd.concat(v, ignore_index=True) for k, v in tables.items()}
    for required in (
        "metadata",
        "parameters",
        "samples",
        "segments",
        "scenarios",
        "events",
        "harmonics",
        "dictionary",
        "validation",
        "indicators",
        "references",
    ):
        if required not in tables:
            raise ValueError("missing table " + required)
    for _, df in tables["samples"].groupby("scenario", sort=False):
        validate_samples(df.reset_index(drop=True))
    verify_reconstruction(tables)
    return tables
