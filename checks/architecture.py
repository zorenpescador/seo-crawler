"""Stubs for checks_catalog.csv category: Site Architecture & Internal Linking (remaining checks).

health_score.py already implements orphan pages and low-internal-link-support.
These stubs cover the rest of the category. See checks/crawlability.py for
the pattern.
"""
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

INTERNAL_LINK_COUNT_MAX = 100
GENERIC_ANCHOR_TEXTS = {"click here", "read more", "learn more", "here", "more", "link", "this page", "more info"}
SKIPPED_HREF_PREFIXES = ("javascript:", "mailto:", "tel:", "#")


def _internal_links(html: Any, page_url: Any) -> List[Dict[str, Any]]:
    if not html:
        return []
    own_domain = urlparse(str(page_url)).netloc.lower()
    soup = BeautifulSoup(str(html), "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(SKIPPED_HREF_PREFIXES):
            continue
        absolute = urljoin(str(page_url), href)
        parsed = urlparse(absolute)
        if parsed.netloc.lower() != own_domain:
            continue
        rel = a.get("rel") or []
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
        links.append({
            "href": absolute,
            "text": a.get_text(strip=True),
            "nofollow": "nofollow" in rel_str.lower(),
        })
    return links


def check_C067(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page more than 3 clicks from homepage (Warning · Site)
    Crawl-depth graph analysis.
    """
    raise NotImplementedError("C067 not yet implemented")


def check_C068(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page more than 5 clicks from homepage (Error · Site)
    Severe depth.
    """
    raise NotImplementedError("C068 not yet implemented")


def check_C069(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """too few internal links to an important page (Warning · Site)
    Priority page (per target-keyword map) under-linked.
    """
    raise NotImplementedError("C069 not yet implemented")


def check_C070(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """too many internal links on a single page (Notice · Page)
    >100 internal links dilutes equity.
    """
    counts = pages_df.apply(lambda row: len(_internal_links(row.get("HTML"), row.get("URL"))), axis=1)
    return pages_df.loc[counts.gt(INTERNAL_LINK_COUNT_MAX), ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C071(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken internal link (Error · Page)
    <a href> internal target returns 4XX/5XX. Only catches targets that
    are themselves in the crawled URL set.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))

    def _has_broken_link(row: pd.Series) -> bool:
        for link in _internal_links(row.get("HTML"), row.get("URL")):
            status = status_map.get(link["href"])
            if status and status.startswith(("4", "5")):
                return True
        return False

    mask = pages_df.apply(_has_broken_link, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C072(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """internal link to a redirected URL (Warning · Page)
    Only catches targets that are themselves in the crawled URL set.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))

    def _has_redirect_link(row: pd.Series) -> bool:
        for link in _internal_links(row.get("HTML"), row.get("URL")):
            status = status_map.get(link["href"])
            if status and status.startswith(("301", "302", "303", "307", "308")):
                return True
        return False

    mask = pages_df.apply(_has_redirect_link, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C073(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """internal link uses nofollow (Notice · Page)
    Unusual for internal navigation, verify intent.
    """
    mask = pages_df.apply(
        lambda row: any(link["nofollow"] for link in _internal_links(row.get("HTML"), row.get("URL"))), axis=1
    )
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C074(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """internal link with empty or generic anchor text ('click here', 'read more') (Notice · Page)"""
    def _has_generic_anchor(row: pd.Series) -> bool:
        for link in _internal_links(row.get("HTML"), row.get("URL")):
            text = link["text"].strip().lower()
            if not text or text in GENERIC_ANCHOR_TEXTS:
                return True
        return False

    mask = pages_df.apply(_has_generic_anchor, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C075(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal link anchor text mismatch vs destination topic (Notice · Page)
    Heuristic keyword overlap check.
    """
    raise NotImplementedError("C075 not yet implemented")


def check_C077(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """navigation/footer link count anomaly vs sitewide pattern (Notice · Site)
    Outlier page missing standard nav.
    """
    raise NotImplementedError("C077 not yet implemented")


def check_C078(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """breadcrumb missing on deep page (Notice · Page)"""
    raise NotImplementedError("C078 not yet implemented")


def check_C079(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """pagination series missing links to first/last page (Notice · Page)"""
    raise NotImplementedError("C079 not yet implemented")


def check_C080(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """subdomain treated as separate crawl root without cross-linking (Notice · Site)"""
    raise NotImplementedError("C080 not yet implemented")


CHECKS = {
    "C067": check_C067,
    "C068": check_C068,
    "C069": check_C069,
    "C075": check_C075,
    "C077": check_C077,
    "C078": check_C078,
    "C079": check_C079,
    "C080": check_C080,
}
