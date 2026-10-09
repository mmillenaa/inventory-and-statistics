import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import pandas as pd
from data_logic import (load_collection, category_options, filter_categories,
                        metadata_count, phrase_frequency, search_records, year_frequency)
from integrations import search_dataverse


class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.cat, cls.ini = load_collection([p.name for p in cls.root.glob("*.xlsx")], cls.root)

    def test_preserves_conflicting_descriptions_and_representation_units(self):
        self.assertEqual(len(self.cat), 348)
        films = self.cat[self.cat.Arquivo_origem.str.contains("FILMES")]
        self.assertEqual(len(films), 6)
        self.assertTrue(films["Conflito de código"].all())
        self.assertEqual(films["Representações vinculadas"].sum(), 0)
        self.assertEqual(len(self.cat.attrs["representations"]), 574)
        dasp = self.cat[self.cat.Arquivo_origem.str.contains("DASP")]
        self.assertEqual(len(dasp), 183)
        self.assertEqual(dasp["Representações vinculadas"].sum(), 365)

    def test_classifications_and_multiple_filter_options(self):
        self.assertIn("PLN", category_options(self.cat, "Espécie/Tipo documental"))
        cpos = filter_categories(self.cat, {"Espécie/Tipo documental":["PLN"], "Forma documental":["MT0"]})
        self.assertFalse(cpos.empty)
        self.assertTrue(cpos.Arquivo_origem.str.contains("CPOS").all())
        self.assertGreater(len(filter_categories(self.cat, {"Espécie/Tipo documental":["PLN", "FOT"]})), len(cpos))

    def test_mapping_titles_dates_and_separate_purpose(self):
        self.assertEqual(len(self.ini), 560)
        self.assertTrue(self.ini.Ano.str.fullmatch(r"\d{4}").all())
        penha = self.ini[self.ini.Arquivo_origem.str.contains("MSSCPENHA")]
        self.assertEqual((penha["Finalidade primária"] == "Difusão").sum(), 276)
        self.assertEqual((penha["Intervenção"] == "Produção midiática").sum(), 277)
        self.assertEqual((self.ini["Título do documento"] != "").sum(), 556)
        self.assertEqual(len(filter_categories(self.ini, {"Nome da iniciativa":["Ato"]})), 12)

    def test_metadata_excludes_technical_fields(self):
        total = metadata_count(self.cat,"catalogue") + metadata_count(self.ini,"initiatives")
        self.assertEqual(total, 17186)
        modified = self.cat.copy()
        modified["Campo interno"] = "valor"
        self.assertEqual(metadata_count(modified,"catalogue"), metadata_count(self.cat,"catalogue"))

    def test_phrase_search_and_numbers(self):
        frame = pd.DataFrame({"Título (Busca)":["Roda de samba: conversa", "Roda de conversa em 2025", "Roda", "Conversa"], "Conteúdo (Busca)":["", "", "Conversa", ""]})
        self.assertEqual(search_records(frame,"roda de conversa").index.tolist(), [1])
        self.assertEqual(search_records(frame,"2025").index.tolist(), [1])
        self.assertTrue(search_records(frame.iloc[:0],"algo").empty)

    def test_complete_phrases_and_cloud_columns(self):
        frame = pd.DataFrame({"Proponente":["FGV Direito SP, 1ª Frente de Sobreviventes", "fgv direito sp"], "Ano":[2025,2025]})
        counts, detail = phrase_frequency(frame, ["Proponente","Ano"])
        self.assertEqual(counts["FGV Direito SP"],2)
        self.assertEqual(counts["1ª Frente de Sobreviventes"],1)
        self.assertEqual(counts["2025"],2)
        self.assertEqual(detail.Frequência.sum(),5)
        self.assertEqual(phrase_frequency(frame,[])[0],{})

    def test_temporal_coverage_and_zero_years(self):
        frequency, dated, undated = year_frequency(self.cat,"Data (Busca)")
        self.assertEqual((dated,undated),(305,43))
        self.assertEqual(frequency.Frequência.sum(),305)
        frequency, dated, undated = year_frequency(pd.DataFrame({"Ano":["2022","2024",""]}),"Ano")
        self.assertEqual(frequency.Frequência.tolist(),[1,0,1])
        self.assertEqual((dated,undated),(2,1))

    def test_no_selection_is_valid(self):
        cat,ini = load_collection([],self.root)
        self.assertTrue(cat.empty and ini.empty)
        self.assertEqual(metadata_count(cat,"catalogue"),0)

    def test_dataverse_paginates(self):
        first = Mock(); first.json.return_value={"data":{"total_count":3,"items":[{"global_id":"1"},{"global_id":"2"}]}}
        second = Mock(); second.json.return_value={"data":{"total_count":3,"items":[{"global_id":"3"}]}}
        with patch("integrations.requests.get",side_effect=[first,second]) as get:
            items=search_dataverse("https://example.org/api/search","autor")
        self.assertEqual(len(items),3)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["start"],2)
        self.assertEqual(get.call_args.kwargs["timeout"],15)


if __name__ == "__main__":
    unittest.main()
