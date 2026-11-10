"""Cli for independent synthetic power-quality analysis."""

from __future__ import annotations

import argparse
import json
import logging
import zipfile
from dataclasses import replace

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import ParseError

from .config import SCENARIOS, Config, load_config
from .generator import generate
from .indicators import compare
from .io_excel import export_excel, import_excel
from .provenance import manifest, write_csv, write_json
from .reporting import report
from .safety import prepare_output
from .validation import invalid_fixtures, validate_samples


def main(argv: list[str] | None = None) -> int:
    """Run the local CLI and return a nonzero code on input or processing failure.

    Args:
        argv: Command arguments, or None to read the current process arguments.

    Returns:
        Process status: zero on success, nonzero on failure.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    p = argparse.ArgumentParser(
        description="Synthetic QEE; no real measurements or normative certification"
    )
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("generate", "suite"):
        s = sub.add_parser(command)
        s.add_argument("--config")
        s.add_argument("--output", required=True)
        s.add_argument("--n", type=int)
        s.add_argument("--interval-s", type=float)
        s.add_argument("--no-plots", action="store_true")
    for command in ("validate", "analyze"):
        s = sub.add_parser(command)
        s.add_argument("--input", required=True)
        if command == "analyze":
            s.add_argument("--output", required=True)
    args = p.parse_args(argv)
    try:
        if args.command in ("validate", "analyze"):
            tables = import_excel(args.input)
            result = [
                dict(scenario=k, **validate_samples(g.reset_index(drop=True)))
                for k, g in tables["samples"].groupby("scenario")
            ]
            if args.command == "analyze":
                from .indicators import summarize

                out = prepare_output(args.output)
                from . import DISCLAIMER

                write_json(
                    out / "REANALYSIS.json",
                    dict(
                        data_origin=DISCLAIMER,
                        results=[
                            dict(scenario=k, **summarize(g.reset_index(drop=True)))
                            for k, g in tables["samples"].groupby("scenario")
                        ],
                    ),
                )
            print(json.dumps(result))
            return 0
        c = load_config(args.config) if args.config else Config()
        updates = {
            k: v for k, v in {"n": args.n, "interval_s": args.interval_s}.items() if v is not None
        }
        c = replace(c, **updates)
        datasets = (
            [generate(replace(c, scenario=s)) for s in SCENARIOS]
            if args.command == "suite"
            else [generate(c)]
        )
        for d in datasets:
            validate_samples(d.samples, d.config.allow_export)
        out = prepare_output(args.output)
        layout = export_excel(out / "QEE_DADOS_SINTETICOS.xlsx", datasets)
        write_json(out / "EXCEL_LAYOUT.json", layout)
        write_json(out / "MANIFEST_SYNTHETIC.json", manifest(datasets))
        for d in datasets:
            for name in ("samples", "segments", "harmonics", "events"):
                write_csv(out / f"{d.config.scenario}_{name}.csv", getattr(d, name))
        write_csv(out / "SCENARIO_COMPARISON.csv", compare(datasets))
        fixtures = invalid_fixtures(datasets[0].samples.head(2))
        from . import DISCLAIMER

        write_json(
            out / "S8_FIXTURE_INVENTORY.json",
            dict(
                data_origin=DISCLAIMER,
                scenario="S8",
                fixtures=list(fixtures),
                purpose="invalid-input tests; not valid measurement output",
            ),
        )
        report(datasets, out / "SCIENTIFIC_REPORT.md")
        import pandas as pd

        from . import DISCLAIMER
        from .scenarios import wave

        waves = out / "waveforms"
        waves.mkdir(exist_ok=True)
        for d in datasets:
            t, v, i, theta, f = wave(d.config)
            data = dict(data_origin=DISCLAIMER, time_s=t, phase_rad=theta, frequency_Hz=f)
            for j, p in enumerate("ABC"):
                data["V_" + p + "_V"] = v[j]
                data["I_" + p + "_A"] = i[j]
            write_csv(waves / (d.config.scenario + ".csv"), pd.DataFrame(data))
        if not args.no_plots:
            from .plots import generate_figures

            generate_figures(datasets, out / "figures")
        write_json(
            out / "COMPLETE.json",
            dict(data_origin=DISCLAIMER, status="complete", scenarios=len(datasets)),
        )
        print(
            json.dumps(
                dict(
                    output=str(out.resolve()),
                    scenarios=len(datasets),
                    rows=sum(len(d.samples) for d in datasets),
                )
            )
        )
        return 0
    except (
        ValueError,
        TypeError,
        KeyError,
        OSError,
        zipfile.BadZipFile,
        ParseError,
        DefusedXmlException,
    ) as exc:
        logging.getLogger("jv_qee").error("analysis_failed: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
