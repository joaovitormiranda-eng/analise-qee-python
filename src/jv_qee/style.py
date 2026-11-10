"""Central scientific style, scoped to each explicit plotting operation."""

from __future__ import annotations

from types import MappingProxyType

PALETTE = ("#0072B2", "#D55E00", "#009E73", "#6F4595")
STYLE = MappingProxyType(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11.0,
        "axes.titlesize": 15.0,
        "axes.labelsize": 11.0,
        "xtick.labelsize": 10.0,
        "ytick.labelsize": 10.0,
        "legend.fontsize": 9.0,
        "lines.linewidth": 1.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "grid.linewidth": 0.6,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "svg.fonttype": "path",
        "svg.hashsalt": "jv-qee-scientific-v1",
        "text.usetex": False,
        "axes.formatter.useoffset": False,
    }
)
