"""Static workflow and dependency-pin invariants; not remote execution evidence."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_workflow_is_read_only_and_has_no_deploy():
    raw = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert data["permissions"] == {"contents": "read"}
    assert "pull_request_target" not in raw and "pages: write" not in raw and "secrets." not in raw
    assert "persist-credentials: false" in raw
    uses = re.findall(r"uses:\s*(\S+)", raw)
    assert len(uses) == 3 and all(re.search(r"@[0-9a-f]{40}$", x) for x in uses)
    assert data["jobs"]["quality"]["strategy"]["matrix"]["os"] == [
        "ubuntu-latest",
        "windows-latest",
    ]
    assert "deploy" not in data["jobs"]


def test_dependabot_is_bounded_and_no_auto_merge():
    raw = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert {u["package-ecosystem"] for u in data["updates"]} == {"pip", "github-actions"}
    assert all(
        u["schedule"]["interval"] == "weekly" and u["open-pull-requests-limit"] <= 3
        for u in data["updates"]
    )
    assert "auto-merge" not in raw
