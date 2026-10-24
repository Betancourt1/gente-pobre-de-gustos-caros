"""Rutas y parámetros compartidos del proyecto."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ENIGH_DIR = ROOT / "conjunto_de_datos_enigh2024_ns_csv"
ENSAFI_DIR = ROOT / "conjunto_de_datos_ensafi_2023_csv"

ENIGH_TABLES = {
    "concentradohogar": ENIGH_DIR
    / "conjunto_de_datos_concentradohogar_enigh2024_ns"
    / "conjunto_de_datos"
    / "conjunto_de_datos_concentradohogar_enigh2024_ns.csv",
    "poblacion": ENIGH_DIR
    / "conjunto_de_datos_poblacion_enigh2024_ns"
    / "conjunto_de_datos"
    / "conjunto_de_datos_poblacion_enigh2024_ns.csv",
    "viviendas": ENIGH_DIR
    / "conjunto_de_datos_viviendas_enigh2024_ns"
    / "conjunto_de_datos"
    / "conjunto_de_datos_viviendas_enigh2024_ns.csv",
    "gastoshogar": ENIGH_DIR
    / "conjunto_de_datos_gastoshogar_enigh2024_ns"
    / "conjunto_de_datos"
    / "conjunto_de_datos_gastoshogar_enigh2024_ns.csv",
    "gastos_catalogo": ENIGH_DIR
    / "conjunto_de_datos_gastoshogar_enigh2024_ns"
    / "catalogos"
    / "gastos.csv",
}

ENSAFI_TABLES = {
    "tmodulo": ENSAFI_DIR
    / "conjunto_de_datos_tmodulo_ensafi_2023"
    / "conjunto_de_datos"
    / "conjunto_de_datos_tmodulo_ensafi_2023.csv",
    "thogar": ENSAFI_DIR
    / "conjunto_de_datos_thogar_ensafi_2023"
    / "conjunto_de_datos"
    / "conjunto_de_datos_thogar_ensafi_2023.csv",
    "tvivienda": ENSAFI_DIR
    / "conjunto_de_datos_tvivienda_ensafi_2023"
    / "conjunto_de_datos"
    / "conjunto_de_datos_tvivienda_ensafi_2023.csv",
}

PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
TABLES = ROOT / "reports" / "tables"

# Edad del jefe/a del hogar (ENIGH) y de la persona elegida (ENSAFI).
AGE_BINS = [18, 30, 45, 60, 200]
AGE_LABELS = ["18-29", "30-44", "45-59", "60+"]

# Paleta consistente para todas las figuras.
COLORS = {
    "young": "#d1495b",
    "adult": "#00798c",
    "older": "#30638e",
    "senior": "#8d99ae",
    "accent": "#edae49",
    "gray": "#6c757d",
    "light": "#e9ecef",
    "good": "#2a9d8f",
    "bad": "#e76f51",
}

AGE_COLORS = {
    "18-29": COLORS["young"],
    "30-44": COLORS["adult"],
    "45-59": COLORS["older"],
    "60+": COLORS["senior"],
}

SOURCE_ENIGH = (
    "Fuente: INEGI, ENIGH 2024 Nueva Serie. Cálculos propios con factor de expansión."
)
SOURCE_ENSAFI = (
    "Fuente: INEGI/CONDUSEF, ENSAFI 2023. Cálculos propios con factor de expansión."
)
