"""Stubs for checks_catalog.csv category: Crawlability & Indexability.

Each function is a placeholder for a check not yet implemented in
health_score.py / site_audit.py. Fill in the body and remove the
NotImplementedError once real logic lands, then wire the check_id into
health_score.CHECK_NAME_TO_CATALOG_ID so it feeds the health score.
"""
import re
from typing import Any, Dict
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup

ROBOTS_META_NAME_PATTERN = re.compile("^robots$", re.IGNORECASE)
SOFT_404_TEXT_PATTERN = re.compile(
    r"\b(page not found|404 error|error 404|not found|doesn't exist|does not exist)\b", re.IGNORECASE
)
SOFT_404_WORD_COUNT_MAX = 200


def _robots_meta_content(html: Any) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(str(html), "html.parser")
    meta = soup.find("meta", attrs={"name": ROBOTS_META_NAME_PATTERN})
    if not meta:
        return ""
    return str(meta.get("content", "")).lower()


def check_C001(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt missing (Warning · Site)
    No robots.txt found at domain root.
    """
    raise NotImplementedError("C001 not yet implemented")


def check_C002(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt not valid (syntax errors) (Warning · Site)
    robots.txt contains malformed directives.
    """
    raise NotImplementedError("C002 not yet implemented")


def check_C003(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt blocks entire site (Error · Site)
    Disallow: / found for relevant user-agents.
    """
    raise NotImplementedError("C003 not yet implemented")


def check_C004(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt blocks CSS/JS resources (Warning · Site)
    Rendering-critical assets disallowed.
    """
    raise NotImplementedError("C004 not yet implemented")


def check_C005(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap.xml missing (Warning · Site)
    No sitemap referenced in robots.txt or at /sitemap.xml.
    """
    raise NotImplementedError("C005 not yet implemented")


def check_C006(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap.xml not valid XML (Error · Site)
    Sitemap fails to parse.
    """
    raise NotImplementedError("C006 not yet implemented")


def check_C007(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains 4XX/5XX URLs (Error · Site)
    URLs listed in sitemap return client/server errors.
    """
    raise NotImplementedError("C007 not yet implemented")


def check_C008(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains redirected URLs (Warning · Site)
    URLs listed in sitemap 3XX-redirect elsewhere.
    """
    raise NotImplementedError("C008 not yet implemented")


def check_C009(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains noindex URLs (Warning · Site)
    URLs in sitemap carry a noindex directive.
    """
    raise NotImplementedError("C009 not yet implemented")


def check_C010(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap not referenced in robots.txt (Notice · Site)
    Sitemap exists but isn't declared.
    """
    raise NotImplementedError("C010 not yet implemented")


def check_C011(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page blocked by robots.txt (Error · Page)
    Crawler already checks this via robotparser; not yet surfaced as a finding.
    """
    raise NotImplementedError("C011 not yet implemented")


def check_C012(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page has noindex directive (Warning · Page)
    meta robots contains noindex. (X-Robots-Tag would need response
    headers, which the crawler doesn't currently capture.)
    """
    mask = pages_df["HTML"].fillna("").apply(lambda html: "noindex" in _robots_meta_content(html))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C013(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page has nofollow on all outlinks (Warning · Page)
    meta robots nofollow prevents link equity flow.
    """
    mask = pages_df["HTML"].fillna("").apply(lambda html: "nofollow" in _robots_meta_content(html))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C014(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page not crawlable (timeout/DNS/conn error) (Error · Page)
    Request failed outright.
    """
    raise NotImplementedError("C014 not yet implemented")


def check_C015(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page returns soft 404 (200 status, error-like content) (Warning · Page)
    Heuristic: thin body (<200 words) with 'not found' language but HTTP 200.
    """
    def _has_404_language(html: Any) -> bool:
        if not html:
            return False
        soup = BeautifulSoup(str(html), "html.parser")
        return bool(SOFT_404_TEXT_PATTERN.search(soup.get_text(" ", strip=True)))

    is_200 = pages_df["Status"].astype(str).str.startswith("200")
    is_thin = pages_df["Word Count"].astype(int) < SOFT_404_WORD_COUNT_MAX
    has_404_language = pages_df["HTML"].fillna("").apply(_has_404_language)
    mask = is_200 & is_thin & has_404_language
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C016(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """conflicting robots signals (meta vs X-Robots-Tag) (Warning · Page)
    HTTP header and HTML meta robots disagree.
    """
    raise NotImplementedError("C016 not yet implemented")


def check_C017(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """canonical points to a blocked/noindex page (Error · Page)
    Canonical target is itself non-indexable.
    """
    raise NotImplementedError("C017 not yet implemented")


def _canonical_cross_domain(row: pd.Series) -> bool:
    canonical = str(row.get("Canonical URL", "")).strip()
    if not canonical:
        return False
    own_domain = urlparse(str(row.get("URL", ""))).netloc.lower()
    canonical_domain = urlparse(canonical).netloc.lower()
    return bool(canonical_domain) and canonical_domain != own_domain


def check_C018(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """canonical points to a different domain (Warning · Page)
    Cross-domain canonical, verify intent.
    """
    mask = pages_df.apply(_canonical_cross_domain, axis=1)
    return pages_df.loc[mask, ["URL", "Canonical URL"]].drop_duplicates().reset_index(drop=True)


def check_C019(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """canonical chain (canonical points to a page with its own different canonical) (Warning · Page)
    Canonical does not resolve to a stable target.
    """
    raise NotImplementedError("C019 not yet implemented")


def check_C020(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """paginated page missing rel=next/prev or self-canonical (Notice · Page)
    Pagination signals absent.
    """
    raise NotImplementedError("C020 not yet implemented")


CHECKS = {
    "C001": check_C001,
    "C002": check_C002,
    "C003": check_C003,
    "C004": check_C004,
    "C005": check_C005,
    "C006": check_C006,
    "C007": check_C007,
    "C008": check_C008,
    "C009": check_C009,
    "C010": check_C010,
    "C011": check_C011,
    "C014": check_C014,
    "C016": check_C016,
    "C017": check_C017,
    "C019": check_C019,
    "C020": check_C020,
}
