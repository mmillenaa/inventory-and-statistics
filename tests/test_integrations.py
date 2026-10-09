import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import requests

from integrations import author_publications, search_dataverse


class DataverseTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cache = Path(self.directory.name) / "observatorio.json"
        self.seed = patch("integrations.SNAPSHOT_PATH", Path(self.directory.name) / "sem-copia.json")
        self.seed.start()
        self.addCleanup(self.seed.stop)
        self.authors = ["Machado, Maíra Rocha", "Franco, Millena Miranda"]
        self.item = {"name": "Casa de Detenção", "global_id": "hdl:teste/1",
                     "authors": ["Machado, Maíra Rocha", "Franco, Millena Miranda"], "url": "https://example.org/base"}

    def test_public_search_ignores_expired_tokens_and_batches_authors(self):
        with patch("integrations.search_dataverse", return_value=[self.item]) as search:
            frame = author_publications(["chave-expirada"], self.authors, self.cache)
        self.assertEqual(len(frame), 1)
        self.assertEqual(search.call_count, 2)
        for call in search.call_args_list:
            self.assertEqual(len(call.args), 2)
            self.assertIn('authorName:"Machado, Maíra Rocha"', call.args[1])
        self.assertEqual(frame.attrs["diagnostics"], {})

    def test_source_outage_keeps_last_success_and_avoids_author_error_list(self):
        with patch("integrations.search_dataverse", return_value=[self.item]):
            author_publications([], self.authors, self.cache)
        with patch("integrations.search_dataverse", side_effect=requests.Timeout):
            frame = author_publications([], self.authors, self.cache)
        self.assertEqual(frame["Identificador"].tolist(), ["hdl:teste/1"])
        self.assertEqual(set(frame.attrs["diagnostics"]), {"FGV", "SciELO"})
        self.assertIn("Mantida a última listagem", frame.attrs["notice"])
        self.assertNotIn("Machado", frame.attrs["notice"])

    def test_partial_outage_preserves_other_repository(self):
        def search(url, query):
            if "scielo" in url:
                response = Mock(status_code=403)
                raise requests.HTTPError(response=response)
            return [self.item]
        with patch("integrations.search_dataverse", side_effect=search):
            frame = author_publications([], self.authors, self.cache)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.attrs["diagnostics"], {"SciELO": "HTTP 403"})
        self.assertEqual(len(json.loads(self.cache.read_text())["FGV"]["records"]), 1)

    def test_rejects_incidental_name_mentions_and_checks_author_metadata(self):
        unrelated = {**self.item, "global_id": "hdl:teste/2", "authors": ["Outra pessoa"]}
        with patch("integrations.search_dataverse", return_value=[self.item, unrelated]):
            frame = author_publications([], self.authors, self.cache)
        self.assertEqual(frame["Identificador"].tolist(), ["hdl:teste/1"])

    def test_search_requests_only_published_versions(self):
        response = Mock()
        response.json.return_value = {"status": "OK", "data": {"items": [], "total_count": 0}}
        with patch("integrations.requests.get", return_value=response) as get:
            self.assertEqual(search_dataverse("https://example.org/api/search", "autor"), [])
        self.assertEqual(get.call_args.kwargs["params"]["fq"], "publicationStatus:Published")

    def test_invalid_json_schema_does_not_look_like_success(self):
        response = Mock()
        response.json.return_value = {"status": "ERROR", "message": "Search syntax error"}
        with patch("integrations.requests.get", return_value=response):
            with self.assertRaises(ValueError):
                search_dataverse("https://example.org/api/search", "autor")


if __name__ == "__main__":
    unittest.main()
