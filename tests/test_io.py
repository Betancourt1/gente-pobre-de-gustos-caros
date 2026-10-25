"""Regresiones con CSV sintéticos; no requieren descargar microdatos."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gpdgc import config, io
from gpdgc.weights import weighted_share


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        ids = ["0100000001", "1000000001", "1000000002"]
        tables = {
            "concentradohogar": pd.DataFrame({
                "folioviv": ids, "foliohog": ["1"] * 3, "factor": [1] * 3,
                "edad_jefe": [30, 65, 17], "tot_integ": [3, 1, 1],
                "menores": [0, 0, 0], "ing_cor": [1000, 500, 100],
                "gasto_mon": [160, 70, 0],
                "est_dis": ["01"] * 3, "upm": ["01", "02", "03"],
            }),
            "viviendas": pd.DataFrame({
                "folioviv": ids, "tenencia": ["1", "3", "3"], "renta": [100, 0, 0],
                "pago_viv": [0] * 3, "tot_resid": [4, 1, 1], "tot_hog": [1] * 3,
                "tam_loc": ["1"] * 3, "est_socio": ["1"] * 3,
            }),
            "poblacion": pd.DataFrame({
                "folioviv": [ids[0]] * 4 + ids[1:], "foliohog": ["1"] * 6,
                "numren": ["01", "02", "03", "04", "01", "01"],
                "parentesco": ["101", "301", "301", "401", "101", "101"],
                "sexo": ["1"] * 6, "edad": [30, 13, 14, 8, 65, 17], "factor": [1] * 6,
            }),
            "gastoshogar": pd.DataFrame({
                "folioviv": [ids[0]] * 3 + [ids[1]], "foliohog": ["1"] * 4,
                "clave": ["011131", "111111", "111111", "13291A"],
                "tipo_gasto": ["G1", "G1", "G2", "G1"], "gasto_tri": [100, 20, 40, 50],
            }),
            "gastospersona": pd.DataFrame({
                "folioviv": [ids[0], ids[0], ids[1]], "foliohog": ["1"] * 3,
                "clave": ["073111", "101111", "132111"], "tipo_gasto": ["G1"] * 3,
                "gasto_tri": [10, 30, 20],
            }),
        }
        self.paths = {name: root / f"{name}.csv" for name in tables}
        for name, table in tables.items():
            table.to_csv(self.paths[name], index=False)
        self.enterContext(patch.object(config, "ENIGH_TABLES", self.paths))
        self.enterContext(patch.object(config, "PROCESSED", root / "new-cache"))

    def test_cruce_gastos_personales_y_equivalencia(self):
        h = io.load_enigh_hogares(force_gastos=True).set_index("folioviv")
        self.assertEqual(len(h), 2)  # jefe de 17 años fuera del universo adulto
        self.assertIn(("01", "03"), h.attrs["design_units"])  # PSU retained for domain variance
        young = h.loc["0100000001"]
        self.assertEqual(young.gasto_total_g1, 160)
        self.assertEqual(young.gasto_d2, 20)
        self.assertEqual(young.n_personas, 3)  # excluye trabajador doméstico
        self.assertEqual(young.n_menores_14, 1)
        self.assertAlmostEqual(young.escala_eq, 1.8)
        self.assertAlmostEqual(young.carga_renta, .3)
        self.assertEqual(h.loc["1000000001", "gasto_d2"], 20)
        self.assertTrue(h.tiene_registros_gasto.all())
        self.assertTrue((config.PROCESSED / "gastos_consumo_g1_v2.parquet").exists())
        pd.testing.assert_frame_equal(io.load_gastos_hogar(), io.load_gastos_hogar(force=True))

    def test_cruce_no_oculta_claves_huerfanas(self):
        p = self.paths["gastospersona"]
        data = pd.read_csv(p, dtype="string")
        data.loc[0, "folioviv"] = "9999999999"
        data.to_csv(p, index=False)
        with self.assertRaisesRegex(ValueError, "claves de gastos"):
            io.load_enigh_hogares(force_gastos=True)

    def test_rechaza_duplicados_en_fuentes(self):
        p = self.paths["viviendas"]
        data = pd.read_csv(p, dtype="string")
        pd.concat([data, data.iloc[:1]]).to_csv(p, index=False)
        with self.assertRaises(pd.errors.MergeError):
            io.load_enigh_hogares(force_gastos=True)


class MonthlyComparisonTests(unittest.TestCase):
    def test_periodos_ceros_desconocidos_y_topes(self):
        data = pd.DataFrame({
            "P5_19": [1000, 2000, 0, pd.NA, 98000, 1000],
            "INGRESO_M": [4300, 4000, 0, pd.NA, 98000, 4300],
            "P5_21": [2000, 5000, 100, 100, 99000, 98000],
        }, dtype="Float64")
        out = io.add_monthly_comparison(data)
        self.assertEqual(out.comparable_ingreso_gasto.tolist(), [True, True, True, False, False, False])
        self.assertEqual(out.gasto_supera_ingreso_laboral.iloc[:3].tolist(), [False, True, True])
        self.assertTrue(out.gasto_supera_ingreso_laboral.iloc[3:].isna().all())
        self.assertAlmostEqual(weighted_share(out.gasto_supera_ingreso_laboral, [1] * 6), 2 / 3)


if __name__ == "__main__":
    unittest.main()
