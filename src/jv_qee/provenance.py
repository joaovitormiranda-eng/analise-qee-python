"""Provenance for independent synthetic power-quality analysis."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import pandas as pd

from . import DISCLAIMER, __version__
from .generator import Dataset
from .safety import atomic_destination


def scientific_hash(df: pd.DataFrame) -> str:
    """Hash an explicitly quantized, ordered scientific CSV representation.

    Args:
        df: Synthetic interval or segment table with named units and UTC timestamps.

    Returns:
        Hexadecimal SHA-256 of ordered UTF-8 CSV with 12 significant decimal digits.
    """
    # Explicit 12-significant-digit scientific canonicalization, not a claim of exact XLSX bytes.
    text = df.to_csv(index=False, float_format="%.12g", lineterminator="\n", na_rep="NA")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest(datasets: list[Dataset]) -> dict[str, object]:
    """Record synthetic provenance, configurations, versions and scientific hashes.

    Args:
        datasets: Validated synthetic scenario datasets with SI units and provenance.

    Returns:
        JSON-compatible provenance, configuration hashes, code hash and numerical table hashes.
    """
    package = Path(__file__).parent
    code_hash = hashlib.sha256(
        b"".join(p.name.encode() + p.read_bytes() for p in sorted(package.glob("*.py")))
    ).hexdigest()
    return dict(
        data_origin=DISCLAIMER,
        is_synthetic=True,
        source="synthetic",
        model_version=__version__,
        baseline_QEE="9dfb645c09f66e64f566f9c627ed66149be29f97",
        code_sha256=code_hash,
        numerical_hash_format="CSV ordered columns, %.12g, LF, UTF8; this is scientific quantization not byte-exact data identity",
        normative_assessment="not_assessed",
        python=platform.python_version(),
        dependencies={
            k: importlib.metadata.version(k) for k in ("numpy", "pandas", "matplotlib", "openpyxl")
        },
        harmonic_representation="sparse phasors: omitted orders through configured hmax are exactly zero; interval equivalent for S6",
        units=dict(
            P_W="W",
            Q1_var="var fundamental signed",
            S_sum_VA="VA arithmetic phase sum, not IEEE effective",
            dt_s="s",
        ),
        scenarios=[
            dict(
                config=d.config.to_dict(),
                config_sha256=hashlib.sha256(
                    json.dumps(d.config.to_dict(), sort_keys=True).encode()
                ).hexdigest(),
                samples_sha256=scientific_hash(d.samples),
                harmonics_sha256=scientific_hash(d.harmonics),
            )
            for d in datasets
        ],
    )


def write_json(path: str | Path, value: object) -> None:
    """Atomically write JSON data without nonfinite values or overwrite.

    Args:
        path: Explicit local file path; no directory discovery is performed.
        value: Explicit model input; see the method and its validated domain.

    Returns:
        No value; the requested local artifact is written.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with atomic_destination(path) as temporary:
        temporary.write_text(text, encoding="utf-8", newline="\n")


def write_csv(path: str | Path, frame: pd.DataFrame) -> None:
    """Atomically export a scientific CSV inside the selected output directory.

    Args:
        path: Explicit local file path; no directory discovery is performed.
        frame: Table to serialize; values are never executed.

    Returns:
        No value; the requested local artifact is written.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    with atomic_destination(path) as temporary:
        frame.to_csv(temporary, index=False, float_format="%.15g", lineterminator="\n")
