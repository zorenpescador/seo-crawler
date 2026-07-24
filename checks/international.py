"""Stubs for checks_catalog.csv category: International SEO.

See checks/crawlability.py for the pattern these stubs follow.
"""
import re
from typing import Any, Dict, List

import pandas as pd
from bs4 import BeautifulSoup

HREFLANG_CODE_PATTERN = re.compile(r"^([a-zA-Z]{2,3}(-[a-zA-Z]{2,8})?|x-default)$")


def _hreflang_entries(html: Any) -> List[Dict[str, str]]:
    if not html:
        return []
    soup = BeautifulSoup(str(html), "html.parser")
    entries = []
    for link in soup.find_all("link", attrs={"hreflang": True}):
        rel = link.get("rel") or []
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
        if "alternate" not in rel_str.lower():
            continue
        entries.append({"hreflang": str(link.get("hreflang", "")).strip(), "href": str(link.get("href", ""))})
    return entries


def check_C096(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """hreflang attribute present but invalid language/region code (Error · Page)"""
    def _has_invalid_code(html: Any) -> bool:
        return any(
            entry["hreflang"] and not HREFLANG_CODE_PATTERN.match(entry["hreflang"])
            for entry in _hreflang_entries(html)
        )

    mask = pages_df["HTML"].fillna("").apply(_has_invalid_code)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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


def check_C101(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """multiple x-default hreflang entries (Warning · Page)
    Should be exactly one.
    """
    def _has_multiple_x_default(html: Any) -> bool:
        entries = _hreflang_entries(html)
        return sum(1 for e in entries if e["hreflang"].lower() == "x-default") > 1

    mask = pages_df["HTML"].fillna("").apply(_has_multiple_x_default)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C102(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """missing x-default for a multi-region set (Notice · Page)"""
    def _missing_x_default(html: Any) -> bool:
        entries = _hreflang_entries(html)
        if len(entries) < 2:
            return False
        return not any(e["hreflang"].lower() == "x-default" for e in entries)

    mask = pages_df["HTML"].fillna("").apply(_missing_x_default)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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


def check_C106(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """duplicate hreflang for same language/region on one page (Warning · Page)"""
    def _has_duplicate_hreflang(html: Any) -> bool:
        codes = [e["hreflang"].lower() for e in _hreflang_entries(html) if e["hreflang"]]
        return len(codes) != len(set(codes))

    mask = pages_df["HTML"].fillna("").apply(_has_duplicate_hreflang)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C107(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """content language auto-detection mismatch (declared vs detected) (Notice · Page)
    Basic language-detection heuristic.
    """
    raise NotImplementedError("C107 not yet implemented")


CHECKS = {
    "C097": check_C097,
    "C098": check_C098,
    "C099": check_C099,
    "C100": check_C100,
    "C103": check_C103,
    "C104": check_C104,
    "C105": check_C105,
    "C107": check_C107,
}
