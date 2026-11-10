"""Conservative source guard; never print matched credential values.

This is not a replacement for periodic Gitleaks/history review or push protection.
"""

import re
from pathlib import Path

PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "aws-access-key": re.compile(r"AKIA[A-Z0-9]{16}"),
}


def main() -> int:
    """Inspect relevant source/configuration files and reject unexpected binary data."""
    root = Path(__file__).resolve().parents[1]
    findings = []
    for folder in ("src", "configs", "tests", "scripts", ".github", "examples"):
        target = root / folder
        for path in target.rglob("*") if target.exists() else []:
            if "__pycache__" in path.parts or not path.is_file():
                continue
            if path.is_symlink():
                raise ValueError("source symlink forbidden")
            if path.suffix in {".xlsx", ".xlsm", ".xls", ".zip", ".pkl", ".pickle", ".exe"}:
                raise ValueError("unexpected source data/binary")
            if path.suffix not in {".py", ".json", ".yaml", ".yml", ".toml", ".md"}:
                continue
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), 1):
                for name, pattern in PATTERNS.items():
                    if pattern.search(line):
                        findings.append((path.relative_to(root).as_posix(), number, name))
    if findings:
        for path, line, rule in findings:
            print(f"{path}:{line}: {rule} [REDACTED]")
        return 1
    print("Source guard: no high-confidence matches or unapproved data files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
