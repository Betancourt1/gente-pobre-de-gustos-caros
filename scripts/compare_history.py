#!/usr/bin/env python3
"""Produce H1c aggregate CSV tables and figures from the downloaded ENIGH waves."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gpdgc.historical import YEARS, compare_waves, load_wave

COLORS = {"alimentos_fuera": "#00798c", "recreacion_hospedaje": "#d1495b", "h1c": "#30638e"}
LABELS = {"alimentos_fuera": "Alimentos fuera del hogar", "recreacion_hospedaje": "Recreación, turismo y hospedaje", "h1c": "Suma de ambas categorías (H1c)"}


def style_axis(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)
    ax.set_xticks(YEARS)
    ax.set_xlim(1991, 2027)
    ax.set_xlabel("Año de la encuesta")


def plot_results(tables, out):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
                         "axes.labelsize": 10, "figure.facecolor": "white", "axes.facecolor": "white"})
    profiles = tables["perfiles"]
    young = profiles[profiles.grupo_edad.eq("18–29")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True)
    for ax, metric in zip(axes, LABELS):
        data = young[young.indicador.eq(metric)].sort_values("anio")
        point = data.estimacion.to_numpy() * 100
        interval = np.vstack([point - data.ic95_inferior.to_numpy() * 100, data.ic95_superior.to_numpy() * 100 - point])
        ax.errorbar(data.anio, point, yerr=interval, fmt="o-", capsize=4, lw=1.5, color=COLORS[metric])
        for x, y, upper in zip(data.anio, point, data.ic95_superior * 100):
            ax.annotate(f"{y:.1f}%", (x, upper), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=10)
        ax.set_title(LABELS[metric], pad=14)
        ax.set_ylim(0, 15)
        style_axis(ax)
    axes[0].set_ylabel("Media de la proporción del gasto monetario (%)")
    fig.suptitle("Hogares con jefatura de 18–29 años, en cuatro momentos", fontsize=17, x=.06, ha="left")
    fig.text(.06, .05, "ENIGH 1994, 2004, 2014 y 2024 · Factores de hogar; IC 95% con estratos y UPM.\nH1c conserva categorías amplias; no equivale a D2 ni identifica preferencias de una generación.", fontsize=10, color="#444444")
    fig.subplots_adjust(left=.07, right=.98, top=.79, bottom=.23, wspace=.13)
    fig.savefig(out / "h1_historico_jovenes.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True, sharey=True)
    for ax, group in zip(axes.flat, ["18–29", "30–44", "45–59", "60+"]):
        data = profiles[profiles.grupo_edad.eq(group) & profiles.indicador.eq("h1c")].sort_values("anio")
        p = data.estimacion.to_numpy() * 100
        errors = np.vstack([p - data.ic95_inferior.to_numpy() * 100, data.ic95_superior.to_numpy() * 100 - p])
        ax.errorbar(data.anio, p, yerr=errors, fmt="o-", color=COLORS["h1c"], capsize=4)
        for x, y, upper in zip(data.anio, p, data.ic95_superior * 100):
            ax.annotate(f"{y:.1f}%", (x, upper), xytext=(0, 6), textcoords="offset points", ha="center")
        ax.set_title(f"Jefatura de {group} años", loc="left", weight="bold")
        ax.set_ylim(0, 16)
        ax.set_ylabel("Proporción H1c (%)")
        style_axis(ax)
    fig.suptitle("Perfiles históricos por edad e IC 95%", fontsize=16, x=.07, ha="left")
    fig.text(.07, .025, "ENIGH · Media ponderada de proporciones de cada hogar; IC 95% con estratos y UPM.\nAlimentos fuera + recreación, turismo y hospedaje / gasto monetario oficial. Muestras transversales distintas.", fontsize=10, color="#444444")
    fig.subplots_adjust(left=.09, right=.97, top=.88, bottom=.15, hspace=.33, wspace=.2)
    fig.savefig(out / "h1_historico_edades.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    data = tables["quintiles"]
    palette = ["#787878", "#be7a30", "#00798c", "#d1495b"]
    for i, (year, color) in enumerate(zip(YEARS, palette)):
        sub = data[data.anio.eq(year)].sort_values("quintil_ingreso_pc")
        p = sub.estimacion.to_numpy() * 100
        errors = np.vstack([p - sub.ic95_inferior.to_numpy() * 100, sub.ic95_superior.to_numpy() * 100 - p])
        ax.errorbar(sub.quintil_ingreso_pc + (i - 1.5) * .12, p, yerr=errors, fmt="o", capsize=3, color=color, label=str(year))
    ax.set_xticks(range(1, 6), ["Q1\nMenor ingreso", "Q2", "Q3", "Q4", "Q5\nMayor ingreso"])
    ax.set_ylabel("Proporción H1c (%), jefatura de 18–29")
    ax.set_ylim(bottom=0)
    ax.set_title("Comparación dentro de la posición de ingreso de cada época", loc="left", fontsize=16, pad=20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.18)
    ax.legend(ncol=4, frameon=False, loc="upper left")
    fig.text(.10, .045, "ENIGH · Quintiles ponderados de ingreso corriente por persona entre hogares con jefatura adulta de cada año.\nIC 95% condicionales a los cortes estimados. El mismo quintil no implica el mismo poder adquisitivo.", fontsize=9, color="#444444")
    fig.subplots_adjust(left=.10, right=.97, top=.85, bottom=.24)
    fig.savefig(out / "h1_historico_quintiles.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data/raw/enigh")
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    waves, validation = {}, []
    for year in YEARS:
        print(f"ENIGH {year}: leyendo y conciliando...", flush=True)
        waves[year], audit = load_wave(args.raw, year)
        validation.append(audit)
    tables = compare_waves(waves)
    tables["validacion"] = pd.DataFrame(validation)
    table_dir, figure_dir = args.output / "tables", args.output / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(table_dir / f"h1_historico_{name}.csv", index=False, float_format="%.10g")
    plot_results(tables, figure_dir)
    from gpdgc.significance_report import build
    build(args.output)
    print(f"Listo: {len(tables)} tablas y 3 figuras en {args.output}")


if __name__ == "__main__":
    main()
