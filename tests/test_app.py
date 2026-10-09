import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from analysis_ui import ALL_CARANDIRU, PENHA_SUFFIX, initiative_filter
from data_logic import load_collection


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.app = AppTest.from_file(str(self.root / "app.py"), default_timeout=30).run()

    def assertHealthy(self):
        self.assertEqual([e.message for e in self.app.exception], [])

    def test_global_metric_and_real_filter(self):
        self.assertHealthy()
        self.assertEqual(self.app.metric[0].value, "17.186")
        self.app.multiselect(key="inic_Nome da iniciativa").set_value(["Ato"]).run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[4].value,"12")
        self.assertEqual(self.app.metric[0].value,"17.186")

    def test_change_files_resets_filters(self):
        self.app.multiselect(key="inic_Nome da iniciativa").set_value(["Ato"]).run()
        penha = next(f for f in self.app.multiselect(key="inic_files").options if "MSSCPENHA" in f)
        self.app.multiselect(key="inic_files").set_value([penha]).run()
        self.assertHealthy()
        self.assertEqual(self.app.multiselect(key="inic_Nome da iniciativa").value,[])
        self.assertEqual(self.app.metric[4].value,"304")

    def test_empty_inventory_keeps_other_tab(self):
        self.app.multiselect(key="cat_files").set_value([]).run()
        self.assertHealthy()
        self.assertIsNotNone(self.app.multiselect(key="inic_files"))
        self.assertEqual(self.app.metric[1].value,"560")

    def test_representations_view(self):
        self.app.radio(key="cat_unit").set_value("Representações / arquivos (Geral)").run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[1].value,"574")
        self.app.multiselect(key="cat_Espécie/Tipo documental").set_value(["FME"]).run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[1].value,"39")

    def test_timeline_cloud_and_export(self):
        self.app.selectbox(key="cat_view").set_value("Linha do tempo (distribuição cronológica)").run()
        self.assertHealthy()
        self.app.selectbox(key="inic_view").set_value("Nuvem de palavras").run()
        self.assertHealthy()
        self.assertIn("Título do documento",self.app.multiselect(key="inic_cloud_fields").options)
        self.app.multiselect(key="inic_cloud_fields").set_value(["Ano","Proponente"]).run()
        self.assertHealthy()
        self.app.button(key="inic_prepare_docx").click().run()
        self.assertHealthy()
        self.assertTrue(self.app.session_state["inic_docx"].startswith(b"PK"))

    def test_intervention_origin_rules(self):
        _, ini = load_collection([p.name for p in self.root.glob("*MAPEAMENTOS*.xlsx")],self.root)
        self.assertEqual(len(initiative_filter(ini,[ALL_CARANDIRU])),256)
        self.assertEqual(len(initiative_filter(ini,["Difusão"+PENHA_SUFFIX])),276)
        self.assertEqual(len(initiative_filter(ini,[ALL_CARANDIRU,"Difusão"+PENHA_SUFFIX])),532)

    def test_configured_password_protects_data(self):
        app = AppTest.from_file(str(self.root/"app.py"),default_timeout=30)
        app.secrets["senha_porta"] = "senha-apenas-do-teste"
        app.run()
        self.assertEqual(len(app.metric),0)
        app.text_input(key="input_senha").set_value("senha-apenas-do-teste").run()
        self.assertEqual([e.message for e in app.exception],[])
        self.assertEqual(app.metric[0].value,"17.186")


if __name__ == "__main__":
    unittest.main()
