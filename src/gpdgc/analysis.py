"""Tablas analíticas que respaldan cada hipótesis del proyecto."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .weights import (
    gini,
    lorenz_curve,
    top_share,
    weighted_mean,
    weighted_quantile,
    weighted_share,
)


def _by_age(df: pd.DataFrame, weight: str, func) -> pd.DataFrame:
    rows = []
    for label in config.AGE_LABELS:
        sub = df[df["grupo_edad"].astype("string").eq(label)]
        row = {"grupo_edad": label, "n": int(len(sub))}
        row.update(func(sub))
        rows.append(row)
    out = pd.DataFrame(rows)
    total = weighted_share(df["grupo_edad"].notna(), df[weight])
    out["peso_pct"] = [
        weighted_share(df["grupo_edad"].astype("string").eq(lbl), df[weight])
        / total
        * 100
        if total
        else np.nan
        for lbl in out["grupo_edad"]
    ]
    return out


# ---------------------------------------------------------------------------
# ENIGH: H1, H2, H5 y vivienda
# ---------------------------------------------------------------------------


def enigh_profile(df: pd.DataFrame) -> pd.DataFrame:
    """H1: nivel y composición del gasto por edad del jefe/a."""

    def stats(sub):
        w = sub["factor"]
        return {
            "ing_eq_medio": weighted_mean(sub["ing_eq"], w),
            "ing_eq_mediano": weighted_quantile(sub["ing_eq"], w, 0.5),
            "gasto_eq_medio": weighted_mean(sub["gasto_eq"], w),
            "gasto_eq_mediano": weighted_quantile(sub["gasto_eq"], w, 0.5),
            "share_d1": weighted_mean(sub["share_d1"], w),
            "share_d2": weighted_mean(sub["share_d2"], w),
            "share_d3": weighted_mean(sub["share_d3"], w),
            "gasto_d2_eq": weighted_mean(sub["gasto_d2"] / sub["escala_eq"], w),
            "share_alimentos": weighted_mean(sub["share_alimentos"], w),
            "share_vivienda": weighted_mean(sub["share_vivienda"], w),
            "share_salud": weighted_mean(sub["share_salud"], w),
            "share_educacion": weighted_mean(sub["share_educacion"], w),
            "share_restaurantes": weighted_mean(sub["share_restaurantes"], w),
            "share_recreacion": weighted_mean(sub["share_recreacion"], w),
            "share_alcohol": weighted_mean(sub["share_alcohol"], w),
            "share_d2_alcohol": weighted_mean(sub["gasto_d2_alcohol"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
            "share_d2_restaurantes": weighted_mean(sub["gasto_d2_restaurantes"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
            "share_d2_recreacion": weighted_mean(sub["gasto_d2_recreacion"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
            "share_d2_personal": weighted_mean(sub["gasto_d2_personal"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
            "share_d2_streaming": weighted_mean(sub["gasto_d2_streaming"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
            "share_d2_auto": weighted_mean(sub["gasto_d2_auto"] / sub["gasto_total_g1"].where(sub["gasto_total_g1"] > 0), w),
        }

    out = _by_age(df, "factor", stats)
    out.attrs["source"] = config.SOURCE_ENIGH
    return out


def enigh_by_decile(df: pd.DataFrame, basket: str = "share_d2") -> pd.DataFrame:
    """H2: share de la canasta por grupo de edad y decil de ingreso."""
    sub = df[df["decil_ing"].notna()].copy()
    sub["decil_ing"] = sub["decil_ing"].astype(int)
    rows = []
    for age in config.AGE_LABELS:
        for dec in range(1, 11):
            s = sub[
                sub["grupo_edad"].astype("string").eq(age)
                & sub["decil_ing"].eq(dec)
            ]
            rows.append(
                {
                    "grupo_edad": age,
                    "decil_ing": dec,
                    "n": len(s),
                    basket: weighted_mean(s[basket], s["factor"]),
                }
            )
    return pd.DataFrame(rows)


def enigh_concentration(df: pd.DataFrame) -> dict:
    """H5: concentración del gasto discrecional entre hogares."""
    out = {
        "gini_d2": gini(df["gasto_d2"], df["factor"]),
        "top10_d2": top_share(df["gasto_d2"], df["factor"], 0.10),
        "top20_d2": top_share(df["gasto_d2"], df["factor"], 0.20),
        "gini_d1": gini(df["gasto_d1"], df["factor"]),
        "top10_d1": top_share(df["gasto_d1"], df["factor"], 0.10),
    }
    x, y = lorenz_curve(df["gasto_d2"], df["factor"])
    out["lorenz_x"] = x
    out["lorenz_y"] = y

    by_age = []
    total_d2 = (df["gasto_d2"] * df["factor"]).sum()
    for label in config.AGE_LABELS:
        sub = df[df["grupo_edad"].astype("string").eq(label)]
        by_age.append(
            {
                "grupo_edad": label,
                "top20_d2": top_share(sub["gasto_d2"], sub["factor"], 0.20),
                "share_gasto_d2_total": (
                    (sub["gasto_d2"] * sub["factor"]).sum() / total_d2
                    if total_d2
                    else np.nan
                ),
            }
        )
    out["by_age"] = pd.DataFrame(by_age)
    return out


def enigh_housing(df: pd.DataFrame) -> pd.DataFrame:
    """H4 (vivienda): carga de renta y peso de vivienda por edad."""

    def stats(sub):
        w = sub["factor"]
        renters = sub[sub["es_rentado"]]
        return {
            "pct_rentados": weighted_share(sub["es_rentado"], w),
            "carga_renta_mediana": weighted_quantile(
                renters["carga_renta"], renters["factor"], 0.5
            )
            if len(renters)
            else np.nan,
            "share_vivienda": weighted_mean(sub["share_vivienda"], w),
        }

    out = _by_age(df, "factor", stats)
    out.attrs["source"] = config.SOURCE_ENIGH
    return out


# ---------------------------------------------------------------------------
# ENSAFI: H3 y H4
# ---------------------------------------------------------------------------


def ensafi_financial(df: pd.DataFrame) -> pd.DataFrame:
    """H3: ahorro, deuda y estrés financiero por grupo de edad."""

    def stats(sub):
        w = sub["FAC_ELE"]
        return {
            "pct_afore": weighted_share(sub["tiene_afore"], w),
            "pct_reporta_ahorro_cuentas": weighted_share(sub["reporta_ahorro_cuentas"], w),
            "pct_deuda_credito": weighted_share(sub["tiene_deuda_credito"], w),
            "pct_reporta_atraso": weighted_share(sub["reporta_atraso_pago"], w),
            "pct_ingreso_insuficiente": weighted_share(sub["ingreso_insuficiente"], w),
            "pct_alto_estres": weighted_share(sub["alto_estres"], w),
            "pct_gasto_supera_ingreso_laboral": weighted_share(sub["gasto_supera_ingreso_laboral"], w),
            "n_comparables_ingreso_gasto": int(sub["comparable_ingreso_gasto"].sum()),
            "pct_comparables_ingreso_gasto": weighted_share(sub["comparable_ingreso_gasto"], w),
            "ingreso_laboral_mensual_mediano": weighted_quantile(sub["ingreso_laboral_mensual"], w, 0.5),
            "gasto_mensual_mediano": weighted_quantile(sub["gasto_mensual"], w, 0.5),
        }

    out = _by_age(df, "FAC_ELE", stats)
    out.attrs["source"] = config.SOURCE_ENSAFI
    return out


_EXPECT_COLS = {
    "P9_3_1": "Apoyo de gobierno",
    "P9_3_2": "Pensión, jubilación o AFORE",
    "P9_3_4": "Familia",
    "P9_3_5": "Seguir trabajando",
    "P9_3_6": "Inversiones",
}


def ensafi_expectations(df: pd.DataFrame) -> pd.DataFrame:
    """H4: fuentes previstas para cubrir gastos en la vejez."""
    rows = []
    for label in config.AGE_LABELS:
        sub = df[df["grupo_edad"].astype("string").eq(label)]
        w = sub["FAC_ELE"]
        row = {"grupo_edad": label, "n": len(sub)}
        for col, name in _EXPECT_COLS.items():
            row[name] = weighted_share(sub[col].eq(1), w)
        row["Meta: vivienda"] = weighted_share(sub["P9_1"].isin([1, 2]), w)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.attrs["source"] = config.SOURCE_ENSAFI
    return out


def ensafi_assets(df: pd.DataFrame, viv: pd.DataFrame) -> pd.DataFrame:
    """Bienes y servicios 'visibles' por grupo de edad (ENSAFI)."""
    merged = df.merge(viv, on="LLAVEVIV", how="left", validate="many_to_one", indicator=True)
    if not merged["_merge"].eq("both").all():
        raise ValueError("Hay personas ENSAFI sin correspondencia en viviendas")
    rows = []
    for label in config.AGE_LABELS:
        sub = merged[merged["grupo_edad"].astype("string").eq(label)]
        w = sub["FAC_ELE"]
        rows.append(
            {
                "grupo_edad": label,
                "Auto": weighted_share(sub["tiene_auto"], w),
                "Celular": weighted_share(sub["tiene_celular"], w),
                "Internet": weighted_share(sub["tiene_internet"], w),
                "TV de paga": weighted_share(sub["tiene_tv_paga"], w),
                "Streaming": weighted_share(sub["tiene_streaming"], w),
            }
        )
    return pd.DataFrame(rows)


def key_findings(profile: pd.DataFrame, fin: pd.DataFrame, exp: pd.DataFrame) -> pd.DataFrame:
    """Resumen legible de los principales contrastes."""
    young = profile[profile["grupo_edad"].eq("18-29")].iloc[0]
    senior = profile[profile["grupo_edad"].eq("60+")].iloc[0]
    fy = fin[fin["grupo_edad"].eq("18-29")].iloc[0]
    fs = fin[fin["grupo_edad"].eq("60+")].iloc[0]
    ey = exp[exp["grupo_edad"].eq("18-29")].iloc[0]
    es = exp[exp["grupo_edad"].eq("60+")].iloc[0]

    rows = [
        ("Share D2 (gusto visible), jefes 18-29", young["share_d2"]),
        ("Share D2 (gusto visible), jefes 60+", senior["share_d2"]),
        ("Brecha D2 jóvenes - 60+ (p.p.)", (young["share_d2"] - senior["share_d2"]) * 100),
        ("Share D1 (discrecional amplio), jefes 18-29", young["share_d1"]),
        ("Share D1 (discrecional amplio), jefes 60+", senior["share_d1"]),
        ("% con AFORE, 18-29", fy["pct_afore"]),
        ("% con AFORE, 60+", fs["pct_afore"]),
        ("Proporción con deuda o productos de crédito, 18-29", fy["pct_deuda_credito"]),
        ("% alto estrés financiero, 18-29", fy["pct_alto_estres"]),
        ("% que espera pensión/AFORE, 18-29", ey["Pensión, jubilación o AFORE"]),
        ("% que espera pensión/AFORE, 60+", es["Pensión, jubilación o AFORE"]),
        ("% que espera apoyo de gobierno, 18-29", ey["Apoyo de gobierno"]),
    ]
    return pd.DataFrame(rows, columns=["indicador", "valor"])
