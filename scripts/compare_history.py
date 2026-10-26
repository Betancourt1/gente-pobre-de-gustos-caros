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

from gpdgc.figure_style import (plt, math, COLORS, AGES, title, time_panels, panel_bars, finish)

def plot_results(tables, out):
    profiles=tables['perfiles']
    h1panels=[(profiles[profiles.indicador.eq(key)][lambda d:d.grupo_edad.eq('18–29')],label,['18–29'],15,100) for key,label in
              [('alimentos_fuera','Alimentos fuera del hogar'),('recreacion_hospedaje','Recreación, turismo y hospedaje'),('h1c','H1c · Ambas categorías')]]
    for name in ['h1_historico_jovenes.png']:
        time_panels(out / name,'H1 · Gasto de los hogares jóvenes en cuatro encuestas','ENIGH · Jefatura de 18–29 años · Porcentaje del gasto monetario oficial',h1panels,
                    'IC 95% individuales',3)
    time_panels(out / 'h1_historico_edades.png','H1 · La trayectoria del gasto según la edad','H1c / gasto monetario oficial (%) · Edad de la jefatura · ENIGH',
                [(profiles[profiles.indicador.eq('h1c')][lambda d:d.grupo_edad.eq(a)],'Jefatura de '+a+' años',[a],16,100) for a in AGES],
                'IC 95% individuales · H1c: alimentos fuera + recreación, turismo y hospedaje')
    q=tables['quintiles'];fig,axs=plt.subplots(2,2,figsize=(13,9));title(fig,'H1 · Gasto de hogares jóvenes según su posición de ingreso','H1c / gasto monetario (%) · Jefatura de 18–29 años · ENIGH')
    limit=max(25,math.ceil(float(q.ic95_superior.max()*100)/5)*5)
    for ax,year in zip(axs.flat,[1994,2004,2014,2024]):
        d=q[q.anio.eq(year)].sort_values('quintil_ingreso_pc')
        panel_bars(ax,d,str(year),['Q1 · menor ingreso','Q2','Q3','Q4','Q5 · mayor ingreso'],[COLORS['18–29']]*5,limit)
    fig.subplots_adjust(left=.17,right=.89,top=.83,bottom=.08,hspace=.5,wspace=.7)
    finish(fig, out / 'h1_historico_quintiles.png', 'IC 95% individuales · Quintiles de ingreso corriente por persona')

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
