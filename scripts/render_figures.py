"""Regenerate all 35 figures from published CSVs, without recalculating tables."""
from pathlib import Path
import argparse
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from gpdgc import config, plots, historical_figures, historical_report
from gpdgc.significance_report import build as build_significance
from compare_history import plot_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, default=ROOT / 'reports',
                        help='Folder containing tables/; figures are written to figures/.')
    args = parser.parse_args()
    reports = args.reports.resolve()
    config.FIGURES = reports / 'figures'
    config.FIGURES.mkdir(parents=True, exist_ok=True)

    def read(name):
        return pd.read_csv(reports / 'tables' / name)

    plots.fig_h1_composicion(read('h1_perfil_hogares.csv'))
    plots.fig_h1b_bienes(read('h1b_bienes_ensafi.csv'))
    plots.fig_h2_decil(read('h2_share_d2_por_decil.csv'), read('h2_nivel_d2_por_decil.csv'))
    plots.fig_h3_finanzas(read('h3_finanzas_ensafi.csv'))
    plots.fig_h4_pensiones_vivienda(read('h4_expectativas_ensafi.csv'), read('h4_vivienda_por_edad.csv'))

    national = read('h5_concentracion_nacional.csv').set_index('indicador')
    precision = {}
    for key in ['gini', 'top10', 'top20']:
        row = national.loc[key + '_d2']
        precision[key] = {'estimacion': row.valor,
                          'ic95_inferior': row.ic95_inferior,
                          'ic95_superior': row.ic95_superior}
    plots.fig_h5_concentracion({'precision': precision,
                               'lorenz_precision': read('h5_curva_lorenz_d2.csv'),
                               'by_age': read('h5_concentracion_por_edad.csv')})

    historical_figures.main(reports)
    plot_results({'perfiles': read('h1_historico_perfiles.csv'),
                  'quintiles': read('h1_historico_quintiles.csv')}, config.FIGURES)
    build_significance(reports, write_tables=False)
    historical_report.main(reports, write_tables=False)
    print(f'35 figures and HTML reports regenerated in {config.FIGURES}; tables unchanged.')


if __name__ == '__main__':
    main()
