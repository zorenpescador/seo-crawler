"""Stubs for checks_catalog.csv category: International SEO.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict

import pandas as pd


def check_C096(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang attribute present but invalid language/region code (Error · Page)"""
    raise NotImplementedError("C096 not yet implemented")


def check_C097(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang missing return link (no reciprocal confirmation) (Error · Page)
    Page A links to B, B doesn't link back to A.
    """
    raise NotImplementedError("C097 not yet implemented")


def check_C098(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang points to a non-canonical URL (Warning · Page)"""
    raise NotImplementedError("C098 not yet implemented")


def check_C099(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang points to a redirected URL (Warning · Page)"""
    raise NotImplementedError("C099 not yet implemented")


def check_C100(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang points to a 4XX/5XX URL (Error · Page)"""
    raise NotImplementedError("C100 not yet implemented")


def check_C101(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """multiple x-default hreflang entries (Warning · Page)
    Should be exactly one.
    """
    raise NotImplementedError("C101 not yet implemented")


def check_C102(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """missing x-default for a multi-region set (Notice · Page)"""
    raise NotImplementedError("C102 not yet implemented")


def check_C103(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang set is not confirmed on all pages in the cluster (Warning · Site)
    Inconsistent cluster membership.
    """
    raise NotImplementedError("C103 not yet implemented")


def check_C104(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """conflicting language declared in html lang vs hreflang self-reference (Notice · Page)"""
    raise NotImplementedError("C104 not yet implemented")


def check_C105(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """hreflang declared in HTML and sitemap disagree (Warning · Site)"""
    raise NotImplementedError("C105 not yet implemented")


def check_C106(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """duplicate hreflang for same language/region on one page (Warning · Page)"""
    raise NotImplementedError("C106 not yet implemented")


def check_C107(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """content language auto-detection mismatch (declared vs detected) (Notice · Page)
    Basic language-detection heuristic.
    """
    raise NotImplementedError("C107 not yet implemented")


CHECKS = {
    "C096": check_C096,
    "C097": check_C097,
    "C098": check_C098,
    "C099": check_C099,
    "C100": check_C100,
    "C101": check_C101,
    "C102": check_C102,
    "C103": check_C103,
    "C104": check_C104,
    "C105": check_C105,
    "C106": check_C106,
    "C107": check_C107,
}
