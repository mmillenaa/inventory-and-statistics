import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import pandas as pd
from data_logic import (load_collection, category_options, filter_categories,
                        metadata_count, phrase_frequency, search_records, search_matches, year_frequency, CATEGORIES,
                        reconcile_filters, faceted_options, display_table)
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
        self.assertEqual(films["Representações vinculadas"].sum(), 39)
        self.assertEqual(films["Espécie/Tipo documental"].tolist(),[("FME",)]*6)
        self.assertEqual(self.cat["Representações vinculadas"].sum(),574)
        self.assertFalse(self.cat["Representações vinculadas"].eq(0).any())
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

    def test_facets_exclude_impossible_categories(self):
        fields=["Gênero documental","Espécie/Tipo documental","Técnica de registro","Forma documental"]
        options=faceted_options(self.cat,fields,{"Gênero documental":["ICO"]})
        self.assertEqual(options["Espécie/Tipo documental"],["FOT", "PLN", "REL"])
        self.assertNotIn("NOT",options["Espécie/Tipo documental"])
        for field, values in options.items():
            for value in values:
                selections={"Gênero documental":["ICO"],field:[value]}
                self.assertFalse(filter_categories(self.cat,selections).empty)

    def test_new_search_removes_conflicting_filter(self):
        searched=search_records(self.cat,"mãe")
        self.assertFalse(searched.empty)
        valid=reconcile_filters(searched,list(CATEGORIES),{"Espécie/Tipo documental":["PLN"]})
        self.assertEqual(valid["Espécie/Tipo documental"],[])
        self.assertFalse(filter_categories(searched,valid).empty)

    def test_search_reports_actual_fields_and_hides_internal_columns(self):
        frame=pd.DataFrame({"Título (Busca)":["Casa antiga", "Arquivo"], "Conteúdo (Busca)":["", "Uma casa"]})
        matches=search_matches(frame,"casa")
        self.assertEqual(matches.sum().to_dict(),{"Título (Busca)":1,"Conteúdo (Busca)":1})
        view=display_table(self.cat)
        self.assertNotIn("Conflito de código",view)
        self.assertNotIn("Representações vinculadas",view)

    def test_dataverse_paginates(self):
        first = Mock(); first.json.return_value={"data":{"total_count":3,"items":[{"global_id":"1"},{"global_id":"2"}]}}
        second = Mock(); second.json.return_value={"data":{"total_count":3,"items":[{"global_id":"3"}]}}
        with patch("integrations.requests.get",side_effect=[first,second]) as get:
            items=search_dataverse("https://example.org/api/search","autor")
        self.assertEqual(len(items),3)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["start"],2)
        self.assertEqual(get.call_args.kwargs["timeout"],30)

    def test_source_positions_follow_both_spreadsheet_structures(self):
        layouts=self.ini.attrs["source_columns"]
        car=next(mapping["Geral"] for filename,mapping in layouts.items() if "REMEMORA-CARANDIRU" in filename)
        pen=next(mapping["Geral"] for filename,mapping in layouts.items() if "MSSCPENHA" in filename)
        fields=["Nome da iniciativa","Ano","Fonte / Origem","Proponente"]
        self.assertEqual([car[field] for field in fields],["B","G","M","I"])
        self.assertEqual([pen[field] for field in fields],["B","H","N","J"])
        for mapping in self.cat.attrs["source_columns"].values():
            self.assertEqual(mapping["Geral"]["Forma documental"],"Q")
            self.assertEqual(mapping["Geral"]["Técnica de registro"],"O")

    def test_ndt_is_present_in_source_and_every_representation_has_one_description(self):
        ndt=[rep for rep in self.cat.attrs["representations"] if rep["Técnica de registro"]=="NDT"]
        self.assertEqual(len(ndt),85)
        self.assertEqual(len(filter_categories(self.cat,{"Técnica de registro":["NDT"]})),41)
        linked=[identifier for value in self.cat["Representações_ID"] for identifier in value]
        self.assertEqual(len(linked),574)
        self.assertEqual(len(set(linked)),574)

    def test_controlled_vocabulary_covers_every_source_category(self):
        from vocabulario_controlado import descrever_sigla, rotular_sigla, rotulo_curto_sigla
        for field,type_key in zip(CATEGORIES,["genero","especie","tecnica","forma"]):
            for value in category_options(self.cat,field):
                self.assertTrue(descrever_sigla(value,type_key),(field,value))
                self.assertNotEqual(rotulo_curto_sigla(value,type_key),value)
        self.assertEqual(rotular_sigla("AVS","genero"),"Audiovisual — AVS")
        self.assertEqual(rotular_sigla("MT0","forma"),"Matriz bruta — MT0")

    def test_metadata_count_independently_from_excel_cell_positions(self):
        from openpyxl import load_workbook
        def filled(value):
            if value is None:
                return False
            text=" ".join(str(value).split()).lower()
            return text not in {"","na","n/a","nan","none","null","nat","-","--","[título não localizado]"} and not text.startswith("#")
        totals={"catalogue":0,"initiatives":0}
        records={"catalogue":0,"initiatives":0}
        for path in self.root.glob("*.xlsx"):
            book=load_workbook(path,read_only=True,data_only=True)
            if "MAPEAMENTOS" in path.name:
                rows=list(book["Geral"].values)[2:]
                data=[row[1:20] if "MSSCPENHA" in path.name else row[1:19] for row in rows if filled(row[1])]
                records["initiatives"]+=len(data)
                totals["initiatives"]+=sum(filled(value) for row in data for value in row)
            else:
                for sheet in book:
                    if sheet.title in {"Geral","Classificação"}:
                        continue
                    rows=list(sheet.values)
                    if not rows or len(rows[0])<2 or "título descritivo" not in str(rows[0][1]).lower():
                        continue
                    data=[row[:20] for row in rows[1:] if len(row)>1 and filled(row[1])]
                    records["catalogue"]+=len(data)
                    totals["catalogue"]+=sum(filled(value) for row in data for value in row)
            book.close()
        self.assertEqual(records,{"catalogue":348,"initiatives":560})
        self.assertEqual(totals,{"catalogue":6957,"initiatives":10229})
        self.assertEqual(sum(totals.values()),17186)


if __name__ == "__main__":
    unittest.main()
