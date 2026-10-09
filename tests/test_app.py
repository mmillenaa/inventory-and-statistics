import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from analysis_ui import category_label
from data_logic import load_collection, category_options, filter_categories, faceted_options
from unittest.mock import Mock, patch
import pandas as pd


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        api = pd.DataFrame([{"Título da base": "Publicação automática de teste", "Autores": "Machado, Maíra Rocha", "Identificador": "doi:teste/API", "Link de acesso": "https://example.org/publicacao"}])
        self.api_mock = patch("integrations.author_publications", return_value=api)
        self.api_mock.start()
        self.addCleanup(self.api_mock.stop)
        response = Mock(status_code=200, content=b"<html></html>")
        self.web_mock = patch("requests.get", return_value=response)
        self.web_mock.start()
        self.addCleanup(self.web_mock.stop)
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
        carandiru = next(e for e in self.app.checkbox if e.key.startswith("inic_source_") and "REMEMORA-CARANDIRU" in e.label)
        carandiru.set_value(False).run()
        self.assertHealthy()
        self.assertEqual(self.app.multiselect(key="inic_Nome da iniciativa").value,[])
        self.assertEqual(self.app.metric[4].value,"304")

    def test_empty_inventory_keeps_other_tab(self):
        for source in self.app.checkbox:
            if source.key.startswith("cat_source_"):
                source.set_value(False)
        self.app.run()
        self.assertHealthy()
        self.assertEqual(len([e for e in self.app.checkbox if e.key.startswith("inic_source_")]),2)
        self.assertEqual(self.app.metric[1].value,"560")

    def test_inventory_counts_descriptions_without_unit_switch(self):
        self.assertHealthy()
        self.assertEqual(self.app.metric[1].value,"348")
        self.assertFalse(any(e.key == "cat_unit" for e in self.app.radio))
        self.app.multiselect(key="cat_Gênero documental").set_value(["ICO"]).run()
        self.assertHealthy()
        self.assertGreater(int(self.app.metric[1].value),0)
        self.assertEqual(self.app.multiselect(key="cat_Espécie/Tipo documental").options,["Fotografia — FOT", "Planta — PLN", "Relatório — REL"])

    def test_timeline_cloud_and_export(self):
        self.app.selectbox(key="cat_view").set_value("Linha do tempo (distribuição cronológica)").run()
        self.assertHealthy()
        self.app.selectbox(key="inic_view").set_value("Nuvem de palavras").run()
        self.assertHealthy()
        self.assertEqual(self.app.multiselect(key="inic_cloud_fields").options,["Nome da iniciativa", "Ano", "Fonte/Origem", "Proponente"])
        self.assertTrue(any("Ano (G)" in e.value and "Ano (H)" in e.value and "Fonte/Origem (M)" in e.value and "Fonte/Origem (N)" in e.value for e in self.app.caption))
        self.app.multiselect(key="inic_cloud_fields").set_value(["Ano","Proponente"]).run()
        self.assertHealthy()
        self.assertFalse(any("Word" in e.label for e in self.app.button))
        self.assertTrue(any(e.key == "inic_csv" for e in self.app.get("download_button")))

    def test_intervention_uses_actual_field_and_regular_multiselect(self):
        control = self.app.multiselect(key="inic_Intervenção")
        self.assertEqual(control.value,[])
        self.assertEqual(control.options,["Manifestação artístico-cultural", "Produção midiática"])
        control.set_value(["Produção midiática"]).run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[4].value,"344")
        self.app.multiselect(key="inic_Intervenção").set_value([]).run()
        self.assertEqual(self.app.metric[4].value,"560")

    def test_mapping_filters_follow_other_selections(self):
        self.app.multiselect(key="inic_Nome da iniciativa").set_value(["Ato"]).run()
        self.assertHealthy()
        _, frame = load_collection([p.name for p in self.root.glob("*MAPEAMENTOS*.xlsx")],self.root)
        expected = category_options(filter_categories(frame,{"Nome da iniciativa":["Ato"]}),"Intervenção")
        self.assertEqual(self.app.multiselect(key="inic_Intervenção").options,expected)
        self.assertEqual(self.app.metric[4].value,"12")

    def test_search_sources_clear_button_and_hidden_internal_fields(self):
        self.app.text_input(key="cat_search").set_value("casa").run()
        self.assertHealthy()
        self.assertTrue(any("correspondências nos campos" in e.value and "Título descritivo" in e.value for e in self.app.caption))
        self.app.selectbox(key="cat_view").set_value("Frequências categoriais").run()
        self.assertHealthy()
        for element in self.app.dataframe:
            self.assertNotIn("Conflito de código",element.value.columns)
            self.assertNotIn("Representações vinculadas",element.value.columns)
        self.assertTrue(any("Campo de origem:" in e.value for e in self.app.caption))
        self.app.button(key="cat_clear_search").click().run()
        self.assertHealthy()
        self.assertEqual(self.app.text_input(key="cat_search").value,"")
        self.assertEqual(self.app.metric[1].value,"348")

    def test_search_change_reconciles_existing_filters(self):
        self.app.multiselect(key="cat_Espécie/Tipo documental").set_value(["PLN"]).run()
        self.app.text_input(key="cat_search").set_value("mãe").run()
        self.assertHealthy()
        self.assertGreater(int(self.app.metric[1].value),0)
        self.assertEqual(self.app.multiselect(key="cat_Espécie/Tipo documental").value,[])

    def test_original_description_style_and_removed_controls(self):
        self.assertTrue(any("class='desc-lista'" in e.value for e in self.app.markdown))
        sources=[e for e in self.app.checkbox if "_source_" in e.key]
        self.assertEqual(len(sources),8)
        self.assertTrue(all(e.value for e in sources))
        self.assertFalse(any("Selecione as planilhas" in e.label for e in self.app.multiselect))
        self.assertFalse(any("pendências" in e.label or "Editar referência" in e.label for e in self.app.expander))
        self.assertFalse(any("Consultar publicações" in e.label or "Atualizar equipe" in e.label for e in self.app.checkbox))
        self.assertFalse(any("Referência para copiar" in e.label for e in self.app.text_area))
        self.assertTrue(any("Publicação automática de teste" in e.value.to_string() for e in self.app.dataframe))

    def test_legacy_password_does_not_restrict_access(self):
        app = AppTest.from_file(str(self.root/"app.py"),default_timeout=30)
        app.secrets["senha_porta"] = "senha-apenas-do-teste"
        app.run()
        self.assertFalse(any(element.key == "input_senha" for element in app.text_input))
        self.assertEqual([e.message for e in app.exception],[])
        self.assertEqual(app.metric[0].value,"17.186")

    def test_source_checkbox_stays_off_until_selected_again(self):
        source = next(e for e in self.app.checkbox if e.key.startswith("cat_source_") and "CPOS" in e.label)
        source.set_value(False).run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[1].value,"335")
        self.app.selectbox(key="cat_view").set_value("Frequências categoriais").run()
        self.assertHealthy()
        self.assertFalse(self.app.checkbox(key=source.key).value)
        self.app.checkbox(key=source.key).set_value(True).run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[1].value,"348")

    def test_all_frequency_fields_use_words_in_graph_tables(self):
        self.app.selectbox(key="cat_view").set_value("Frequências categoriais").run()
        for field, expected in [("Gênero documental","Audiovisual"), ("Espécie/Tipo documental","Filme"),
                                ("Técnica de registro","Técnica não determinada"), ("Forma documental","Matriz bruta")]:
            self.app.selectbox(key="cat_frequency_field").set_value(field).run()
            self.assertHealthy()
            frequency=next(e.value for e in self.app.dataframe if "Categoria" in e.value.columns)
            self.assertIn(expected,frequency["Categoria"].tolist())
            self.assertFalse(set(frequency["Categoria"]) & {"AVS","ICO","FLG","TXT","MT0","MB0","NDT","NDG","DGZ","FOT","FME"})
        self.assertIn("Audiovisual — AVS",self.app.multiselect(key="cat_Gênero documental").options)
        self.assertIn("Matriz bruta — MT0",self.app.multiselect(key="cat_Forma documental").options)

    def test_empty_cloud_selection_and_no_match_do_not_crash(self):
        self.app.selectbox(key="inic_view").set_value("Nuvem de palavras").run()
        self.app.multiselect(key="inic_cloud_fields").set_value([]).run()
        self.assertHealthy()
        self.app.text_input(key="inic_search").set_value("termo_inexistente_935814").run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[4].value,"0")
        self.assertTrue(all(not e.options for e in self.app.multiselect if e.key in {"inic_Nome da iniciativa","inic_Intervenção","inic_Abrangência","inic_Modalidade"}))
        self.app.button(key="inic_clear_search").click().run()
        self.assertHealthy()
        self.assertEqual(self.app.metric[4].value,"560")


if __name__ == "__main__":
    unittest.main()
