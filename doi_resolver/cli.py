"""Command-line interface for doi-resolver."""
import argparse
import os
import sys

from .core import FORMATS, Resolver, extract_dois


def main(argv=None, resolver=None):
    ap = argparse.ArgumentParser(prog="doi-resolver", description="Resolve DOIs to BibTeX/CSL-JSON/RIS/APA text.")
    ap.add_argument("dois", nargs="*", help="DOIs or DOI URLs")
    ap.add_argument("-i", "--input", help="text file to scan for DOIs (reference list, notes, ...)")
    ap.add_argument("-f", "--format", default="bibtex", choices=sorted(FORMATS))
    ap.add_argument("-o", "--output", help="output file (default stdout)")
    ap.add_argument("--cache", default=os.path.join(os.path.expanduser("~"), ".doi_resolver_cache.json"))
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between network requests")
    ap.add_argument("--list", action="store_true", help="only list DOIs found in --input")
    args = ap.parse_args(argv)

    dois = list(args.dois)
    if args.input:
        with open(args.input, encoding="utf-8", errors="replace") as fh:
            dois += extract_dois(fh.read())
    if not dois:
        ap.error("no DOIs given")
    if args.list:
        print("\n".join(dois))
        return 0
    resolver = resolver or Resolver(args.cache, delay=args.delay)
    results, failures = resolver.resolve_many(dois, args.format)
    text = "\n\n".join(results.values()) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    for d, err in failures.items():
        print("FAILED %s: %s" % (d, err), file=sys.stderr)
    return 1 if failures else 0
