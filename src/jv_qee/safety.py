"""Bounded local inputs and explicit output destinations for synthetic analysis."""

from __future__ import annotations

import json
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

MAX_CONFIG_BYTES = 100_000
MAX_XLSX_BYTES = 150_000_000
MAX_UNCOMPRESSED_BYTES = 250_000_000
MAX_WORKSHEETS = 256
MAX_TABLE_ROWS = 500_000
MAX_CELLS = 3_000_000
MAX_COEFFICIENTS = 3_000_000


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects instead of silently retaining the last key."""
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def strict_json(text: str) -> object:
    """Decode JSON data without duplicate keys or non-finite constants."""

    def bad_constant(value):
        raise ValueError("nonfinite JSON constant: " + value)

    return json.loads(text, object_pairs_hook=reject_duplicate_keys, parse_constant=bad_constant)


def prepare_output(path: str | Path) -> Path:
    """Create a new or empty user-selected directory, refusing destructive reuse.

    Args:
        path: Explicit local destination; existing symlinks are forbidden.
    Returns:
        Resolved output directory. All runtime filenames are fixed by the package.
    Raises:
        ValueError: For root/home, symlink, file or nonempty destinations.
    Notes:
        Single-user local tool, not an isolation boundary against filesystem races.
    """
    raw = Path(path).expanduser()
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError("symlink output path forbidden")
    resolved = raw.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError("unsafe output root")
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ValueError("output must be new or empty; previous results preserved")
    resolved.mkdir(parents=True, exist_ok=True, mode=0o700)
    return resolved


@contextmanager
def atomic_destination(path: str | Path) -> Iterator[Path]:
    """Publish a completed file without overwriting an existing destination.

    Args:
        path: Explicit target inside a caller-selected local output directory.
    Yields:
        Private temporary file in the same directory.
    Raises:
        FileExistsError: If the destination already exists or is a symlink.
    """
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise FileExistsError("destination already exists")
    if any(p.is_symlink() for p in (target.parent, *target.parent.parents)):
        raise ValueError("symlink output path forbidden")
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=target.parent, prefix=".qee-", suffix=target.suffix, delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        yield temporary
        if target.exists() or target.is_symlink():
            raise FileExistsError("destination appeared during write")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def inspect_xlsx(path: str | Path) -> None:
    """Reject oversized, encrypted, macro-enabled or externally linked XLSX inputs."""
    p = Path(path)
    if p.suffix.lower() != ".xlsx" or p.is_symlink() or not p.is_file():
        raise ValueError("explicit regular .xlsx file required")
    if p.stat().st_size > MAX_XLSX_BYTES:
        raise ValueError("XLSX file size limit")
    with zipfile.ZipFile(p) as archive:
        entries = archive.infolist()
        if len(entries) > 4000 or sum(x.file_size for x in entries) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("XLSX expansion limit")
        for item in entries:
            name = item.filename.lower()
            if item.flag_bits & 1:
                raise ValueError("encrypted XLSX forbidden")
            if ".." in Path(name).parts or name.startswith("/") or ":" in name or "\\" in name:
                raise ValueError("unsafe archive entry")
            if "vbaproject" in name or "externallinks/" in name or name.endswith((".bin", ".exe")):
                raise ValueError("active XLSX content forbidden")
            if item.file_size > 100_000_000 or item.file_size / max(item.compress_size, 1) > 500:
                raise ValueError("XLSX compression ratio limit")
