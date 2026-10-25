"""Checks for survey-domain uncertainty, age standardization and source selection."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from gpdgc.historical import (FOOD_CODES, LODGING_EXTRA, RECREATION_CODES,
                               selected_expenses, source_file, survey_mean, survey_variance)


class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"est_dis": ["a", "a", "b", "b"],
                                "upm": ["1", "2", "1", "2"], "peso": [1., 1., 1., 1.],
                                "edad_jefe": [20, 28, 20, 28]})

    def test_stratified_variance_and_mean(self):
        result = survey_mean(self.df, [0, 2, 4, 6], [True] * 4)
        self.assertEqual(result["estimacion"], 3)
        self.assertEqual(result["gl_diseno"], 2)
        self.assertAlmostEqual(result["error_estandar"] ** 2, .5)

    def test_domain_retains_zero_influence_psus(self):
        result = survey_mean(self.df, [0, 2, 4, 6], [True, False, True, False])
        self.assertEqual(result["n"], 2)
        self.assertEqual(result["estimacion"], 2)
        self.assertAlmostEqual(result["error_estandar"] ** 2, 2)
        self.assertEqual(result["gl_diseno"], 2)

    def test_mean_of_household_ratios_not_ratio_of_totals(self):
        self.df["peso"] = [1, 3, 1, 3]
        result = survey_mean(self.df, np.array([1, 9, 1, 9]) / [2, 10, 2, 10], [True] * 4)
        self.assertAlmostEqual(result["estimacion"], .8)
        self.assertNotAlmostEqual(result["estimacion"], 56 / 64)

    def test_age_standardization(self):
        result = survey_mean(self.df, [0, 2, 4, 6], [True] * 4, {20: .75, 28: .25})
        self.assertAlmostEqual(result["estimacion"], 2.5)
        self.assertAlmostEqual(result["error_estandar"] ** 2, .5)

    def test_singleton_and_missing_age_fail_explicitly(self):
        with self.assertRaises(ValueError):
            survey_variance(self.df.iloc[:1], np.array([0.]))
        with self.assertRaises(ValueError):
            survey_mean(self.df, [0, 2, 4, 6], [True] * 4, {21: 1.})

    def test_mapping_preserves_broad_recreation(self):
        self.assertIn("N005", RECREATION_CODES[1994])
        self.assertIn("N005", RECREATION_CODES[2004])
        self.assertEqual(LODGING_EXTRA[2014], {"N005"})
        self.assertIn("112030", LODGING_EXTRA[2024])
        for year in (1994, 2004):
            self.assertFalse(FOOD_CODES[year] & RECREATION_CODES[year])

    def test_person_and_household_monetary_expenses_are_both_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            for table, code, amount in [("gastoshogar", "N005", "12"), ("gastospersona", "A243", "8")]:
                path = source_file(raw, 2014, table)
                path.parent.mkdir(parents=True)
                pd.DataFrame({"folioviv": ["001", "001", "001"], "foliohog": ["1", "1", "1"],
                              "clave": [code, code, code], "tipo_gasto": ["G1", "G4", "G6"],
                              "gasto_tri": [amount, " ", "3"]}).to_csv(path, index=False)
            result, rows = selected_expenses(raw, 2014, pd.Index(["0011"]))
            self.assertEqual(rows, 6)
            self.assertEqual(result.loc["0011", "hospedaje_extra"], 15)
            self.assertEqual(result.loc["0011", "alimentos_fuera_raw"], 11)
            with self.assertRaises(ValueError):
                selected_expenses(raw, 2014, pd.Index(["0021"]))


if __name__ == "__main__":
    unittest.main()
