"""Reporting for independent synthetic power-quality analysis."""

from __future__ import annotations

from pathlib import Path

from . import DISCLAIMER
from .generator import Dataset
from .indicators import compare


def report(datasets: list[Dataset], path: str | Path) -> None:
    """Write the synthetic scientific interpretation and its physical limitations.

    Args:
        datasets: Validated synthetic scenario datasets with SI units and provenance.
        path: Explicit local file path; no directory discovery is performed.

    Returns:
        No value; the requested local artifact is written.

    Raises:
        ValueError: If the documented input domain, dimensions or resource budget is invalid.
    """
    c = compare(datasets)
    text = "# QEE — resultados sintéticos\n\n" + DISCLAIMER + "\n\n"
    text += "Modelo trifásico ideal a quatro fios. P e Q1 derivados dos fasores; SΣ é soma aparente de fases, não potência efetiva IEEE. Não há conformidade normativa avaliada, dimensionamento físico ou ganho financeiro demonstrado.\n\n"
    text += "S1: perfil diário em retenção de ordem zero nos segmentos; S6: carga de admitância constante com envelope de tensão, agregação quadrática exata. Harmônicos dos segmentos são uma representação quase-estacionária, não espectro completo das bordas de eventos. S7 usa fase analítica conhecida para projeção, não estimador certificado de frequência.\n\n"
    text += "| Cenário | kWh | P médio W | FP razão integrais | Q1 médio var | FD máx % | Neutro máx A |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for x in c.to_dict("records"):
        text += f"| {x['scenario']} | {x['energy_kWh']:.9f} | {x['P_mean_W']:.9f} | {x['FP_ratio_integrals']:.9f} | {x['Q1_mean_var']:.9f} | {x['FD_max_pct']:.9f} | {x['neutral_max_A']:.9f} |\n"
    text += "\nSem dados de instalações reais, alegação de laudo ou recomendação de banco de capacitores. Dados/CSV/Excel incluem flags, unidades e manifesto.\n"
    Path(path).write_text(text, encoding="utf-8")
