"""Stubs for checks_catalog.csv category: On-Page & Duplicates (remaining checks).

health_score.py already implements: missing title/description/H1/canonical,
thin content, duplicate titles/descriptions/H1/body, and (via this module)
title/description length. See checks/crawlability.py for the stub pattern.
"""
from typing import Any, Dict

import pandas as pd
from bs4 import BeautifulSoup

TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
DESCRIPTION_MIN_LENGTH = 70
DESCRIPTION_MAX_LENGTH = 160


def check_C042(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """title too short (Warning · Page)
    <30 chars. Excludes pages with no title (see Missing Title, C041).
    """
    length = pages_df["Title Length"].astype(int)
    mask = length.gt(0) & length.lt(TITLE_MIN_LENGTH)
    return pages_df.loc[mask, ["URL", "Title", "Title Length"]].drop_duplicates().reset_index(drop=True)


def check_C043(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """title too long (Warning · Page)
    >60 chars.
    """
    mask = pages_df["Title Length"].astype(int).gt(TITLE_MAX_LENGTH)
    return pages_df.loc[mask, ["URL", "Title", "Title Length"]].drop_duplicates().reset_index(drop=True)


def check_C046(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """meta description too short (Notice · Page)
    <70 chars. Excludes pages with no description (see Missing Description, C045).
    """
    length = pages_df["Description Length"].astype(int)
    mask = length.gt(0) & length.lt(DESCRIPTION_MIN_LENGTH)
    return pages_df.loc[mask, ["URL", "Description", "Description Length"]].drop_duplicates().reset_index(drop=True)


def check_C047(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """meta description too long (Notice · Page)
    >160 chars.
    """
    mask = pages_df["Description Length"].astype(int).gt(DESCRIPTION_MAX_LENGTH)
    return pages_df.loc[mask, ["URL", "Description", "Description Length"]].drop_duplicates().reset_index(drop=True)


def _h1_count(html: Any) -> int:
    if not html:
        return 0
    soup = BeautifulSoup(str(html), "html.parser")
    return len(soup.find_all("h1"))


def check_C050(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """multiple H1s (Warning · Page)"""
    counts = pages_df["HTML"].fillna("").apply(_h1_count)
    return pages_df.loc[counts.gt(1), ["URL", "H1"]].drop_duplicates().reset_index(drop=True)


def check_C052(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """H1 duplicates the title exactly (Notice · Page)
    Missed opportunity for complementary signal. Excludes pages missing a
    title or H1 (see Missing Title, C041, and Missing H1, C049).
    """
    titles = pages_df["Title"].astype(str).str.strip()
    h1s = pages_df["H1"].astype(str).str.strip()
    mask = titles.ne("") & h1s.ne("") & titles.eq(h1s)
    return pages_df.loc[mask, ["URL", "Title", "H1"]].drop_duplicates().reset_index(drop=True)


def check_C055(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """exact-duplicate page (same content hash, different URL) (Error · Site)
    Byte-identical or near-identical body.
    """
    raise NotImplementedError("C055 not yet implemented")


def check_C057(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """keyword cannibalization (2+ pages targeting same priority keyword) (Warning · Site)
    Cross-reference priority_keywords.csv target mapping.
    """
    raise NotImplementedError("C057 not yet implemented")


def check_C058(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """low text-to-HTML ratio (Notice · Page)
    Page is markup-heavy relative to visible text.
    """
    raise NotImplementedError("C058 not yet implemented")


def _has_lang_attribute(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    return bool(lang and str(lang).strip())


def check_C059(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """missing language declaration (html lang attribute) (Notice · Page)"""
    mask = ~pages_df["HTML"].fillna("").apply(_has_lang_attribute)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C060(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken heading hierarchy (e.g. H1 -> H3, skipping H2) (Notice · Page)"""
    raise NotImplementedError("C060 not yet implemented")


def check_C061(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """URL contains excessive parameters (Notice · Page)
    >3 query parameters, duplicate-content risk.
    """
    raise NotImplementedError("C061 not yet implemented")


def check_C062(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """URL is excessively long (Notice · Page)
    >115 characters.
    """
    raise NotImplementedError("C062 not yet implemented")


def check_C063(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """non-descriptive URL (auto-generated IDs/slugs) (Notice · Page)"""
    raise NotImplementedError("C063 not yet implemented")


def check_C064(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """underscores used in URL instead of hyphens (Notice · Page)"""
    raise NotImplementedError("C064 not yet implemented")


def check_C065(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """uppercase characters in URL (Notice · Page)
    Case-variant duplicate risk.
    """
    raise NotImplementedError("C065 not yet implemented")


CHECKS = {
    "C055": check_C055,
    "C057": check_C057,
    "C058": check_C058,
    "C060": check_C060,
    "C061": check_C061,
    "C062": check_C062,
    "C063": check_C063,
    "C064": check_C064,
    "C065": check_C065,
}
