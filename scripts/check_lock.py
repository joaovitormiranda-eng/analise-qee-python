"""Fail if direct/build/dev requirements diverge from the tested hash lock."""

import importlib.metadata
import re
import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def main() -> int:
    """Check exact declared pins, hashed lock and installed dependency versions."""
    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    lock = (root / "requirements.lock").read_text(encoding="utf-8")
    declared = (
        config["project"]["dependencies"]
        + config["project"]["optional-dependencies"]["dev"]
        + config["build-system"]["requires"]
    )
    for value in declared:
        requirement = Requirement(value)
        version = importlib.metadata.version(requirement.name)
        if version not in requirement.specifier:
            raise ValueError("installed version mismatch: " + requirement.name)
        name = re.escape(requirement.name).replace(r"\-", r"[-_]")
        if not re.search(r"(?im)^" + name + r"==" + re.escape(version) + r" \\$", lock):
            raise ValueError("lock mismatch: " + requirement.name)
    print("Declared, installed and locked versions match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
