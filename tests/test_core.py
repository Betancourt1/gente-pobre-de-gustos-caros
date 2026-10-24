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
from gpdgc.weights import gini, top_share, weighted_mean, weighted_share  # noqa: E402


class TaxonomyTests(unittest.TestCase):
    def test_canastas(self) -> None:
        df = pd.DataFrame(
            {
                "clave": ["011131", "071110", "081404", "111111", "132101", "171111", "T901"],
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


if __name__ == "__main__":
    unittest.main()
