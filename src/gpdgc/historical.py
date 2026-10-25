"""Comparación descriptiva ENIGH por edad; H1c no equivale a la canasta D2."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from dbfread import DBF
from scipy.stats import t

from .weights import weighted_quantile

YEARS = (1994, 2004, 2014, 2024)
AGE_GROUPS = {"18–29": (18, 29), "18–24": (18, 24), "25–29": (25, 29),
              "30–44": (30, 44), "45–59": (45, 59), "60+": (60, 120)}
METRICS = ("alimentos_fuera", "recreacion_hospedaje", "h1c", "h1c_sin_transferencias")


def code_range(prefix, first, last):
    return {f"{prefix}{i:03}" for i in range(first, last + 1)}


FOOD_CODES = {
    1994: code_range("A", 204, 207), 2004: code_range("A", 235, 239),
    2014: code_range("A", 243, 247),
    2024: {f"11111{i}" for i in range(1, 7)},
}
RECREATION_CODES = {
    1994: code_range("E", 18, 31) | code_range("L", 1, 27) | code_range("N", 3, 5),
    2004: code_range("E", 20, 33) | code_range("L", 1, 29) | code_range("N", 3, 5),
}
LODGING_EXTRA = {2014: {"N005"}, 2024: {"112012", "112013", "112030", "112090"}}
TRANSFER_CODES = {y: code_range("N", 11, 16) | code_range("T", 901, end)
                  for y, end in ((1994, 904), (2004, 914))}


def source_file(raw: Path, year: int, table: str) -> Path:
    patterns = {
        (1994, "concentrado"): "concen_dbf/concen.dbf",
        (2004, "concentrado"): "concen_dbf/concen.dbf",
        (1994, "gastos"): "gastos_dbf/gastos94.dbf",
        (2004, "gastos"): "gastos_dbf/gastos.dbf",
        (2014, "concentrado"): "NCV_Concentrado_2014_concil_2010_csv/NCV_concentrado_2014_concil_2010.csv",
        (2014, "gastoshogar"): "NCV_Gastohogar_2014_concil_2010_csv/ncv_gastohogar_2014_concil_2010.csv",
        (2014, "gastospersona"): "NCV_Gastopersona_2014_concil_2010_csv/ncv_gastopersona_2014_concil_2010.csv",
    }
    relative = patterns.get((year, table), f"enigh2024_ns_{table if table != 'concentrado' else 'concentradohogar'}_csv/{table if table != 'concentrado' else 'concentradohogar'}.csv")
    return raw / str(year) / "microdata" / relative


def read_concentrado(raw: Path, year: int) -> pd.DataFrame:
    path = source_file(raw, year, "concentrado")
    if year < 2014:
        df = pd.DataFrame(iter(DBF(str(path), encoding="latin1")))
        df.columns = df.columns.str.lower()
        df["id"] = df["folio"].str.strip()
        rename = {"hog": "peso", "edad": "edad_jefe", "tam_hog": "tot_integ",
                  "n_ocup": "ocupados", "ingcor": "ing_cor", "gasmon": "gasto_mon",
                  "estrato": "tam_loc"}
    else:
        df = pd.read_csv(path, dtype=str)
        df["id"] = df.folioviv.str.strip() + df.foliohog.str.strip()
        rename = {"factor_hog" if year == 2014 else "factor": "peso"}
    df = df.rename(columns=rename).set_index("id", verify_integrity=True)
    for col in ("peso", "edad_jefe", "tot_integ", "ocupados", "ing_cor", "gasto_mon", "menores", "tam_loc"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    for col in ("est_dis", "upm"):
        df[col] = df[col].astype(str).str.strip()
        if df[col].isin(["", "nan", "None"]).any():
            raise ValueError(f"{year}: diseño muestral incompleto")
    if not (df.peso.gt(0).all() and df.tot_integ.gt(0).all()):
        raise ValueError(f"{year}: ponderador o tamaño de hogar inválido")
    return df


def csv_expense_chunks(raw: Path, year: int):
    for table in ("gastoshogar", "gastospersona"):
        with pd.read_csv(source_file(raw, year, table), dtype=str,
                         usecols=["folioviv", "foliohog", "clave", "tipo_gasto", "gasto_tri"],
                         chunksize=150_000) as reader:
            yield from reader


def selected_expenses(raw: Path, year: int, ids: pd.Index):
    """Agrega claves necesarias; valida todas las llaves de cada tabla leída."""
    groups = {"alimentos_fuera_raw": FOOD_CODES[year]}
    if year < 2014:
        groups.update(recreacion_raw=RECREATION_CODES[year], transferencias=TRANSFER_CODES[year])
        path = source_file(raw, year, "gastos")
        # Explicit filename avoids accidentally reading the 1994 capital-outlay table.
        rows = ({"id": r["FOLIO"].strip(), "clave": r["CLAVE"].strip(), "monto": r["GAS_TRI"]}
                for r in DBF(str(path), encoding="latin1"))
        chunks = [pd.DataFrame(rows)]
    else:
        groups["hospedaje_extra"] = LODGING_EXTRA[year]
        chunks = csv_expense_chunks(raw, year)
    result = pd.DataFrame(0.0, index=ids, columns=list(groups))
    source_rows = 0
    for chunk in chunks:
        source_rows += len(chunk)
        if year >= 2014:
            chunk["id"] = chunk.folioviv.str.strip() + chunk.foliohog.str.strip()
        unknown = pd.Index(chunk.id.unique()).difference(ids)
        if len(unknown):
            raise ValueError(f"{year}: {len(unknown)} hogares de gastos sin concentrado")
        if year >= 2014:
            # Monetary co-payments can appear on in-kind G4/G6 records.
            # Official aggregates sum gasto_tri across types, not only G1.
            chunk["monto"] = chunk.gasto_tri
        chunk["clave"] = chunk.clave.str.strip()
        for name, codes in groups.items():
            part = chunk.loc[chunk.clave.isin(codes)].copy()
            part["monto"] = pd.to_numeric(part.monto.astype("string").str.strip().replace("", pd.NA), errors="raise").fillna(0)
            if part.monto.isna().any() or part.monto.lt(0).any():
                raise ValueError(f"{year}: gasto faltante o negativo en {name}")
            sums = part.groupby("id").monto.sum()
            result.loc[sums.index, name] += sums
    return result, source_rows


def load_wave(raw: Path, year: int):
    df = read_concentrado(raw, year)
    selected, source_rows = selected_expenses(raw, year, df.index)
    df = df.join(selected, validate="one_to_one")
    df["alimentos_fuera"] = df.alimentos_fuera_raw if year == 1994 else pd.to_numeric(df["fuera_hog" if year == 2004 else "ali_fuera"])
    if year == 1994:
        df["recreacion_hospedaje"] = df.recreacion_raw
    elif year == 2004:
        df["recreacion_hospedaje"] = pd.to_numeric(df.esparci)
    else:
        df["recreacion_hospedaje"] = pd.to_numeric(df.esparci) + pd.to_numeric(df.paq_turist) + df.hospedaje_extra
        df["transferencias"] = pd.to_numeric(df.transf_gas)
    df["h1c"] = df.alimentos_fuera + df.recreacion_hospedaje
    # Every published share is a household ratio, subsequently averaged with weights.
    for col in METRICS[:3]:
        df[f"share_{col}"] = df[col] / df.gasto_mon.where(df.gasto_mon.gt(0))
    net = df.gasto_mon - df.transferencias
    df["share_h1c_sin_transferencias"] = df.h1c / net.where(net.gt(0))
    valid = df.edad_jefe.ge(18)
    income = df.ing_cor / df.tot_integ
    cuts = [weighted_quantile(income[valid], df.peso[valid], q / 5) for q in range(1, 5)]
    df["quintil_ingreso_pc"] = np.searchsorted(cuts, income, side="left") + 1
    psus = df.groupby("est_dis").upm.nunique()
    if psus.lt(2).any():
        raise ValueError(f"{year}: estrato con una UPM; requiere decisión explícita")
    food_error = (df.alimentos_fuera - df.alimentos_fuera_raw).abs()
    recreation_error = (df.recreacion_hospedaje - df.recreacion_raw).abs() if year == 2004 else pd.Series([0.0])
    if food_error.max() > 0.10 or recreation_error.max() > 0.10:
        raise ValueError(f"{year}: discrepancia en conciliación de categorías")
    if df.gasto_mon.lt(0).any() or df.h1c.gt(df.gasto_mon + 0.10).any():
        raise ValueError(f"{year}: H1c excede gasto monetario")
    audit = {"anio": year, "n_hogares_fuente": len(df), "n_jefatura_adulta": int(valid.sum()),
             "n_edad_cero": int(df.edad_jefe.eq(0).sum()),
             "n_gasto_cero": int((valid & df.gasto_mon.le(0)).sum()), "n_neto_cero": int((valid & net.le(0)).sum()),
             "n_filas_gastos": source_rows, "n_estratos": len(psus), "n_upm": int(psus.sum()),
             "gl_diseno": int(psus.sum() - len(psus)), "min_upm_por_estrato": int(psus.min()),
             "max_error_alimentos_pesos": food_error.max(), "max_error_recreacion_2004_pesos": recreation_error.max() if year == 2004 else np.nan,
             "n_llaves_sin_hogar": 0, "n_h1c_mayor_gasto": 0}
    return df, audit


def survey_variance(df: pd.DataFrame, influence: np.ndarray) -> tuple[float, int]:
    """Taylor con UPM y estratos completos; aproximación con reemplazo, sin FPC."""
    units = df[["est_dis", "upm"]].copy()
    units["u"] = influence
    totals = units.groupby(["est_dis", "upm"], sort=False).u.sum()
    by_stratum = totals.groupby(level=0)
    counts = by_stratum.transform("size")
    if counts.lt(2).any():
        raise ValueError("No se admiten estratos de una UPM sin regla explícita")
    squared = (totals - by_stratum.transform("mean")) ** 2
    variance = (squared * counts / (counts - 1)).sum()
    return float(variance), int(len(totals) - totals.index.get_level_values(0).nunique())


def survey_mean(df: pd.DataFrame, values, domain, age_weights=None):
    values = np.asarray(values, dtype=float)
    weights = df.peso.to_numpy(dtype=float)
    valid = np.asarray(domain, dtype=bool) & np.isfinite(values)
    if not valid.any():
        raise ValueError("Dominio sin observaciones válidas")
    influence = np.zeros(len(df))
    if age_weights is None:
        point = np.average(values[valid], weights=weights[valid])
        influence[valid] = weights[valid] * (values[valid] - point) / weights[valid].sum()
    else:
        point = 0.0
        for age, share in age_weights.items():
            members = valid & df.edad_jefe.eq(age).to_numpy()
            if not members.any():
                raise ValueError(f"Sin soporte para estandarizar edad {age}")
            age_mean = np.average(values[members], weights=weights[members])
            point += share * age_mean
            influence[members] = share * weights[members] * (values[members] - age_mean) / weights[members].sum()
    variance, degrees = survey_variance(df, influence)
    se = np.sqrt(variance)
    margin = t.ppf(0.975, degrees) * se
    return {"estimacion": point, "error_estandar": se, "ic95_inferior": point - margin,
            "ic95_superior": point + margin, "n": int(valid.sum()), "hogares_expandidos": weights[valid].sum(),
            "gl_diseno": degrees}


def category_mapping():
    """Correspondencias operativas; los agregados oficiales conservan su alcance por ola."""
    rows = []
    for year in YEARS:
        modern = year >= 2014
        rows.extend([
            {"anio": year, "componente": "alimentos_fuera",
             "construccion": "gastos.GAS_TRI" if year == 1994 else ("concen.FUERA_HOG" if year == 2004 else "concentrado.ali_fuera"),
             "claves_o_columnas": ";".join(sorted(FOOD_CODES[year])),
             "nota": "Validado contra suma de gasto monetario de las claves; incluye copagos monetarios en registros mixtos."},
            {"anio": year, "componente": "recreacion_hospedaje",
             "construccion": "gastos.GAS_TRI" if year == 1994 else ("concen.ESPARCI" if year == 2004 else "esparci + paq_turist + gasto_tri de hospedaje adicional"),
             "claves_o_columnas": ";".join(sorted(RECREATION_CODES[year])) if not modern else "esparci;paq_turist;" + ";".join(sorted(LODGING_EXTRA[year])),
             "nota": "Incluye equipo, cultura, recreacion, paquetes de fiestas/turismo y hospedaje incluso no turistico. Agregados amplios, no productos identicos."},
            {"anio": year, "componente": "denominador_principal",
             "construccion": "concen.GASMON" if not modern else "concentrado.gasto_mon",
             "claves_o_columnas": "GASMON" if not modern else "gasto_mon", "nota": "Gasto corriente monetario oficial, incluidas transferencias."},
            {"anio": year, "componente": "resta_sensibilidad_transferencias",
             "construccion": "gastos.GAS_TRI" if not modern else "concentrado.transf_gas",
             "claves_o_columnas": ";".join(sorted(TRANSFER_CODES[year])) if not modern else "transf_gas",
             "nota": "Definicion propia de cada ola; en 2024 incluye comisiones financieras y asistencia, entre otros servicios."},
        ])
    return pd.DataFrame(rows)


def compare_waves(waves):
    """Tablas públicas agregadas; sin identificadores ni registros individuales."""
    ref = waves[2024]
    ref_young = ref.edad_jefe.between(18, 29) & ref.gasto_mon.gt(0)
    ref_weights = ref.loc[ref_young].groupby("edad_jefe").peso.sum()
    age_weights = (ref_weights / ref_weights.sum()).to_dict()
    profiles, sensitivity, composition, ranks = [], [], [], []
    for year, df in waves.items():
        for group, (low, high) in AGE_GROUPS.items():
            domain = df.edad_jefe.between(low, high)
            for metric in METRICS:
                profiles.append({"anio": year, "grupo_edad": group, "indicador": metric,
                                 **survey_mean(df, df[f"share_{metric}"], domain)})
        young = df.edad_jefe.between(18, 29)
        for metric in METRICS:
            sensitivity.append({"anio": year, "indicador": metric, "ajuste": "edades_simples_2024",
                                **survey_mean(df, df[f"share_{metric}"], young, age_weights)})
        composition_values = {"edad_media": df.edad_jefe, "integrantes": df.tot_integ,
                              "menores_12": df.menores, "ocupados": df.ocupados}
        for metric, values in composition_values.items():
            composition.append({"anio": year, "indicador": metric, **survey_mean(df, values, young)})
        composition.append({"anio": year, "indicador": "proporcion_hogares_jovenes_entre_jefaturas_adultas",
                            **survey_mean(df, young.astype(float), df.edad_jefe.ge(18))})
        for quintile in range(1, 6):
            domain = young & df.quintil_ingreso_pc.eq(quintile)
            ranks.append({"anio": year, "quintil_ingreso_pc": quintile,
                          **survey_mean(df, df.share_h1c, domain)})
    profiles, sensitivity = pd.DataFrame(profiles), pd.DataFrame(sensitivity)
    from itertools import combinations
    from .survey import difference, adjust_holm
    changes = []
    for adjustment, table in [("sin_ajuste", profiles[profiles.grupo_edad.eq("18–29")]), ("edades_simples_2024", sensitivity)]:
        for metric in METRICS:
            sub = table[table.indicador.eq(metric)].set_index("anio")
            for year, final_year in combinations(YEARS, 2):
                current, prior = sub.loc[final_year], sub.loc[year]
                contrast = difference(current.to_dict(), prior.to_dict(), independent=True)
                changes.append({"anio_base": year, "anio_final": final_year, "grupo_edad": "18–29", "indicador": metric,
                                "ajuste": adjustment, "familia": f"{adjustment}|{metric}",
                                "cambio_pp": contrast["estimacion"] * 100, "error_estandar_pp": contrast["error_estandar"] * 100,
                                "ic95_inferior_pp": contrast["ic95_inferior"] * 100, "ic95_superior_pp": contrast["ic95_superior"] * 100,
                                "gl_contraste": contrast["gl_diseno"], "p_valor": contrast["p_valor"]})
    changes = adjust_holm(pd.DataFrame(changes))
    return {"correspondencias": category_mapping(), "perfiles": profiles, "edades_ajustadas": sensitivity, "cambios": changes,
            "composicion": pd.DataFrame(composition), "quintiles": pd.DataFrame(ranks),
            "pesos_edad": pd.DataFrame({"edad_jefe": list(age_weights), "peso_referencia_2024": list(age_weights.values())})}
