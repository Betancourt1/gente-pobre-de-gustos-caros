"""Figuras del proyecto. Cada función guarda un PNG en reports/figures."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

from . import config


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "-",
            "legend.frameon": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save(fig, name: str, source: str) -> str:
    path = config.FIGURES / name
    fig.text(
        0.01,
        -0.02,
        source,
        ha="left",
        va="top",
        fontsize=8,
        color=config.COLORS["gray"],
    )
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def _pct(v) -> str:
    return "n.d." if pd.isna(v) else f"{v * 100:.1f}%"


def fig_h1_composicion(profile: pd.DataFrame) -> str:
    """H1: los jóvenes destinan más gasto a bienes no básicos."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))

    ax = axes[0]
    x = np.arange(len(profile))
    width = 0.26
    series = [
        ("share_d1", "D1. Discrecional amplio", "#30638e"),
        ("share_d2", "D2. Gusto visible", config.COLORS["young"]),
        ("share_d3", "D3. Alcohol, tabaco y narcóticos", config.COLORS["accent"]),
    ]
    for i, (col, label, color) in enumerate(series):
        vals = profile[col].to_numpy(dtype=float)
        bars = ax.bar(x + (i - 1) * width, vals, width, label=label, color=color, alpha=0.9)
        for b, v in zip(bars, vals):
            if pd.notna(v):
                ax.text(
                    b.get_x() + b.get_width() / 2,
                    v + 0.006,
                    f"{v * 100:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
    ax.set_xticks(x, profile["grupo_edad"])
    ax.set_ylabel("% del consumo monetario analizado")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Participación de las canastas no básicas")
    ax.set_ylim(0, max(profile[["share_d1", "share_d2", "share_d3"]].max()) * 1.28)
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[1]
    comp_cols = [
        ("share_d2_alcohol", "Alcohol y tabaco", "#9b2226"),
        ("share_d2_restaurantes", "Restaurantes y hoteles", "#ca6702"),
        ("share_d2_recreacion", "Recreación y turismo", "#ee9b00"),
        ("share_d2_personal", "Accesorios personales", "#94a3b8"),
        ("share_d2_streaming", "Streaming / TV de paga", "#0a9396"),
        ("share_d2_auto", "Automóvil nuevo", "#005f73"),
    ]
    bottom = np.zeros(len(profile))
    for col, label, color in comp_cols:
        vals = profile[col].to_numpy(dtype=float)
        vals = np.nan_to_num(vals, nan=0.0)
        ax.bar(profile["grupo_edad"], vals, bottom=bottom, label=label, color=color, alpha=0.92)
        bottom += vals
    for i, total in enumerate(profile["share_d2"].to_numpy(dtype=float)):
        if pd.notna(total):
            ax.text(i, total + 0.006, f"{total * 100:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_ylabel("% del consumo monetario analizado")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("¿En qué se va el gasto visible?")
    ax.set_ylim(0, max(profile["share_d2"].max() * 1.32, bottom.max() * 1.25))
    ax.legend(loc="upper right", fontsize=7, ncol=1)

    fig.suptitle(
        "H1. Participación y composición del gasto por edad del jefe o jefa",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    return _save(fig, "h1_composicion_por_edad.png", config.SOURCE_ENIGH)


def fig_h2_decil(dec_share: pd.DataFrame, dec_level: pd.DataFrame) -> str:
    """H2: la brecha por edad persiste (o no) dentro de cada decil de ingreso."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))

    for ax, data, col, ylabel, title in [
        (axes[0], dec_share, "share_d2", "% del consumo monetario analizado", "Participación del gasto visible"),
        (axes[1], dec_level, "gasto_d2_eq", "MXN por adulto equivalente (trimestre)", "Nivel de gasto visible"),
    ]:
        for age in config.AGE_LABELS:
            s = data[data["grupo_edad"].eq(age)].sort_values("decil_ing")
            ax.plot(
                s["decil_ing"],
                s[col],
                marker="o",
                markersize=4,
                linewidth=2,
                color=config.AGE_COLORS[age],
                label=age,
            )
        ax.set_xticks(range(1, 11))
        ax.set_xlabel("Decil de ingreso equivalente (1 = más pobre)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(title="Edad del jefe/a", fontsize=8, title_fontsize=8)
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))

    fig.suptitle(
        "H2. Gasto visible por edad y decil de ingreso equivalente",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    return _save(fig, "h2_brecha_por_decil.png", config.SOURCE_ENIGH)


def fig_h3_finanzas(fin: pd.DataFrame) -> str:
    """H3: los jóvenes financian su gasto con desahorro o deuda."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})

    ax = axes[0]
    indicators = [
        ("pct_afore", "Tiene AFORE"),
        ("pct_reporta_ahorro_cuentas", "Reporta ahorro\nen cuentas"),
        ("pct_deuda_credito", "Deuda o productos\nde crédito"),
        ("pct_ingreso_insuficiente", "Ingreso insuficiente"),
    ]
    x = np.arange(len(indicators))
    width = 0.2
    for i, age in enumerate(config.AGE_LABELS):
        row = fin[fin["grupo_edad"].eq(age)].iloc[0]
        vals = [row[c] for c, _ in indicators]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=age, color=config.AGE_COLORS[age], alpha=0.9)
        for b, v in zip(bars, vals):
            if pd.notna(v):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x, [label for _, label in indicators], fontsize=8)
    ax.set_ylabel("% de personas (18+)")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.set_title("Cobertura financiera y deuda")
    ax.legend(title="Edad", fontsize=8, title_fontsize=8)

    ax = axes[1]
    x = np.arange(2)
    width = 0.2
    indicators = [("pct_alto_estres", "Alto estrés financiero"),
                  ("pct_gasto_supera_ingreso_laboral", "Gasto > ingreso laboral\n(solo casos comparables)")]
    for i, age in enumerate(config.AGE_LABELS):
        row = fin[fin["grupo_edad"].eq(age)].iloc[0]
        vals = [row[c] for c, _ in indicators]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=age, color=config.AGE_COLORS[age], alpha=0.9)
        for b, v in zip(bars, vals):
            if pd.notna(v):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, [label for _, label in indicators], fontsize=8)
    ax.set_ylabel("% de personas (18+)")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, max(fin[["pct_alto_estres", "pct_gasto_supera_ingreso_laboral"]].max()) * 1.35)
    ax.set_title("Estrés y comparación mensual de gasto e ingreso laboral")
    ax.legend(title="Edad", fontsize=8, title_fontsize=8)

    fig.suptitle(
        "H3. Indicadores financieros por edad; no identifican cómo se financia el gasto visible",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    return _save(fig, "h3_finanzas_ensafi.png", config.SOURCE_ENSAFI +
                 " Gasto/ingreso: solo montos conocidos; ingreso laboral, no total. Ahorro: en cuentas.")


def fig_h4_pensiones_vivienda(exp: pd.DataFrame, housing: pd.DataFrame) -> str:
    """H4: pensión y vivienda: expectativas vs. carga actual."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.5, 1]})

    ax = axes[0]
    sources = [
        "Apoyo de gobierno",
        "Pensión, jubilación o AFORE",
        "Seguir trabajando",
        "Familia",
        "Inversiones",
    ]
    x = np.arange(len(sources))
    width = 0.2
    for i, age in enumerate(config.AGE_LABELS):
        row = exp[exp["grupo_edad"].eq(age)].iloc[0]
        vals = [row[s] for s in sources]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=age, color=config.AGE_COLORS[age], alpha=0.9)
        for b, v in zip(bars, vals):
            if pd.notna(v):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x, ["Gobierno", "Pensión/\nAFORE", "Seguir\ntrabajando", "Familia", "Inversiones"], fontsize=8)
    ax.set_ylabel("% que espera cubrir sus gastos así")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.set_title("¿Con qué espera vivir en la vejez?")
    ax.legend(title="Edad", fontsize=8, title_fontsize=8)

    ax = axes[1]
    x = np.arange(len(housing))
    ax.bar(x, housing["pct_rentados"], color=config.COLORS["older"], alpha=0.9, label="% que renta")
    for i, v in enumerate(housing["pct_rentados"]):
        ax.text(i, v + 0.008, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, housing["grupo_edad"])
    ax.set_ylabel("% de hogares que rentan")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 0.5)
    ax.set_title("Hogares que rentan")
    ax2 = ax.twinx()
    ax2.plot(
        x,
        housing["carga_renta_mediana"],
        color=config.COLORS["young"],
        marker="o",
        linewidth=2.5,
        label="Renta / ingreso (mediana)",
    )
    for i, v in enumerate(housing["carga_renta_mediana"]):
        if pd.notna(v):
            ax2.annotate(
                f"{v * 100:.0f}%",
                (i, v),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                va="bottom",
                fontsize=8,
                color=config.COLORS["young"],
            )
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    carga = housing["carga_renta_mediana"].dropna()
    if len(carga):
        ax2.set_ylim(max(0, carga.min() * 0.90), carga.max() * 1.18)
    ax2.set_ylabel("Renta / ingreso (mediana)", color=config.COLORS["young"])
    ax2.tick_params(axis="y", colors=config.COLORS["young"])
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=7)

    fig.suptitle(
        "H4. Expectativas de retiro y situación de vivienda por edad",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    return _save(fig, "h4_pensiones_vivienda.png", config.SOURCE_ENSAFI + " | " + config.SOURCE_ENIGH)


def fig_h5_concentracion(conc: dict) -> str:
    """H5: el gasto visible está concentrado en una minoría de hogares."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))

    ax = axes[0]
    ax.plot(conc["lorenz_x"] * 100, conc["lorenz_y"] * 100, color=config.COLORS["young"], linewidth=2.5, label="Gasto visible (D2)")
    ax.plot([0, 100], [0, 100], color=config.COLORS["gray"], linestyle="--", linewidth=1, label="Igualdad perfecta")
    ax.set_xlabel("% acumulado de hogares (ordenados por gasto visible)")
    ax.set_ylabel("% acumulado del gasto visible")
    ax.set_title("Curva de Lorenz del gasto visible")
    ax.legend(loc="upper left", fontsize=8)
    ax.annotate(
        f"Gini = {conc['gini_d2']:.2f}\nTop 10% = {conc['top10_d2'] * 100:.0f}%\nTop 20% = {conc['top20_d2'] * 100:.0f}%",
        xy=(0.05, 0.65),
        xycoords="axes fraction",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=config.COLORS["light"]),
    )

    ax = axes[1]
    by_age = conc["by_age"]
    bars = ax.bar(by_age["grupo_edad"], by_age["share_gasto_d2_total"], color=[config.AGE_COLORS[a] for a in by_age["grupo_edad"]], alpha=0.9)
    for b, v in zip(bars, by_age["share_gasto_d2_total"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v * 100:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("% del gasto visible total del país")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Reparto del gasto visible por edad del jefe/a")
    ax.set_ylim(0, by_age["share_gasto_d2_total"].max() * 1.25)

    fig.suptitle(
        "H5. Concentración y distribución del gasto visible por edad",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    return _save(fig, "h5_concentracion.png", config.SOURCE_ENIGH)


def fig_h1b_bienes(assets: pd.DataFrame) -> str:
    """Complemento H1: tenencia declarada de bienes y servicios visibles."""
    _style()
    fig, ax = plt.subplots(figsize=(11, 5))
    indicators = ["Auto", "Celular", "Internet", "TV de paga", "Streaming"]
    x = np.arange(len(indicators))
    width = 0.2
    for i, age in enumerate(config.AGE_LABELS):
        row = assets[assets["grupo_edad"].eq(age)].iloc[0]
        vals = [row[c] for c in indicators]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=age, color=config.AGE_COLORS[age], alpha=0.9)
        for b, v in zip(bars, vals):
            if pd.notna(v):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x, indicators)
    ax.set_ylabel("% de personas (18+)")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.set_title("Personas que residen en viviendas con estos bienes y servicios")
    ax.legend(title="Edad", fontsize=8, title_fontsize=8)
    return _save(fig, "h1b_bienes_ensafi.png", config.SOURCE_ENSAFI)
