"""Utilidades de ponderación y estadística descriptiva."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _float_array(values) -> np.ndarray:
    """Convierte Series, listas o arreglos a float, sin romper con pandas 3."""
    return np.asarray(pd.to_numeric(values, errors="coerce"), dtype=float)


def weighted_mean(values, weights) -> float:
    v = _float_array(values)
    w = _float_array(weights)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not mask.any():
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def weighted_quantile(values, weights, q: float) -> float:
    """Inversa de la distribución empírica ponderada, sin interpolación."""
    if not 0 <= q <= 1:
        raise ValueError("q debe estar entre 0 y 1")
    v = _float_array(values)
    w = _float_array(weights)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[mask], w[mask]
    if v.size == 0:
        return float("nan")
    order = np.argsort(v, kind="mergesort")
    v, w = v[order], w[order]
    cw = np.cumsum(w)
    cutoff = q * cw[-1]
    idx = int(np.searchsorted(cw, cutoff, side="left"))
    idx = min(idx, v.size - 1)
    return float(v[idx])


def weighted_share(mask, weights) -> float:
    """Proporción entre respuestas conocidas con ponderador válido."""
    answers = pd.Series(mask)
    m = answers.fillna(False).to_numpy(dtype=bool)
    w = _float_array(weights)
    valid = answers.notna().to_numpy() & np.isfinite(w) & (w > 0)
    if not valid.any():
        return float("nan")
    return float(w[valid & m].sum() / w[valid].sum())


def add_weighted_deciles(
    df: pd.DataFrame, value_col: str, weight_col: str, out_col: str = "decil"
) -> pd.DataFrame:
    """Cortes ponderados; los empates quedan juntos y pueden dejar deciles vacíos."""
    out = df.copy()
    v = pd.to_numeric(out[value_col], errors="coerce")
    w = pd.to_numeric(out[weight_col], errors="coerce")
    valid = np.isfinite(v) & np.isfinite(w) & (w > 0)
    out[out_col] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    if not valid.any():
        return out
    cuts = [
        weighted_quantile(v[valid], w[valid], i / 10)
        for i in range(1, 10)
    ]
    out.loc[valid, out_col] = np.searchsorted(cuts, v[valid], side="left") + 1
    return out


def gini(values, weights) -> float:
    """Coeficiente de Gini ponderado."""
    v = _float_array(values)
    w = _float_array(weights)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0) & (v >= 0)
    v, w = v[mask], w[mask]
    if v.size == 0 or v.sum() == 0:
        return float("nan")
    order = np.argsort(v, kind="mergesort")
    v, w = v[order], w[order]
    cw = np.cumsum(w)
    cv = np.cumsum(v * w)
    # Curva de Lorenz con el origen (0, 0); Gini = 1 - 2 * área.
    lorentz_x = np.concatenate(([0.0], cw / cw[-1]))
    lorentz_y = np.concatenate(([0.0], cv / cv[-1]))
    area = np.trapezoid(lorentz_y, lorentz_x)
    return float(1 - 2 * area)


def lorenz_curve(values, weights, n_points: int = 200):
    """Devuelve x, y de la curva de Lorenz (participación acumulada)."""
    v = _float_array(values)
    w = _float_array(weights)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0) & (v >= 0)
    v, w = v[mask], w[mask]
    if v.size == 0 or v.sum() == 0:
        return np.array([0, 1]), np.array([0, 1])
    order = np.argsort(v, kind="mergesort")
    v, w = v[order], w[order]
    cw = np.cumsum(w) / np.sum(w)
    cv = np.cumsum(v * w) / np.sum(v * w)
    x = np.concatenate(([0.0], cw))
    y = np.concatenate(([0.0], cv))
    # Remuestreo para suavizar la línea.
    grid = np.linspace(0, 1, n_points)
    return grid, np.interp(grid, x, y)


def top_share(values, weights, top: float = 0.10) -> float:
    """Top ponderado, incluyendo solo la fracción del peso que alcanza el corte."""
    if not 0 <= top <= 1:
        raise ValueError("top debe estar entre 0 y 1")
    v = _float_array(values)
    w = _float_array(weights)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0) & (v >= 0)
    v, w = v[mask], w[mask]
    if v.size == 0 or v.sum() == 0:
        return float("nan")
    order = np.argsort(-v, kind="mergesort")
    v, w = v[order], w[order]
    cw = np.cumsum(w)
    cutoff = top * cw[-1]
    included = np.minimum(w, np.maximum(0, cutoff - (cw - w)))
    return float((v * included).sum() / (v * w).sum())
