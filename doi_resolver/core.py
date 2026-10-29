"""DOI extraction, normalization and resolution with an on-disk JSON cache."""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

FORMATS = {
    "bibtex": "application/x-bibtex",
    "csl": "application/vnd.citationstyles.csl+json",
    "ris": "application/x-research-info-systems",
    "text": "text/x-bibliography; style=apa",
}

# Crossref's recommended DOI pattern, matched case-insensitively.
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)


def normalize_doi(doi):
    """Return the bare lowercase DOI (no resolver prefix, no 'doi:', no trailing punctuation)."""
    d = doi.strip()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d, flags=re.IGNORECASE)
    d = re.sub(r"^doi:\s*", "", d, flags=re.IGNORECASE)
    return d.rstrip(".,;)").lower()


def extract_dois(text):
    """Find all DOIs in free text (reference lists, PDFs converted to text, web pages), in order, unique."""
    seen, out = set(), []
    for m in _DOI_RE.finditer(text):
        d = normalize_doi(m.group(1))
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _http_fetch(doi, accept, timeout=20):
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/:;()._-")
    req = urllib.request.Request(url, headers={"Accept": accept,
                                               "User-Agent": "doi-resolver/0.1 (research toolkit)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


class Resolver:
    """Resolve DOIs with caching.

    `fetch(doi, accept) -> str` can be replaced (e.g. in tests); by default it calls doi.org.
    The cache is a JSON file mapping "format|doi" to the response text.
    """

    def __init__(self, cache_path=None, fetch=None, delay=0.0):
        self.cache_path = cache_path
        self.fetch = fetch or _http_fetch
        self.delay = delay
        self.cache = {}
        if cache_path and os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as fh:
                self.cache = json.load(fh)

    def save(self):
        if self.cache_path:
            with open(self.cache_path, "w", encoding="utf-8") as fh:
                json.dump(self.cache, fh, indent=1, sort_keys=True)

    def resolve(self, doi, fmt="bibtex"):
        """Return the metadata string for `doi` in `fmt` (see FORMATS). Raises LookupError if unknown."""
        if fmt not in FORMATS:
            raise ValueError("unknown format %r; choose from %s" % (fmt, ", ".join(FORMATS)))
        doi = normalize_doi(doi)
        key = fmt + "|" + doi
        if key in self.cache:
            return self.cache[key]
        try:
            text = self.fetch(doi, FORMATS[fmt])
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise LookupError("DOI not found: " + doi) from exc
            raise
        if self.delay:
            time.sleep(self.delay)
        self.cache[key] = text.strip()
        return self.cache[key]

    def resolve_many(self, dois, fmt="bibtex"):
        """Resolve a list; returns (results dict doi -> text, failures dict doi -> error message)."""
        results, failures = {}, {}
        for d in dois:
            try:
                results[normalize_doi(d)] = self.resolve(d, fmt)
            except (LookupError, OSError, ValueError) as exc:
                failures[normalize_doi(d)] = str(exc)
        self.save()
        return results, failures
