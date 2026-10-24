"""Clasificación de los gastos del hogar en canastas analíticas.

La ENIGH codifica cada renglón de gasto con una clave de 6 dígitos. Los dos
primeros dígitos identifican el capítulo de la COICOP adaptada por el INEGI.
Este módulo traduce esas claves a tres definiciones de "gusto caro" que se
reportan por separado para no depender de una sola etiqueta normativa.

Capítulos (verificados contra catalogos/gastos.csv):
    01 Alimentos y bebidas no alcohólicas
    02 Bebidas alcohólicas y tabaco
    03 Vestido y calzado
    04 Vivienda, agua, electricidad y combustibles
    05 Mobiliario, equipo y mantenimiento del hogar
    06 Salud
    07 Transporte
    08 Comunicaciones
    09 Recreación, cultura y deporte
    10 Educación
    11 Restaurantes y hoteles
    12 Seguros y servicios financieros
    13 Cuidados personales y otros
    17 Claves especiales (transferencias, erogaciones, etc.)
    18 Alimentos/bebidas empaquetados, despensas y entrega a domicilio
    T9 Regalos
"""

from __future__ import annotations

import pandas as pd

CHAPTER_LABELS = {
    "01": "Alimentos y bebidas no alcohólicas",
    "02": "Bebidas alcohólicas y tabaco",
    "03": "Vestido y calzado",
    "04": "Vivienda, agua, electricidad y combustibles",
    "05": "Mobiliario y equipo del hogar",
    "06": "Salud",
    "07": "Transporte",
    "08": "Comunicaciones",
    "09": "Recreación, cultura y deporte",
    "10": "Educación",
    "11": "Restaurantes y hoteles",
    "12": "Seguros y servicios financieros",
    "13": "Cuidados personales y otros",
    "17": "Claves especiales (transferencias y erogaciones)",
    "18": "Alimentos empaquetados, despensas y entrega a domicilio",
    "T9": "Regalos",
}

# Capítulos que forman parte del gasto de consumo del hogar. Se excluyen 17
# (erogaciones/transferencias, que no son consumo) y T9 (regalos a terceros).
CONSUMPTION_CHAPTERS = {f"{i:02d}" for i in range(1, 14)} | {"18"}

# D1: definición amplia de gasto discrecional.
D1_CHAPTERS = {"02", "05", "07", "08", "09", "11", "12", "13"}

# D2: "gusto caro visible": alcohol/tabaco, recreación, restaurantes/hoteles,
# accesorios personales, streaming/TV de paga y automóviles nuevos.
D2_CHAPTERS = {"02", "09", "11"}
D2_PERSONAL_KEYS = {
    "132111",  # bisutería
    "132112",  # relojes de pulso
    "132911",  # bolsas
    "132912",  # carteras y monederos
    "132913",  # portafolios
    "132915",  # maletas para viaje
}
D2_STREAMING_KEYS = {"081404", "083921", "083922", "083923", "083924"}
D2_NEW_CAR_KEY = "071110"

# D3: "vicios": alcohol, tabaco y narcóticos.
D3_CHAPTERS = {"02"}


def add_expense_flags(df: pd.DataFrame, clave_col: str = "clave") -> pd.DataFrame:
    """Agrega capítulo y banderas D1/D2/D3 a un DataFrame de gastos."""
    out = df.copy()
    clave = out[clave_col].astype("string").str.strip()
    chapter = clave.str[:2]
    chapter = chapter.where(~clave.str.upper().str.startswith("T"), "T9")

    out["capitulo"] = chapter
    out["capitulo_label"] = chapter.map(CHAPTER_LABELS).fillna("Otros")
    out["es_consumo"] = chapter.isin(CONSUMPTION_CHAPTERS)
    out["d1_discrecional"] = chapter.isin(D1_CHAPTERS)
    out["d2_gusto_visible"] = (
        chapter.isin(D2_CHAPTERS)
        | clave.isin(D2_PERSONAL_KEYS)
        | clave.isin(D2_STREAMING_KEYS)
        | clave.eq(D2_NEW_CAR_KEY)
    )
    out["d3_vicios"] = chapter.isin(D3_CHAPTERS)
    return out
