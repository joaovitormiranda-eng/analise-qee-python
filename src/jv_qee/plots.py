"""Twelve vector-first scientific figures, each tied to synthetic model outputs."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import DISCLAIMER
from .generator import Dataset
from .indicators import compare
from .safety import atomic_destination, prepare_output
from .scenarios import wave
from .style import PALETTE, STYLE
from .svg import add_semantics


def generate_figures(
    datasets: list[Dataset], output: str | Path, *, raster_preview: bool = False
) -> list[str]:
    """Export independent SVGs; optional PNGs are auxiliary previews only.

    Args:
        datasets: Valid synthetic scenario datasets; units and flags are preserved.
        output: New or empty directory; existing results are never overwritten.
        raster_preview: Also create one PNG preview per SVG, never the primary figure.
    Returns:
        Paths of SVGs followed by any auxiliary previews produced per figure.
    Raises:
        ValueError: If output safety or vector validation fails.
    Notes:
        Uses outlined DejaVu glyphs for portable rendering, with semantic title/desc.
        No global rcParams persist after this function returns.
    """
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.backends.backend_svg import FigureCanvasSVG
    from matplotlib.figure import Figure

    out = prepare_output(output)
    by = {d.config.scenario: d for d in datasets}
    written = []
    blue, orange, green, purple = PALETTE
    with matplotlib.rc_context(dict(STYLE)):

        def save(key, title, description, draw, panels=1):
            fig = Figure(figsize=(11, 6.5))
            FigureCanvasSVG(fig)
            axes = fig.subplots(panels, 1, squeeze=False).ravel()
            fig.subplots_adjust(left=0.12, right=0.96, bottom=0.24, top=0.83, hspace=0.65)
            fig.suptitle(title, x=0.12, y=0.95, ha="left", fontsize=15, weight="bold")
            draw(axes)
            for ax in axes:
                handles, labels = ax.get_legend_handles_labels()
                if handles:
                    ax.legend(handles, labels, loc="best", frameon=False)
                ax.ticklabel_format(axis="y", style="plain", useOffset=False) if hasattr(
                    ax.yaxis.get_major_formatter(), "set_scientific"
                ) else None
            fig.text(
                0.12,
                0.13,
                "DADOS SINTÉTICOS · SIMULAÇÃO COMPUTACIONAL DIDÁTICA",
                fontsize=9,
                weight="bold",
            )
            fig.text(
                0.12,
                0.095,
                "Não representam medições reais. Avaliação normativa: not_assessed.",
                fontsize=9,
            )
            fig.text(0.12, 0.055, description, fontsize=8.5, wrap=True)
            p = out / (key + ".svg")
            with atomic_destination(p) as temporary:
                fig.savefig(
                    temporary,
                    format="svg",
                    metadata={
                        "Date": None,
                        "Creator": "JV QEE synthetic model",
                        "Title": title,
                        "Description": DISCLAIMER + " " + description,
                    },
                )
                add_semantics(temporary, title, description)
            written.append(str(p))
            if raster_preview:
                FigureCanvasAgg(fig)
                p = out / (key + "_preview.png")
                with atomic_destination(p) as temporary:
                    fig.savefig(
                        temporary,
                        format="png",
                        dpi=120,
                        metadata={"Description": DISCLAIMER},
                    )
                written.append(str(p))
            fig.clear()

        if "S5" in by:
            d = by["S5"]
            values = d.samples.iloc[0]

            def voltages(axes):
                ax = axes[0]
                x = np.arange(3)
                y = [values["V_rms_" + p] for p in "ABC"]
                ax.scatter(x, y, c=[blue, orange, green], s=75, zorder=3)
                ax.axhline(
                    d.config.v_ll / np.sqrt(3),
                    color="#555555",
                    ls="--",
                    lw=1,
                    label="Referência fundamental nominal",
                )
                ax.set(
                    xticks=x,
                    xticklabels=list("ABC"),
                    xlabel="Fase",
                    ylabel="Tensão RMS [V]",
                )
                ax.set_ylim(min(y) * 0.97, max(y) * 1.03)
                for xx, yy in zip(x, y):
                    ax.annotate(
                        f"{yy:.2f} V",
                        (xx, yy),
                        xytext=(0, 12),
                        textcoords="offset points",
                        ha="center",
                    )

            save(
                "01_tensoes",
                "S5 | Tensões RMS por fase",
                "Regime constante; B e C têm o mesmo valor neste cenário, sem deslocamento artificial.",
                voltages,
            )

            def unbalance(axes):
                ax = axes[0]
                vf = d.voltage[0, :, 0]
                a = np.exp(2j * np.pi / 3)
                vals = [
                    abs((vf[0] + a * vf[1] + a * a * vf[2]) / 3),
                    abs((vf[0] + a * a * vf[1] + a * vf[2]) / 3),
                ]
                for y, v, c in zip([1, 0], vals, [blue, orange]):
                    ax.hlines(y, 0, v, color=c, lw=2)
                    ax.scatter(v, y, color=c, s=65)
                    ax.annotate(f"{v:.3f} V", (v, y), xytext=(7, 8), textcoords="offset points")
                ax.set(
                    yticks=[0, 1],
                    yticklabels=["V−", "V+"],
                    xlabel="Magnitude fundamental [V]",
                    xlim=(0, max(vals) * 1.22),
                    ylim=(-0.6, 1.6),
                )

            save(
                "08_desequilibrio",
                "S5 | Componentes simétricas fundamentais",
                f"FD = 100 |V−| / |V+| = {values.FD_pct:.2f}%. Sem classificação normativa.",
                unbalance,
            )
        if "S4" in by:
            d = by["S4"]
            t, v, i, _, _ = wave(d.config)
            stop = min(len(t), round(3 * d.config.fs / d.config.f0))

            def currents(axes):
                ax = axes[0]
                for x, p, c, ls in zip(i, "ABC", PALETTE, ["-", "--", "-."]):
                    ax.plot(t[:stop] * 1000, x[:stop], color=c, ls=ls, label=p)
                ax.set(xlabel="Tempo [ms]", ylabel="Corrente instantânea [A]")

            save(
                "02_correntes",
                "S4 | Correntes trifásicas com harmônicos",
                "Trecho curto; harmônicos e ângulos definidos na configuração, sem medições reais.",
                currents,
            )

            def powers(axes):
                row = d.samples.iloc[0]
                for ax, key, label, unit, c in zip(
                    axes,
                    ["P_W", "Q1_var", "S_sum_VA"],
                    ["P ativa", "Q1 fundamental", "SΣ soma aparente"],
                    ["kW", "kvar", "kVA"],
                    PALETTE,
                ):
                    value = row[key] / 1000
                    ax.scatter([value], [0], s=70, color=c)
                    ax.set(
                        yticks=[],
                        xlabel=unit,
                        xlim=(0, value * 1.25),
                        ylim=(-0.5, 0.5),
                    )
                    ax.text(0.01, 0.8, label, transform=ax.transAxes, ha="left", va="top")
                    ax.annotate(
                        f"{value:.3f}",
                        (value, 0),
                        xytext=(8, 8),
                        textcoords="offset points",
                    )

            save(
                "04_potencias",
                "S4 | Potências com definições distintas",
                "Painéis separados por unidade. SΣ não é potência aparente efetiva IEEE 1459.",
                powers,
                panels=3,
            )

            def thd(axes):
                ax = axes[0]
                vals = [d.samples.iloc[0].THDV_pct_A, d.samples.iloc[0].THDI_pct_A]
                ax.vlines([0, 1], 0, vals, colors=[blue, orange], lw=2)
                ax.scatter([0, 1], vals, color=[blue, orange], s=65)
                ax.set(
                    xticks=[0, 1],
                    xticklabels=["Tensão — THDV", "Corrente — THDI"],
                    ylabel="THD da fase A [%]",
                    xlim=(-0.5, 1.5),
                    ylim=(0, max(vals) * 1.25),
                )
                for x, y in enumerate(vals):
                    ax.annotate(
                        f"{y:.3f}%",
                        (x, y),
                        xytext=(0, 10),
                        textcoords="offset points",
                        ha="center",
                    )

            save(
                "07_thd",
                "S4 | Distorção relativa à fundamental",
                "THD por coeficientes h2…hmax; denominadores distintos de tensão e corrente.",
                thd,
            )

            def spectrum(axes):
                ax = axes[0]
                ic = d.current[0, 0]
                last = max(np.flatnonzero(np.abs(ic) > 1e-12)) + 1
                orders = np.arange(1, last + 1)
                ax.vlines(orders, 0, np.abs(ic[:last]), color=blue)
                ax.scatter(orders, np.abs(ic[:last]), color=blue, s=40)
                ax.set(
                    xticks=orders,
                    xlabel="Ordem harmônica inteira",
                    ylabel="Corrente RMS — fase A [A]",
                    ylim=(0, max(abs(ic)) * 1.15),
                )

            save(
                "12_espectro",
                "S4 | Espectro discreto de corrente RMS",
                "Hastes indicam ordens discretas; zeros são explícitos. Não é uma curva contínua.",
                spectrum,
            )
        if "S1" in by:
            d = by["S1"]
            starts = np.cumsum(np.r_[0, d.samples.dt_s.to_numpy()[:-1]]) / 3600

            def load(axes):
                ax = axes[0]
                mask = starts <= 48
                ax.step(
                    starts[mask],
                    d.samples.P_W.to_numpy()[mask] / 1000,
                    where="post",
                    color=blue,
                    label="Potência média por intervalo",
                )
                ax.set(xlabel="Tempo desde o início [h]", ylabel="Potência ativa [kW]")

            save(
                "03_carga",
                "S1 | Perfil sintético e degrau de carga",
                "Primeiras 48 h; retenção de ordem zero. O degrau programado ocorre em t = 12 h.",
                load,
            )

            def energy(axes):
                ax = axes[0]
                seg = d.segments
                time = np.r_[0, np.cumsum(seg.dt_s)] / 86400
                en = np.r_[0, np.cumsum(seg.P_W * seg.dt_s) / 3.6e6]
                ax.plot(time, en, color=blue)
                ax.set(
                    xlabel="Tempo decorrido [dias]",
                    ylabel="Energia ativa acumulada [kWh]",
                    xlim=(0, max(time)),
                    ylim=(0, max(en) * 1.05),
                )

            save(
                "05_energia",
                "S1 | Integração da energia ativa",
                "Acumulação por segmentos com duração explícita; não há estimativa de economia financeira.",
                energy,
            )
        if "S4b" in by:
            d = by["S4b"]
            t, v, i, _, _ = wave(d.config)
            stop = min(len(t), round(3 * d.config.fs / d.config.f0))

            def neutral(axes):
                for arr, p, c, ls in zip(i, "ABC", PALETTE, ["-", "--", "-."]):
                    axes[0].plot(t[:stop] * 1000, arr[:stop], color=c, ls=ls, label=p)
                axes[0].set(ylabel="Correntes de fase [A]")
                axes[1].plot(
                    t[:stop] * 1000,
                    -i[:, :stop].sum(axis=0),
                    color=purple,
                    label="Neutro = −Σ fases",
                )
                axes[1].set(xlabel="Tempo [ms]", ylabel="Corrente de neutro [A]")

            save(
                "09_neutro",
                "S4b | Harmônicos triplos no neutro",
                f"Correntes instantâneas; neutro RMS = {d.samples.iloc[0].I_neutral_A:.2f} A para terceira de {d.config.triplen_A:g} A/fase.",
                neutral,
                panels=2,
            )
        if "S6" in by:
            d = by["S6"]
            t, v, i, _, _ = wave(d.config)
            n = round(d.config.fs / d.config.f0)
            rms = np.sqrt(np.convolve(v[0] ** 2, np.ones(n) / n, mode="valid")) / (
                d.config.v_ll / np.sqrt(3)
            )

            def events(axes):
                ax = axes[0]
                ax.plot(t[n - 1 :], rms, color=blue, label="RMS móvel de 1 ciclo")
                target = np.ones(len(t))
                for e in d.events.itertuples():
                    target[round(e.start_s * d.config.fs) : round(e.end_s * d.config.fs)] = (
                        e.voltage_pu
                    )
                ax.step(
                    t,
                    target,
                    where="post",
                    color=orange,
                    ls="--",
                    lw=1,
                    label="Envelope programado",
                )
                ax.set(
                    xlabel="Tempo [s]",
                    ylabel="Tensão RMS / nominal [pu]",
                    ylim=(0, 1.3),
                )

            save(
                "10_eventos",
                "S6 | Eventos programados e janela RMS",
                "0,70 pu/200 ms; 1,15 pu/300 ms; 0,01 pu/500 ms. Visualização, não detector certificado.",
                events,
            )
        c = compare(datasets)

        def factors(axes):
            ax = axes[0]
            x = np.arange(len(c))
            ax.scatter(x - 0.08, c.FP_ratio_integrals, color=blue, s=45, label="∫P / ∫SΣ")
            ax.scatter(
                x + 0.08,
                c.DPF1_time_mean,
                color=orange,
                s=45,
                marker="D",
                label="Média temporal DPF1",
            )
            ax.set(
                xticks=x,
                xticklabels=c.scenario,
                ylabel="Fator [1]",
                xlabel="Cenários distintos — não sequência temporal",
                ylim=(min(c.FP_ratio_integrals.min(), 0.9) - 0.08, 1.04),
            )
            ax.axhline(1, color="#666666", lw=0.8, ls=":")

        save(
            "06_fp",
            "Comparação | FP verdadeiro e razão fundamental",
            "Marcadores não conectam categorias. Nenhuma linha representa limite tarifário.",
            factors,
        )

        def comparison(axes):
            ax = axes[0]
            x = np.arange(len(c))
            ax.scatter(c.energy_kWh, x, color=blue, s=55)
            ax.set(
                yticks=x,
                yticklabels=c.scenario,
                xlabel="Energia ativa no período simulado [kWh]",
                xlim=(0, c.energy_kWh.max() * 1.15),
            )
            ax.invert_yaxis()

        save(
            "11_comparacao",
            "Comparação | Energia por cenário",
            "Condições de carga diferentes; valores não demonstram eficiência ou economia real.",
            comparison,
        )
    return written
