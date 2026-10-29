# doi-resolver

**Turn DOIs into clean BibTeX, CSL-JSON, RIS or formatted APA references in one command,
with caching and batch extraction from any text.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Copying citations from publisher websites is slow and error-prone. Every registered DOI already
has authoritative metadata behind it: `doi.org` returns it in many formats through HTTP content
negotiation. This tool automates that, so a reference list, a reviewer's comment, or a folder of
notes can become a `.bib` file in seconds.

## Features

- Extract DOIs from free text (Crossref's recommended pattern, deduplicated, URL/`doi:` prefixes removed)
- Resolve to `bibtex`, `csl` (CSL-JSON), `ris`, or `text` (APA formatted)
- JSON cache on disk, so repeated runs make no network calls
- Polite rate limiting (`--delay`), clear failure report, non-zero exit code on failures
- Pluggable fetch function for testing or custom resolvers

## Usage

```bash
pip install .
doi-resolver 10.1038/s41586-020-2649-2
doi-resolver -i reference_list.txt -o refs.bib
doi-resolver -i notes.md -f csl -o refs.json
doi-resolver -i draft.txt --list            # just show the DOIs found
```

```python
from doi_resolver import Resolver, extract_dois
r = Resolver("cache.json")
results, failures = r.resolve_many(extract_dois(open("refs.txt").read()), fmt="bibtex")
```

## How it works

A GET request to `https://doi.org/<doi>` with an `Accept` header such as `application/x-bibtex`
is redirected by the DOI registration agency (Crossref, DataCite, mEDRA) to its metadata
service, which returns the record in the requested format.

## Testing

Tests run offline with a fake fetcher:

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
