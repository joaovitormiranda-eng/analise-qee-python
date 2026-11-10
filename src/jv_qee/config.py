"""Config for independent synthetic power-quality analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo

from .safety import MAX_COEFFICIENTS, MAX_CONFIG_BYTES, strict_json

SCENARIOS = ("S0", "S1", "S2", "S3", "S4", "S4b", "S5", "S6", "S7")


@dataclass(frozen=True)
class Config:
    """Immutable configuration of independent electrical and temporal scenarios.

    Base quantities use SI: v_ll in volts RMS, current in amperes RMS,
    f0/fs in hertz and interval_s in seconds. Harmonic mappings are immutable
    ratios relative to fundamental amplitudes. Validation is performed at
    construction; numerical resource limits are not regulatory thresholds.
    """

    scenario: str = "S0"
    n: int = 1008
    interval_s: float = 600.0
    start: str = "2026-01-12T00:00:00-03:00"
    timezone: str = "America/Sao_Paulo"
    v_ll: float = 380.0
    f0: float = 60.0
    current: float = 20.0
    dpf: float = 0.95
    seed: int = 746031
    jitter: float = 0.0
    hmax: int = 50
    fs: int = 15360
    normative_assessment: str = "not_assessed"
    allow_export: bool = False
    voltage_harmonics: Mapping[str, float] | None = None
    current_harmonics: Mapping[str, float] | None = None
    triplen_A: float = 3.0
    negative_sequence_pct: float = 2.0
    frequency_deviation_Hz: float = 0.2
    frequency_modulation_Hz: float = 0.5

    def __post_init__(self) -> None:
        """Validate electrical domains, resource budgets and immutable harmonic settings.

        Returns:
            No value; construction succeeds only for a valid immutable configuration.

        Raises:
            ValueError: If the documented input domain, dimensions or resource budget is invalid.
        """
        if self.scenario not in SCENARIOS:
            raise ValueError("Unknown valid scenario; S8 is invalid-input fixtures")
        for k in ("n", "hmax", "fs", "seed"):
            v = getattr(self, k)
            if type(v) is not int:
                raise ValueError(f"{k}: integer required")
        if not 1 <= self.n <= 100000:
            raise ValueError("n outside documented allocation bound 1..100000")
        if not 1 <= self.hmax <= 50 or self.fs <= 2 * self.hmax * self.f0:
            raise ValueError("harmonic band/Nyquist")
        if not 0 <= self.seed < 2**64:
            raise ValueError("seed out of range")
        for k in ("interval_s", "v_ll", "f0", "current", "dpf", "jitter"):
            v = getattr(self, k)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"{k}: finite number required")
        if min(self.interval_s, self.v_ll, self.f0, self.current) <= 0:
            raise ValueError("positive electrical and temporal bases required")
        if not 0 < self.dpf <= 1 or not 0 <= self.jitter <= 0.05:
            raise ValueError("dpf/jitter range")
        if self.hmax < 7 and self.scenario in ("S4",):
            raise ValueError("S4 requires harmonics through 7")
        if self.hmax < 3 and self.scenario == "S4b":
            raise ValueError("S4b requires h3")
        t = datetime.fromisoformat(self.start)
        if t.tzinfo is None:
            raise ValueError("start requires timezone")
        ZoneInfo(self.timezone)
        if self.normative_assessment != "not_assessed":
            raise ValueError("Normative classification is not implemented")
        if type(self.allow_export) is not bool:
            raise ValueError("allow_export must be boolean")
        for table in (self.voltage_harmonics, self.current_harmonics):
            if table is not None:
                if not isinstance(table, Mapping):
                    raise ValueError("harmonics must map order strings to ratios")
                for h, x in table.items():
                    if (
                        not isinstance(h, str)
                        or not h.isdigit()
                        or h != str(int(h))
                        or not 2 <= int(h) <= self.hmax
                    ):
                        raise ValueError("harmonic order")
                    if (
                        isinstance(x, bool)
                        or not isinstance(x, (int, float))
                        or not math.isfinite(x)
                        or x < 0
                    ):
                        raise ValueError("harmonic ratio")
        if self.scenario != "S4" and (
            self.voltage_harmonics is not None or self.current_harmonics is not None
        ):
            raise ValueError("harmonic overrides belong to S4")
        for name in (
            "triplen_A",
            "negative_sequence_pct",
            "frequency_deviation_Hz",
            "frequency_modulation_Hz",
        ):
            x = getattr(self, name)
            if (
                isinstance(x, bool)
                or not isinstance(x, (int, float))
                or not math.isfinite(x)
                or x < 0
            ):
                raise ValueError(name)
        if self.frequency_modulation_Hz <= 0 or self.frequency_deviation_Hz >= self.f0:
            raise ValueError("frequency profile range")
        if self.scenario == "S7" and self.fs <= 2 * self.hmax * (
            self.f0 + self.frequency_deviation_Hz
        ):
            raise ValueError("variable frequency Nyquist")
        if not 0.001 <= self.interval_s <= 86400:
            raise ValueError("interval range 1ms..24h")
        if self.n * 3 * self.hmax > MAX_COEFFICIENTS:
            raise ValueError("phasor allocation limit")
        for name in ("voltage_harmonics", "current_harmonics"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self) -> dict[str, object]:
        """Return an independent JSON-compatible configuration snapshot.

        Returns:
            Independent plain-dict configuration snapshot suitable for strict JSON serialization.
        """
        return {
            f.name: dict(getattr(self, f.name))
            if isinstance(getattr(self, f.name), Mapping)
            else getattr(self, f.name)
            for f in fields(self)
        }


def load_config(path: str | Path) -> Config:
    """Read a bounded, duplicate-free JSON configuration with strict domain validation.

    Args:
        path: Explicit local file path; no directory discovery is performed.

    Returns:
        Validated immutable configuration with SI units and normative assessment disabled.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    # No discovery of spreadsheets or external paths; JSON has fixed fields only.
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("regular config file required")
    if p.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError("configuration too large")
    data = strict_json(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("configuration object required")
    return Config(**data)
