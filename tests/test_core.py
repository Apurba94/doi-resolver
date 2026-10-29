import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout

from doi_resolver.cli import main
from doi_resolver.core import Resolver, extract_dois, normalize_doi

BIB = "@article{Smith_2020, title={Test}, doi={10.1000/abc}}"


class FakeFetch:
    def __init__(self):
        self.calls = []

    def __call__(self, doi, accept):
        self.calls.append((doi, accept))
        if doi == "10.1000/missing":
            raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        return BIB if "bibtex" in accept else json.dumps({"DOI": doi})


class NormalizeTests(unittest.TestCase):
    def test_normalize_variants(self):
        for raw in ["https://doi.org/10.1000/ABC", "http://dx.doi.org/10.1000/abc", "doi: 10.1000/abc", "10.1000/abc."]:
            self.assertEqual(normalize_doi(raw), "10.1000/abc")

    def test_extract_from_reference_list(self):
        text = ("[1] Smith J. Nature. 2020. doi:10.1038/s41586-020-2649-2.\n"
                "[2] See https://doi.org/10.1126/science.abc1234 and again 10.1038/S41586-020-2649-2")
        self.assertEqual(extract_dois(text), ["10.1038/s41586-020-2649-2", "10.1126/science.abc1234"])


class ResolverTests(unittest.TestCase):
    def test_resolve_uses_accept_header_and_cache(self):
        fetch = FakeFetch()
        r = Resolver(fetch=fetch)
        self.assertEqual(r.resolve("https://doi.org/10.1000/ABC"), BIB)
        r.resolve("10.1000/abc")
        self.assertEqual(len(fetch.calls), 1)
        self.assertEqual(fetch.calls[0][1], "application/x-bibtex")

    def test_formats_are_cached_separately(self):
        fetch = FakeFetch()
        r = Resolver(fetch=fetch)
        r.resolve("10.1000/abc", "bibtex")
        self.assertIn('"DOI"', r.resolve("10.1000/abc", "csl"))
        self.assertEqual(len(fetch.calls), 2)

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            Resolver(fetch=FakeFetch()).resolve("10.1/x", "docx")

    def test_404_becomes_lookup_error_and_failure(self):
        r = Resolver(fetch=FakeFetch())
        with self.assertRaises(LookupError):
            r.resolve("10.1000/missing")
        results, failures = r.resolve_many(["10.1000/abc", "10.1000/missing"])
        self.assertEqual(list(results), ["10.1000/abc"])
        self.assertIn("10.1000/missing", failures)

    def test_cache_persists_to_disk(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cache.json")
            Resolver(path, fetch=FakeFetch()).resolve_many(["10.1000/abc"])
            fetch = FakeFetch()
            self.assertEqual(Resolver(path, fetch=fetch).resolve("10.1000/abc"), BIB)
            self.assertEqual(fetch.calls, [])

    def test_cli_with_input_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "refs.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("ref doi:10.1000/abc and 10.1000/missing")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["-i", src, "--cache", os.path.join(d, "c.json")], resolver=Resolver(fetch=FakeFetch()))
            self.assertEqual(code, 1)
            self.assertIn("Smith_2020", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
