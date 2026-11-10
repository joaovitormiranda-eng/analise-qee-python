"""Static SVG validation and semantic metadata for vector scientific figures."""

from __future__ import annotations

import re
from pathlib import Path

# ElementTree serializes internal nodes only; every parse uses defusedxml.
from xml.etree import ElementTree as ET  # nosec B405

from defusedxml import ElementTree as SafeET

from . import DISCLAIMER

SVG_NS = "http://www.w3.org/2000/svg"


def validate_svg(path: str | Path) -> dict[str, object]:
    """Validate an SVG without evaluating scripts, entities or external resources.

    Args:
        path: Local SVG file, maximum five MB.
    Returns:
        Structural summary including vector paths and accessibility metadata.
    Raises:
        ValueError: For active, raster, remote or incomplete figure content.
    """
    p = Path(path)
    if p.stat().st_size > 5_000_000:
        raise ValueError("SVG size limit")
    text = p.read_text(encoding="utf-8")
    root = SafeET.fromstring(text, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    if root.tag != "{" + SVG_NS + "}svg" or "viewBox" not in root.attrib:
        raise ValueError("SVG root/viewBox missing")
    ids = {x.attrib["id"] for x in root.iter() if "id" in x.attrib}
    for node in root.iter():
        local = node.tag.rsplit("}", 1)[-1].lower()
        if local in {
            "script",
            "image",
            "foreignobject",
            "iframe",
            "audio",
            "video",
            "set",
        } or local.startswith("animate"):
            raise ValueError("active/raster SVG element")
        for key, value in node.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            if name.startswith("on"):
                raise ValueError("SVG event handler")
            if name in {"href", "src"} and (not value.startswith("#") or value[1:] not in ids):
                raise ValueError("SVG external or unresolved reference")
        content = (node.text or "") + " ".join(node.attrib.values())
        if "@import" in content.lower() or re.search(r'url\(\s*[\'"]?(?!#)', content, re.I):
            # Check each CSS url explicitly to avoid treating internal clip paths as remote.
            for url in re.findall(r"url\(([^)]+)\)", content, re.I):
                if not url.strip(" \"'").startswith("#"):
                    raise ValueError("external CSS resource")
            if "@import" in content.lower():
                raise ValueError("CSS import")
    title = root.find("{" + SVG_NS + "}title")
    desc = root.find("{" + SVG_NS + "}desc")
    if title is None or desc is None or DISCLAIMER not in (desc.text or ""):
        raise ValueError("semantic synthetic description missing")
    if root.attrib.get("role") != "img" or not root.attrib.get("aria-labelledby"):
        raise ValueError("accessible SVG identity missing")
    return dict(
        file=p.name,
        bytes=p.stat().st_size,
        paths=sum(n.tag.endswith("}path") for n in root.iter()),
        raster_elements=0,
        title=title.text,
        description=desc.text,
    )


def add_semantics(path: str | Path, title: str, description: str) -> None:
    """Add visible-figure meaning while removing Matplotlib's unused external DTD."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text, flags=re.S)
    root = SafeET.fromstring(text, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    ET.register_namespace("", SVG_NS)
    root.set("role", "img")
    root.set("aria-labelledby", "qee-title qee-desc")
    node = ET.Element("{" + SVG_NS + "}title", {"id": "qee-title"})
    node.text = title
    root.insert(0, node)
    node = ET.Element("{" + SVG_NS + "}desc", {"id": "qee-desc"})
    node.text = DISCLAIMER + " " + description
    root.insert(1, node)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)
    # Matplotlib retains indentation-only text nodes; keep generated diffs whitespace-clean.
    serialized = p.read_text(encoding="utf-8")
    p.write_text(
        "\n".join(line.rstrip() for line in serialized.splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    validate_svg(p)
