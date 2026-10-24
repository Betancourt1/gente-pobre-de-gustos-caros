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
    """Cuantil ponderado (interpolación lineal sobre pesos acumulados)."""
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
    m = pd.Series(mask).fillna(False).to_numpy(dtype=bool)
    w = _float_array(weights)
    valid = np.isfinite(w) & (w > 0)
    if not valid.any():
        return float("nan")
    return float(w[valid & m].sum() / w[valid].sum())


def add_weighted_deciles(
    df: pd.DataFrame, value_col: str, weight_col: str, out_col: str = "decil"
) -> pd.DataFrame:
    """Asigna deciles 1-10 usando cortes ponderados."""
    out = df.copy()
    v = pd.to_numeric(out[value_col], errors="coerce")
    w = pd.to_numeric(out[weight_col], errors="coerce")
    valid = v.notna() & w.notna() & (w > 0)
    cuts = [
        weighted_quantile(v[valid], w[valid], q)
        for q in np.arange(0.1, 1.0, 0.1)
    ]
    out[out_col] = pd.cut(
        v, bins=[-np.inf, *cuts, np.inf], labels=range(1, 11), include_lowest=True
    ).astype("Int64")
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
    """Participación del gasto total que concentra el top `top` de hogares."""
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
    idx = int(np.searchsorted(cw, cutoff, side="left"))
    idx = min(idx, v.size - 1)
    return float((v[: idx + 1] * w[: idx + 1]).sum() / (v * w).sum())
