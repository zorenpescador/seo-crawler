"""Stubs for checks_catalog.csv category: Site Architecture & Internal Linking (remaining checks).

health_score.py already implements orphan pages and low-internal-link-support.
These stubs cover the rest of the category. See checks/crawlability.py for
the pattern.
"""
import re
from collections import deque
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


def _click_depths(pages_df: pd.DataFrame) -> Dict[str, int]:
    """BFS click-depth from an inferred homepage over the internal-link graph.

    The homepage is the crawled URL with the shortest path (ties broken
    arbitrarily); if the crawl has no pages, depth is undefined.
    """
    urls = set(pages_df["URL"].astype(str))
    if not urls:
        return {}
    graph = {
        str(row["URL"]): {link["href"] for link in _internal_links(row.get("HTML"), row.get("URL"))}
        for _, row in pages_df.iterrows()
    }
    homepage = min(urls, key=lambda u: len(urlparse(u).path.strip("/")))
    depths = {homepage: 0}
    queue = deque([homepage])
    while queue:
        current = queue.popleft()
        for neighbor in graph.get(current, set()):
            if neighbor in urls and neighbor not in depths:
                depths[neighbor] = depths[current] + 1
                queue.append(neighbor)
    return depths


def check_C067(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page more than 3 clicks from homepage (Warning · Site)
    Crawl-depth graph analysis. Only covers pages reachable from the
    inferred homepage within the crawled set; unreachable pages are
    already covered by Orphan Pages.
    """
    depths = _click_depths(pages_df)
    affected = {url for url, depth in depths.items() if depth > 3}
    return pages_df[pages_df["URL"].astype(str).isin(affected)][["URL"]].drop_duplicates().reset_index(drop=True)


def check_C068(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page more than 5 clicks from homepage (Error · Site)
    Severe depth.
    """
    depths = _click_depths(pages_df)
    affected = {url for url, depth in depths.items() if depth > 5}
    return pages_df[pages_df["URL"].astype(str).isin(affected)][["URL"]].drop_duplicates().reset_index(drop=True)


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


LINK_COUNT_ANOMALY_RATIO = 0.3
LINK_COUNT_ANOMALY_MIN_PAGES = 5


def check_C077(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """navigation/footer link count anomaly vs sitewide pattern (Notice · Site)
    Outlier page missing standard nav. Heuristic: total link count under
    30% of the sitewide median (requires at least 5 crawled pages).
    """
    if len(pages_df) < LINK_COUNT_ANOMALY_MIN_PAGES:
        return pages_df.iloc[0:0][["URL"]]
    counts = pages_df.apply(lambda row: len(_internal_links(row.get("HTML"), row.get("URL"))), axis=1)
    median = counts.median()
    if median <= 0:
        return pages_df.iloc[0:0][["URL"]]
    mask = counts < (median * LINK_COUNT_ANOMALY_RATIO)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


BREADCRUMB_DEPTH_MIN = 3


def _has_breadcrumb(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    if soup.find(attrs={"aria-label": re.compile("breadcrumb", re.IGNORECASE)}):
        return True
    if soup.find(class_=re.compile("breadcrumb", re.IGNORECASE)):
        return True
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        content = script.string or script.get_text()
        if content and "BreadcrumbList" in content:
            return True
    return False


def check_C078(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """breadcrumb missing on deep page (Notice · Page)
    "Deep" is defined as more than 2 clicks from the inferred homepage.
    """
    depths = _click_depths(pages_df)
    deep_urls = {url for url, depth in depths.items() if depth > BREADCRUMB_DEPTH_MIN - 1}

    def _is_deep_without_breadcrumb(row: pd.Series) -> bool:
        return str(row.get("URL", "")) in deep_urls and not _has_breadcrumb(row.get("HTML"))

    mask = pages_df.apply(_is_deep_without_breadcrumb, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_rel(html: Any, rel_name: str) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("link", attrs={"rel": re.compile(rf"\b{rel_name}\b", re.IGNORECASE)}))


def check_C079(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """pagination series missing links to first/last page (Notice · Page)
    Only applies to pages already identified as part of a pagination
    series (i.e. carrying rel=next or rel=prev).
    """
    def _missing_first_or_last(html: Any) -> bool:
        if not (_has_rel(html, "next") or _has_rel(html, "prev")):
            return False
        return not (_has_rel(html, "first") or _has_rel(html, "last"))

    mask = pages_df["HTML"].fillna("").apply(_missing_first_or_last)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C080(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """subdomain treated as separate crawl root without cross-linking (Notice · Site)"""
    raise NotImplementedError("C080 not yet implemented")


CHECKS = {
    "C069": check_C069,
    "C075": check_C075,
    "C080": check_C080,
}
