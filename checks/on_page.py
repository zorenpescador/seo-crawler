"""Stubs for checks_catalog.csv category: On-Page & Duplicates (remaining checks).

health_score.py already implements: missing title/description/H1/canonical,
thin content, duplicate titles/descriptions/H1/body, and (via this module)
title/description length. See checks/crawlability.py for the stub pattern.
"""
import re
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

import pandas as pd
from bs4 import BeautifulSoup

TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
DESCRIPTION_MIN_LENGTH = 70
DESCRIPTION_MAX_LENGTH = 160
URL_QUERY_PARAM_MAX = 3


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


TEXT_TO_HTML_RATIO_MIN = 0.10


def _text_to_html_ratio(html: Any) -> float:
    html_str = str(html) if html else ""
    if not html_str:
        return 1.0
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text_length = len(soup.get_text(" ", strip=True))
    return text_length / len(html_str)


def check_C058(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """low text-to-HTML ratio (Notice · Page)
    Page is markup-heavy relative to visible text. Pages with no HTML
    (crawl failures, handled by C014) are excluded rather than flagged.
    """
    ratios = pages_df["HTML"].fillna("").apply(_text_to_html_ratio)
    return pages_df.loc[ratios.lt(TEXT_TO_HTML_RATIO_MIN), ["URL"]].drop_duplicates().reset_index(drop=True)


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


def _has_heading_hierarchy_skip(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    levels = [int(h.name[1]) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
    seen_max = 0
    for level in levels:
        if seen_max and level > seen_max + 1:
            return True
        seen_max = max(seen_max, level)
    return False


def check_C060(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken heading hierarchy (e.g. H1 -> H3, skipping H2) (Notice · Page)
    Flags a level jump of more than one (e.g. H1 straight to H3). Dropping
    back to a shallower level (H3 back to H1) is normal and not flagged.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_heading_hierarchy_skip)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _query_param_count(url: Any) -> int:
    query = urlparse(str(url)).query
    return len(parse_qs(query)) if query else 0


def check_C061(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """URL contains excessive parameters (Notice · Page)
    >3 query parameters, duplicate-content risk.
    """
    counts = pages_df["URL"].apply(_query_param_count)
    return pages_df.loc[counts.gt(URL_QUERY_PARAM_MAX), ["URL"]].drop_duplicates().reset_index(drop=True)


URL_MAX_LENGTH = 115


def check_C062(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """URL is excessively long (Notice · Page)
    >115 characters.
    """
    mask = pages_df["URL"].astype(str).str.len().gt(URL_MAX_LENGTH)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


NON_DESCRIPTIVE_SLUG_PATTERN = re.compile(r"^(\d+|[0-9a-f]{8,})$", re.IGNORECASE)


def _is_non_descriptive_url(url: Any) -> bool:
    path = urlparse(str(url)).path.rstrip("/")
    if not path:
        return False
    last_segment = path.rsplit("/", 1)[-1]
    return bool(NON_DESCRIPTIVE_SLUG_PATTERN.match(last_segment))


def check_C063(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """non-descriptive URL (auto-generated IDs/slugs) (Notice · Page)
    Heuristic: final path segment is purely numeric, or a long hex string
    (8+ chars), e.g. /product/48213 or /post/3f9a2c1e.
    """
    mask = pages_df["URL"].apply(_is_non_descriptive_url)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C064(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """underscores used in URL instead of hyphens (Notice · Page)"""
    mask = pages_df["URL"].astype(str).str.contains("_", regex=False)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C065(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """uppercase characters in URL (Notice · Page)
    Case-variant duplicate risk.
    """
    mask = pages_df["URL"].astype(str).apply(lambda url: any(c.isupper() for c in url))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {
    "C055": check_C055,
    "C057": check_C057,
}
