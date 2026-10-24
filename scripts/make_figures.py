"""Genera tablas, figuras y el resumen de hallazgos del proyecto.

Uso:
    python scripts/make_figures.py
    python scripts/make_figures.py --force-gastos   # reconstruye desde ambas fuentes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from gpdgc import analysis, config, plots  # noqa: E402
from gpdgc.io import (  # noqa: E402
    load_enigh_hogares,
    load_ensafi_personas,
    load_ensafi_vivienda,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-gastos", action="store_true")
    args = parser.parse_args()

    config.FIGURES.mkdir(parents=True, exist_ok=True)
    config.TABLES.mkdir(parents=True, exist_ok=True)

    print("Cargando ENIGH 2024...")
    enigh = load_enigh_hogares(force_gastos=args.force_gastos)
    print(f"  hogares: {len(enigh):,}")

    # Validación rápida contra la variable agregada oficial.
    ok = enigh.loc[enigh["gasto_mon"] > 0, "gasto_total_g1"]
    ref = enigh.loc[enigh["gasto_mon"] > 0, "gasto_mon"]
    ratio = (ok / ref).replace([float("inf"), float("-inf")], pd.NA).dropna()
    print(f"  gasto G1 / gasto_mon: mediana={ratio.median():.3f} (n={len(ratio):,})")

    print("Cargando ENSAFI 2023...")
    ensafi = load_ensafi_personas()
    viv = load_ensafi_vivienda()
    print(f"  personas 18+: {len(ensafi):,}")

    # --- Tablas ---------------------------------------------------------
    profile = analysis.enigh_profile(enigh)
    dec_share = analysis.enigh_by_decile(enigh, "share_d2")
    dec_level = analysis.enigh_by_decile(enigh, "gasto_d2_eq")
    conc = analysis.enigh_concentration(enigh)
    housing = analysis.enigh_housing(enigh)
    fin = analysis.ensafi_financial(ensafi)
    exp = analysis.ensafi_expectations(ensafi)
    assets = analysis.ensafi_assets(ensafi, viv)
    findings = analysis.key_findings(profile, fin, exp)

    # Estos controles verifican magnitudes, además de que el proceso termine.
    baskets = enigh[["gasto_d3", "gasto_d2", "gasto_d1", "gasto_total_g1"]].to_numpy(dtype=float)
    if not (np.isfinite(baskets).all() and (baskets >= 0).all()
            and (np.diff(baskets, axis=1) >= -1e-8).all()):
        raise ValueError("Las canastas no cumplen 0 <= D3 <= D2 <= D1 <= consumo")
    components = enigh.filter(regex=r"^gasto_d2_(alcohol|restaurantes|recreacion|personal|streaming|auto)$")
    if not np.allclose(components.sum(axis=1), enigh["gasto_d2"]):
        raise ValueError("Los componentes de D2 no concilian con la canasta")
    if not np.isclose(conc["by_age"]["share_gasto_d2_total"].sum(), 1):
        raise ValueError("La distribución por edad no suma el gasto nacional")
    validation = pd.DataFrame([
        ("hogares_fuente", enigh.attrs["hogares_fuente"]),
        ("hogares_excluidos_edad", enigh.attrs["hogares_excluidos_edad"]),
        ("hogares_analizados", len(enigh)),
        ("hogares_con_registros_gasto", int(enigh["tiene_registros_gasto"].sum())),
        ("hogares_sin_registros_gasto", int((~enigh["tiene_registros_gasto"]).sum())),
        ("hogares_con_consumo_positivo", int(enigh["gasto_total_g1"].gt(0).sum())),
        ("hogares_renta_multihogar", int((enigh["es_rentado"] & enigh["tot_hog"].gt(1)).sum())),
        ("mediana_consumo_sobre_gasto_mon", ratio.median()),
        ("personas_ensafi", len(ensafi)),
        ("personas_comparables_ingreso_gasto", int(ensafi["comparable_ingreso_gasto"].sum())),
        ("personas_ingreso_laboral_conocido", int(ensafi["ingreso_laboral_mensual"].notna().sum())),
    ], columns=["indicador", "valor"])

    sensitivity = dec_share.copy()
    for basket in ("share_d1", "share_d3"):
        sensitivity = sensitivity.merge(
            analysis.enigh_by_decile(enigh, basket),
            on=["grupo_edad", "decil_ing", "n"],
            validate="one_to_one",
        )

    outputs = {
        "h1_perfil_hogares.csv": profile,
        "h2_share_d2_por_decil.csv": dec_share,
        "h2_nivel_d2_por_decil.csv": dec_level,
        "h2_sensibilidad_canastas_por_decil.csv": sensitivity,
        "h4_vivienda_por_edad.csv": housing,
        "h3_finanzas_ensafi.csv": fin,
        "h4_expectativas_ensafi.csv": exp,
        "h1b_bienes_ensafi.csv": assets,
        "h5_concentracion_por_edad.csv": conc["by_age"],
        "h5_concentracion_nacional.csv": pd.DataFrame(
            [(key, conc[key]) for key in
             ("gini_d2", "top10_d2", "top20_d2", "gini_d1", "top10_d1")],
            columns=["indicador", "valor"],
        ),
        "h5_curva_lorenz_d2.csv": pd.DataFrame({
            "proporcion_acumulada_hogares": conc["lorenz_x"],
            "proporcion_acumulada_gasto_d2": conc["lorenz_y"],
        }),
        "hallazgos_clave.csv": findings,
        "validacion_datos.csv": validation,
    }
    for name, table in outputs.items():
        table.to_csv(config.TABLES / name, index=False, encoding="utf-8-sig")

    # --- Figuras --------------------------------------------------------
    print("Generando figuras...")
    paths = [
        plots.fig_h1_composicion(profile),
        plots.fig_h2_decil(dec_share, dec_level),
        plots.fig_h3_finanzas(fin),
        plots.fig_h4_pensiones_vivienda(exp, housing),
        plots.fig_h5_concentracion(conc),
        plots.fig_h1b_bienes(assets),
    ]
    for p in paths:
        print(f"  {p}")

    print("\nResumen de hallazgos:")
    print(findings.to_string(index=False))


if __name__ == "__main__":
    main()
