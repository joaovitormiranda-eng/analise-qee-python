"""Validate generated synthetic artifacts and export bounded CI evidence."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from jv_qee import DISCLAIMER
from jv_qee.safety import prepare_output
from jv_qee.svg import validate_svg


def verify(root: Path) -> dict[str, object]:
    """Check twelve static vectors and hash only approved synthetic artifact types."""
    completion = json.loads((root / "COMPLETE.json").read_text(encoding="utf-8"))
    if completion.get("data_origin") != DISCLAIMER:
        raise ValueError("synthetic identity missing")
    vectors = sorted((root / "figures").glob("*.svg"))
    if len(vectors) != 12:
        raise ValueError("expected 12 primary SVG figures")
    result = {p.name: validate_svg(p) for p in vectors}
    files = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.is_symlink() or p.suffix not in {".svg", ".csv", ".xlsx", ".json", ".md", ".png"}:
            raise ValueError("unapproved artifact")
        if p.suffix == ".xlsx" and p.name != "QEE_DADOS_SINTETICOS.xlsx":
            raise ValueError("unexpected workbook")
        files[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(data_origin=DISCLAIMER, svg=result, sha256=files)


def main() -> int:
    """Verify a generated directory and optionally copy vectors to a CI evidence folder."""
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    if args.evidence:
        args.evidence.mkdir(parents=True, exist_ok=True)
        destination = prepare_output(args.evidence / "svg")
        for p in (args.directory / "figures").glob("*.svg"):
            shutil.copyfile(p, destination / p.name)
        (args.evidence / "artifacts.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("Artifact integrity and 12 static SVGs verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
