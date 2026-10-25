"""Lectura y limpieza de los microdatos de ENIGH 2024 y ENSAFI 2023."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from . import config
from .taxonomy import add_expense_flags


def _to_num(s: pd.Series, sentinels: tuple[float, ...] = ()) -> pd.Series:
    out = pd.to_numeric(
        s.astype("string").str.strip().str.replace(",", ".", regex=False),
        errors="coerce",
    )
    for sentinel in sentinels:
        out = out.mask(out == sentinel)
    return out


def _read(path, usecols=None, dtype="string") -> pd.DataFrame:
    """Preserva ceros iniciales; cada cargador convierte solo las magnitudes."""
    return pd.read_csv(
        path,
        encoding="utf-8",
        usecols=usecols,
        dtype=dtype,
        low_memory=False,
    )


# ---------------------------------------------------------------------------
# ENIGH
# ---------------------------------------------------------------------------

_ENIGH_STRING_COLS = {
    "folioviv",
    "foliohog",
    "ubica_geo",
    "tam_loc",
    "est_socio",
    "est_dis",
    "upm",
    "clase_hog",
    "sexo_jefe",
    "educa_jefe",
}


def load_concentradohogar() -> pd.DataFrame:
    df = _read(config.ENIGH_TABLES["concentradohogar"])
    for col in df.columns:
        if col in _ENIGH_STRING_COLS:
            df[col] = df[col].astype("string").str.strip()
        else:
            df[col] = _to_num(df[col])
    df["foliohog"] = df["foliohog"].astype("string").str.strip()
    return df


def load_viviendas() -> pd.DataFrame:
    usecols = [
        "folioviv",
        "tenencia",
        "renta",
        "pago_viv",
        "tot_resid",
        "tot_hog",
        "tam_loc",
        "est_socio",
    ]
    df = _read(config.ENIGH_TABLES["viviendas"], usecols=usecols)
    df["folioviv"] = df["folioviv"].astype("string").str.strip()
    for col in ["tenencia", "tam_loc", "est_socio"]:
        df[col] = df[col].astype("string").str.strip()
    for col in ["renta", "pago_viv", "tot_resid", "tot_hog"]:
        df[col] = _to_num(df[col], sentinels=(999999, 999999999))
    return df


def load_poblacion_hogar() -> pd.DataFrame:
    """Agrega características de las personas a nivel hogar."""
    usecols = ["folioviv", "foliohog", "numren", "parentesco", "sexo", "edad", "factor"]
    df = _read(config.ENIGH_TABLES["poblacion"], usecols=usecols)
    for col in ["folioviv", "foliohog", "numren", "parentesco", "sexo"]:
        df[col] = df[col].astype("string").str.strip()
    df["edad"] = _to_num(df["edad"])
    # Mismo universo de integrantes que tot_integ en concentradohogar.
    df = df[df["parentesco"].str[0].isin(["1", "2", "3", "5", "6"])].copy()
    df["es_joven"] = df["edad"].between(18, 29)
    df["es_menor"] = df["edad"] < 18
    df["menor_14"] = df["edad"] < 14
    df["es_adulto_mayor"] = df["edad"] >= 65
    df["es_hijo"] = df["parentesco"].str.startswith("3", na=False)
    df["joven_hijo"] = df["es_joven"] & df["es_hijo"]

    agg = (
        df.groupby(["folioviv", "foliohog"], as_index=False)
        .agg(
            n_personas=("numren", "size"),
            n_jovenes=("es_joven", "sum"),
            n_jovenes_hijos=("joven_hijo", "sum"),
            n_menores=("es_menor", "sum"),
            n_menores_14=("menor_14", "sum"),
            n_adultos_mayores=("es_adulto_mayor", "sum"),
        )
    )
    return agg


def load_gastos_hogar(force: bool = False) -> pd.DataFrame:
    """Agrega consumo G1 de gastoshogar y gastospersona, sin duplicar registros."""
    cache = config.PROCESSED / "gastos_consumo_g1_v2.parquet"
    sources = [config.ENIGH_TABLES[t] for t in ("gastoshogar", "gastospersona")]
    dependencies = sources + [Path(__file__), Path(__file__).with_name("taxonomy.py")]
    if cache.exists() and not force and cache.stat().st_mtime >= max(
        p.stat().st_mtime for p in dependencies
    ):
        return pd.read_parquet(cache)

    df = pd.concat(
        [_read(p, usecols=["folioviv", "foliohog", "clave", "tipo_gasto", "gasto_tri"])
         for p in sources],
        ignore_index=True,
    )
    df["gasto_tri"] = _to_num(df["gasto_tri"]).astype("float64")
    df = df[df["tipo_gasto"].eq("G1")].copy()
    df = add_expense_flags(df)
    df = df[df["es_consumo"]].copy()

    df["_g_d1"] = df["gasto_tri"].where(df["d1_discrecional"], 0.0)
    df["_g_d2"] = df["gasto_tri"].where(df["d2_gusto_visible"], 0.0)
    df["_g_d3"] = df["gasto_tri"].where(df["d3_vicios"], 0.0)
    df["_g_d2_alcohol"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["capitulo"].eq("02"), 0.0
    )
    df["_g_d2_restaurantes"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["capitulo"].eq("11"), 0.0
    )
    df["_g_d2_recreacion"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["capitulo"].eq("09"), 0.0
    )
    df["_g_d2_personal"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["capitulo"].eq("13"), 0.0
    )
    df["_g_d2_streaming"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["capitulo"].eq("08"), 0.0
    )
    df["_g_d2_auto"] = df["gasto_tri"].where(
        df["d2_gusto_visible"] & df["clave"].eq("071110"), 0.0
    )

    base = (
        df.groupby(["folioviv", "foliohog"], as_index=False)
        .agg(
            gasto_total_g1=("gasto_tri", "sum"),
            gasto_d1=("_g_d1", "sum"),
            gasto_d2=("_g_d2", "sum"),
            gasto_d3=("_g_d3", "sum"),
            gasto_d2_alcohol=("_g_d2_alcohol", "sum"),
            gasto_d2_restaurantes=("_g_d2_restaurantes", "sum"),
            gasto_d2_recreacion=("_g_d2_recreacion", "sum"),
            gasto_d2_personal=("_g_d2_personal", "sum"),
            gasto_d2_streaming=("_g_d2_streaming", "sum"),
            gasto_d2_auto=("_g_d2_auto", "sum"),
            n_renglones=("clave", "size"),
        )
    )

    # Gasto por capítulo (se usa para composición y validación).
    chap = (
        df.pivot_table(
            index=["folioviv", "foliohog"],
            columns="capitulo",
            values="gasto_tri",
            aggfunc="sum",
            fill_value=0.0,
        )
        .add_prefix("cap_")
        .reset_index()
    )

    out = base.merge(chap, on=["folioviv", "foliohog"], how="left")
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache, index=False)
    return out


def load_enigh_hogares(force_gastos: bool = False) -> pd.DataFrame:
    """Base analítica de hogares ENIGH con gasto, ingreso y vivienda."""
    hog = load_concentradohogar()
    viv = load_viviendas()
    per = load_poblacion_hogar()
    gas = load_gastos_hogar(force=force_gastos)

    # `viviendas` solo tiene folioviv; se une a todos los hogares de la vivienda.
    df = hog.merge(viv, on="folioviv", how="left", suffixes=("", "_viv"), validate="many_to_one")
    df = df.merge(per, on=["folioviv", "foliohog"], how="left", validate="one_to_one")
    if df["n_personas"].isna().any() or not df["n_personas"].eq(df["tot_integ"]).all():
        raise ValueError("El cruce de población no concilia con tot_integ")
    if df["tenencia"].isna().any():
        raise ValueError("Hay hogares sin correspondencia en viviendas")
    # Outer detecta claves de gastos perdidas, en lugar de convertirlas en ceros.
    df = df.merge(gas, on=["folioviv", "foliohog"], how="outer", validate="one_to_one", indicator=True)
    if df["_merge"].eq("right_only").any():
        raise ValueError("Hay claves de gastos sin correspondencia en concentradohogar")
    df["tiene_registros_gasto"] = df["_merge"].eq("both")
    df = df.drop(columns="_merge")

    # Gasto total: si no hay renglones, 0.
    for c in [
        "gasto_total_g1",
        "gasto_d1",
        "gasto_d2",
        "gasto_d3",
        "gasto_d2_alcohol",
        "gasto_d2_restaurantes",
        "gasto_d2_recreacion",
        "gasto_d2_personal",
        "gasto_d2_streaming",
        "gasto_d2_auto",
        "n_renglones",
    ]:
        df[c] = df[c].fillna(0.0)
    for chapter in [f"cap_{i:02d}" for i in range(1, 19)]:
        if chapter not in df.columns:
            df[chapter] = 0.0
        df[chapter] = df[chapter].fillna(0.0)

    # Escala de equivalencia OCDE modificada.
    adultos = df["tot_integ"] - df["n_menores_14"]
    df["adultos_eq"] = adultos
    df["escala_eq"] = 1 + 0.5 * (adultos - 1) + 0.3 * df["n_menores_14"]
    df["ing_eq"] = df["ing_cor"] / df["escala_eq"]
    df["gasto_eq"] = df["gasto_total_g1"] / df["escala_eq"]
    df["gasto_d2_eq"] = df["gasto_d2"] / df["escala_eq"]

    df["grupo_edad"] = pd.cut(
        df["edad_jefe"],
        bins=config.AGE_BINS,
        labels=config.AGE_LABELS,
        right=False,
    )
    df["share_d1"] = df["gasto_d1"] / df["gasto_total_g1"].where(df["gasto_total_g1"] > 0)
    df["share_d2"] = df["gasto_d2"] / df["gasto_total_g1"].where(df["gasto_total_g1"] > 0)
    df["share_d3"] = df["gasto_d3"] / df["gasto_total_g1"].where(df["gasto_total_g1"] > 0)
    df["share_alimentos"] = df["cap_01"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_vivienda"] = df["cap_04"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_salud"] = df["cap_06"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_educacion"] = df["cap_10"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_restaurantes"] = df["cap_11"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_recreacion"] = df["cap_09"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )
    df["share_alcohol"] = df["cap_02"] / df["gasto_total_g1"].where(
        df["gasto_total_g1"] > 0
    )

    # Carga de renta: la renta es mensual y el ingreso de la ENIGH es trimestral.
    df["es_rentado"] = df["tenencia"].eq("1")
    df["carga_renta"] = np.where(
        df["es_rentado"] & (df["ing_cor"] > 0),
        (df["renta"] * 3) / df["ing_cor"],
        np.nan,
    )
    df["share_vivienda_gasto"] = df["share_vivienda"]

    # Deciles ponderados de ingreso equivalente.
    from .weights import add_weighted_deciles

    # Mismo universo adulto en perfiles, deciles y concentración nacional.
    n_source = len(df)
    design_units = list(df[["est_dis", "upm"]].drop_duplicates().itertuples(index=False, name=None)) if {"est_dis", "upm"}.issubset(df.columns) else None
    df = df[df["grupo_edad"].notna()].copy()
    df = add_weighted_deciles(df, "ing_eq", "factor", "decil_ing")
    if design_units is not None:
        df.attrs["design_units"] = design_units
    df.attrs["hogares_fuente"] = n_source
    df.attrs["hogares_excluidos_edad"] = n_source - len(df)

    return df


# ---------------------------------------------------------------------------
# ENSAFI
# ---------------------------------------------------------------------------

_ENSAFI_KEYS = {"LLAVEMOD", "LLAVEVIV", "LLAVEHOG", "EST_DIS", "UPM_DIS"}
_ENSAFI_AMOUNTS = {
    "P5_19": (99999,),
    "P5_21": (99999,),
    "P5_22": (999999, 999888, 980000),
    "P6_12": (99999999, 99999888, 98000000),
    "P6_13": (999999, 999888, 980000),
    "INGRESO_M": (999999,),
}


def load_ensafi_personas() -> pd.DataFrame:
    usecols = [
        "LLAVEMOD",
        "LLAVEVIV",
        "LLAVEHOG",
        "EDAD_V",
        "SEXO",
        "FAC_ELE",
        "EST_DIS",
        "UPM_DIS",
        "NIV_BIENES",
        "INGRESO_M",
        "NIV_ESTRES",
        "SALARIO_ENT",
        "SAL_MIN_RP",
        "SAL_MIN_ZF",
        "CONF_FINAN",
        "GRA_CONTROL",
        "ORIEN_FUT",
        "IMPULSIVID",
        "ORIEN_ACCI",
        "OPTIMISMO",
        "GTOS_AHORR",
        "DEPEN_SUM",
        "DEP_ECO",
        "P5_14",
        "P5_16",
        "P5_19",
        "P5_19A",
        "P5_21",
        "P5_22",
        "P6_2_10",
        "P6_3",
        "P6_5_1",
        "P6_5_2",
        "P6_5_3",
        "P6_5_4",
        "P6_5_5",
        "P6_6_1",
        "P6_6_2",
        "P6_6_3",
        "P6_6_4",
        "P6_6_5",
        "P6_6_6",
        "P6_6_7",
        "P6_6_8",
        "P6_6_9",
        "P6_7",
        "P6_8",
        "P6_9",
        "P7_6_1",
        "P7_6_2",
        "P7_6_3",
        "P7_6_4",
        "P7_6_5",
        "P7_6_6",
        "P7_6_7",
        "P7_6_8",
        "P8_4",
        "P9_1",
        "P9_2",
        "P9_3_1",
        "P9_3_2",
        "P9_3_3",
        "P9_3_4",
        "P9_3_5",
        "P9_3_6",
        "P9_3_7",
    ]
    df = _read(config.ENSAFI_TABLES["tmodulo"])
    # Algunas versiones del archivo traen todo como texto; se seleccionan
    # únicamente las columnas necesarias y se convierten.
    df = df[[c for c in usecols if c in df.columns]].copy()
    for col in df.columns:
        if col in _ENSAFI_KEYS:
            df[col] = df[col].astype("string").str.strip()
        else:
            df[col] = _to_num(df[col], _ENSAFI_AMOUNTS.get(col, ()))

    df["grupo_edad"] = pd.cut(
        df["EDAD_V"],
        bins=config.AGE_BINS,
        labels=config.AGE_LABELS,
        right=False,
    )
    df["mujer"] = df["SEXO"].eq(2)
    df["tiene_afore"] = df["P6_2_10"].eq(1)
    # El salto de P6.3 corresponde a no tener las cuentas preguntadas.
    df["reporta_ahorro_cuentas"] = df["P6_3"].eq(1).fillna(False)
    debt_cols = [f"P6_5_{i}" for i in range(1, 6)] + [f"P6_6_{i}" for i in range(1, 10)]
    df["tiene_deuda_credito"] = df[debt_cols].eq(1).any(axis=1)
    # Incidencia sobre adultos; el salto por no tener crédito no indica atraso.
    df["reporta_atraso_pago"] = df["P6_7"].eq(1).fillna(False)
    df["ingreso_insuficiente"] = df["P6_9"].eq(2)
    df["alto_estres"] = df["NIV_ESTRES"].eq(1)
    df["sin_empleo"] = df["P5_14"].isin([3, 4, 5, 6, 7, 8, 9]) & df["P5_16"].eq(7)
    df = add_monthly_comparison(df)
    return df


def add_monthly_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Gasto vs. ingreso laboral mensual conocido; no estima ahorro total."""
    df = df.copy()
    # 98,000 es un límite abierto, no un monto exacto.
    df["ingreso_laboral_mensual"] = df["INGRESO_M"].where(df["P5_19"].ne(98000))
    df["gasto_mensual"] = df["P5_21"].where(df["P5_21"].ne(98000))
    valid = df["ingreso_laboral_mensual"].ge(0).fillna(False) & df["gasto_mensual"].ge(0).fillna(False)
    df["comparable_ingreso_gasto"] = valid
    df["gasto_supera_ingreso_laboral"] = (
        df["gasto_mensual"].gt(df["ingreso_laboral_mensual"]).astype("boolean").where(valid)
    )
    return df


def load_ensafi_vivienda() -> pd.DataFrame:
    usecols = [
        "LLAVEVIV",
        "P1_4_04",  # automóvil o camioneta
        "P1_4_07",  # teléfono celular
        "P1_4_08",  # internet
        "P1_4_09",  # televisión de paga
        "P1_4_10",  # streaming
    ]
    df = _read(config.ENSAFI_TABLES["tvivienda"], usecols=usecols)
    df["LLAVEVIV"] = df["LLAVEVIV"].astype("string").str.strip()
    for col in usecols[1:]:
        df[col] = _to_num(df[col])
    df = df.rename(
        columns={
            "P1_4_04": "tiene_auto",
            "P1_4_07": "tiene_celular",
            "P1_4_08": "tiene_internet",
            "P1_4_09": "tiene_tv_paga",
            "P1_4_10": "tiene_streaming",
        }
    )
    for col in ["tiene_auto", "tiene_celular", "tiene_internet", "tiene_tv_paga", "tiene_streaming"]:
        df[col] = df[col].eq(1)
    return df
