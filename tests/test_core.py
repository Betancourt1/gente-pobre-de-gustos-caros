"""Pruebas rápidas de la clasificación de gastos y de las ponderaciones."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gpdgc.taxonomy import add_expense_flags  # noqa: E402
from gpdgc.weights import (  # noqa: E402
    add_weighted_deciles, gini, top_share, weighted_mean, weighted_share, weighted_quantile,
)


class TaxonomyTests(unittest.TestCase):
    def test_canastas(self) -> None:
        df = pd.DataFrame(
            {
                "clave": ["011131", "071110", "081404", "111111", "132111", "171111", "T901"],
                "gasto": [100.0, 200.0, 30.0, 50.0, 25.0, 999.0, 999.0],
            }
        )
        out = add_expense_flags(df)
        self.assertTrue(out.loc[0, "es_consumo"])
        self.assertFalse(out.loc[5, "es_consumo"])  # capítulo 17
        self.assertFalse(out.loc[6, "es_consumo"])  # regalos
        self.assertTrue(out.loc[1, "d2_gusto_visible"])  # auto nuevo
        self.assertTrue(out.loc[2, "d2_gusto_visible"])  # streaming
        self.assertTrue(out.loc[3, "d2_gusto_visible"])  # restaurantes
        self.assertTrue(out.loc[4, "d2_gusto_visible"])  # bolsos/joyería
        self.assertEqual(out.loc[3, "capitulo"], "11")
        self.assertEqual(out.loc[6, "capitulo"], "T9")

    def test_accesorios_no_incluyen_funeral_bebe_o_mochilas(self):
        df = pd.DataFrame({"clave": ["132111", "132112", "132911", "132915",
                                     "13291A", "132916", "132914", "132113"]})
        self.assertEqual(add_expense_flags(df).d2_gusto_visible.tolist(),
                         [True, True, True, True, False, False, False, False])


class WeightTests(unittest.TestCase):
    def test_media_y_share(self) -> None:
        values = [1.0, 2.0, 3.0]
        weights = [1.0, 1.0, 2.0]
        self.assertAlmostEqual(weighted_mean(values, weights), 2.25)
        self.assertAlmostEqual(weighted_share([True, False, False], weights), 0.25)

    def test_concentracion(self) -> None:
        self.assertAlmostEqual(gini([1.0, 1.0], [1.0, 1.0]), 0.0)
        self.assertAlmostEqual(top_share([1.0, 0.0], [1.0, 1.0], top=0.5), 1.0)
        self.assertTrue(np.isnan(gini([], [])))

    def test_top_incluye_fraccion_exacta_del_peso(self):
        self.assertAlmostEqual(top_share([1, 1], [1, 1], .1), .1)
        self.assertAlmostEqual(top_share([100, 10], [3, 7], .2), 200 / 370)
        self.assertEqual(top_share([1, 1], [1, 1], 0), 0)
        self.assertEqual(top_share([1, 1], [1, 1], 1), 1)

    def test_share_excluye_desconocidos(self):
        self.assertEqual(weighted_share([True, pd.NA], [1, 9]), 1)
        self.assertTrue(np.isnan(weighted_share([pd.NA], [1])))

    def test_deciles_con_empates_y_sin_datos(self):
        data = pd.DataFrame({"x": [1] * 20 + [np.nan, 2], "w": [1] * 21 + [0]})
        result = add_weighted_deciles(data, "x", "w")
        self.assertTrue(result.decil.iloc[:20].eq(1).all())
        self.assertTrue(result.decil.iloc[20:].isna().all())
        self.assertTrue(add_weighted_deciles(data.iloc[20:], "x", "w").decil.isna().all())

    def test_cuantiles_sin_interpolacion(self):
        self.assertEqual(weighted_quantile([1, 10], [1, 3], .5), 10)
        self.assertEqual(weighted_quantile([1, 10], [1, 3], 0), 1)
        self.assertEqual(weighted_quantile([1, 10], [1, 3], 1), 10)

    def test_deciles_sin_desplazar_cortes_por_redondeo(self):
        data = pd.DataFrame({"x": range(1, 11), "w": [1] * 10})
        self.assertEqual(add_weighted_deciles(data, "x", "w").decil.tolist(), list(range(1, 11)))


if __name__ == "__main__":
    unittest.main()
