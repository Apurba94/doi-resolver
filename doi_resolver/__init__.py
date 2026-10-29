"""Resolve DOIs to BibTeX or CSL-JSON via doi.org content negotiation."""
from .core import Resolver, extract_dois, normalize_doi, FORMATS

__version__ = "0.1.0"
__all__ = ["Resolver", "extract_dois", "normalize_doi", "FORMATS"]
