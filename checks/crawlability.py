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
ROBOTS_KNOWN_DIRECTIVES = {"user-agent", "disallow", "allow", "sitemap", "crawl-delay", "host"}
ROBOTS_ASSET_PATH_PATTERN = re.compile(r"\.(css|js)(\?|$)|/(assets|static|wp-content|wp-includes)/", re.IGNORECASE)


def _robots_meta_content(html: Any) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(str(html), "html.parser")
    meta = soup.find("meta", attrs={"name": ROBOTS_META_NAME_PATTERN})
    if not meta:
        return ""
    return str(meta.get("content", "")).lower()


def _all_urls(pages_df: pd.DataFrame) -> pd.DataFrame:
    """Site-level issue confirmed: every crawled page counts as affected."""
    return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)


def _no_urls(pages_df: pd.DataFrame) -> pd.DataFrame:
    return pages_df.iloc[0:0][["URL"]]


def check_C001(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """robots.txt missing (Warning · Site)
    No robots.txt found at domain root. Site-level: every crawled page
    counts as affected when the finding applies, since it's a whole-site
    condition rather than a per-page one.
    """
    site_ctx = site_ctx or {}
    if site_ctx.get("robots_txt") is None:
        return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C002(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """robots.txt not valid (syntax errors) (Warning · Site)
    Heuristic: any non-comment, non-blank line whose directive isn't one
    of the recognized robots.txt directives.
    """
    site_ctx = site_ctx or {}
    robots_txt = site_ctx.get("robots_txt")
    if not robots_txt:
        return _no_urls(pages_df)
    for line in robots_txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        directive = line.split(":", 1)[0].strip().lower()
        if directive not in ROBOTS_KNOWN_DIRECTIVES:
            return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C003(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """robots.txt blocks entire site (Error · Site)
    Disallow: / found under a wildcard (User-agent: *) block.
    """
    site_ctx = site_ctx or {}
    robots_txt = site_ctx.get("robots_txt")
    if not robots_txt:
        return _no_urls(pages_df)
    current_agent_is_wildcard = False
    for line in robots_txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        directive, _, value = line.partition(":")
        directive = directive.strip().lower()
        value = value.strip()
        if directive == "user-agent":
            current_agent_is_wildcard = value == "*"
        elif directive == "disallow" and current_agent_is_wildcard and value == "/":
            return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C004(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """robots.txt blocks CSS/JS resources (Warning · Site)
    Heuristic: a Disallow rule targets a path with a .css/.js extension
    or a common asset directory (assets, static, wp-content, wp-includes).
    """
    site_ctx = site_ctx or {}
    robots_txt = site_ctx.get("robots_txt")
    if not robots_txt:
        return _no_urls(pages_df)
    for line in robots_txt.splitlines():
        line = line.strip()
        if not line.lower().startswith("disallow:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value and ROBOTS_ASSET_PATH_PATTERN.search(value):
            return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C005(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap.xml missing (Warning · Site)
    No sitemap referenced in robots.txt or found at /sitemap.xml.
    """
    site_ctx = site_ctx or {}
    if not site_ctx.get("sitemap_found"):
        return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C006(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap.xml not valid XML (Error · Site)
    Sitemap fails to parse.
    """
    site_ctx = site_ctx or {}
    if site_ctx.get("sitemap_found") and site_ctx.get("sitemap_valid") is False:
        return _all_urls(pages_df)
    return _no_urls(pages_df)


def check_C007(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap contains 4XX/5XX URLs (Error · Site)
    Only checks sitemap URLs that are themselves in the crawled set.
    """
    site_ctx = site_ctx or {}
    sitemap_urls = set(site_ctx.get("sitemap_urls") or [])
    if not sitemap_urls:
        return _no_urls(pages_df)
    mask = pages_df["URL"].astype(str).isin(sitemap_urls) & pages_df["Status"].astype(str).str.startswith(("4", "5"))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C008(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap contains redirected URLs (Warning · Site)
    Only checks sitemap URLs that are themselves in the crawled set.
    """
    site_ctx = site_ctx or {}
    sitemap_urls = set(site_ctx.get("sitemap_urls") or [])
    if not sitemap_urls:
        return _no_urls(pages_df)
    mask = pages_df["URL"].astype(str).isin(sitemap_urls) & pages_df["Status"].astype(str).str.startswith(
        ("301", "302", "303", "307", "308")
    )
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C009(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap contains noindex URLs (Warning · Site)
    Only checks sitemap URLs that are themselves in the crawled set.
    """
    site_ctx = site_ctx or {}
    sitemap_urls = set(site_ctx.get("sitemap_urls") or [])
    if not sitemap_urls:
        return _no_urls(pages_df)
    is_noindex = pages_df["HTML"].fillna("").apply(lambda html: "noindex" in _robots_meta_content(html))
    mask = pages_df["URL"].astype(str).isin(sitemap_urls) & is_noindex
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C010(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """sitemap not referenced in robots.txt (Notice · Site)
    Sitemap exists but isn't declared.
    """
    site_ctx = site_ctx or {}
    if site_ctx.get("sitemap_found") and not site_ctx.get("sitemap_declared_in_robots"):
        return _all_urls(pages_df)
    return _no_urls(pages_df)


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


def check_C014(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """page not crawlable (timeout/DNS/conn error) (Error · Page)
    Request failed outright. Distinct from an HTTP 4XX/5XX response,
    which the crawler records separately as "HTTP Error".
    """
    if "Crawl Status" not in pages_df.columns:
        return pages_df.iloc[0:0][["URL"]]
    mask = pages_df["Crawl Status"].astype(str).str.startswith("Error")
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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


def check_C016(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """conflicting robots signals (meta vs X-Robots-Tag) (Warning · Page)
    HTTP header and HTML meta robots disagree. Compares only the
    noindex/nofollow directives specifically.
    """
    if "X-Robots-Tag" not in pages_df.columns:
        return pages_df.iloc[0:0][["URL"]]

    def _conflicts(row: pd.Series) -> bool:
        header_value = str(row.get("X-Robots-Tag", "") or "").lower()
        if not header_value:
            return False
        meta_value = _robots_meta_content(row.get("HTML"))
        return any((directive in header_value) != (directive in meta_value) for directive in ("noindex", "nofollow"))

    mask = pages_df.apply(_conflicts, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C017(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """canonical points to a blocked/noindex page (Error · Page)
    Canonical target is itself non-indexable. Only checks noindex (via
    meta robots) against targets in the crawled set; robots.txt-blocked
    targets aren't detectable from crawled data alone.
    """
    noindex_urls = set(
        pages_df.loc[
            pages_df["HTML"].fillna("").apply(lambda html: "noindex" in _robots_meta_content(html)), "URL"
        ].astype(str)
    )

    def _points_to_noindex(row: pd.Series) -> bool:
        canonical = str(row.get("Canonical URL", "")).strip()
        own_url = str(row.get("URL", "")).strip()
        return bool(canonical) and canonical != own_url and canonical in noindex_urls

    mask = pages_df.apply(_points_to_noindex, axis=1)
    return pages_df.loc[mask, ["URL", "Canonical URL"]].drop_duplicates().reset_index(drop=True)


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


def check_C019(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """canonical chain (canonical points to a page with its own different canonical) (Warning · Page)
    Canonical does not resolve to a stable target. Only detectable when
    the chained-to page is itself in the crawled set.
    """
    canonical_map = dict(zip(pages_df["URL"].astype(str), pages_df["Canonical URL"].astype(str)))

    def _is_chain(row: pd.Series) -> bool:
        own_url = str(row.get("URL", "")).strip()
        target = str(row.get("Canonical URL", "")).strip()
        if not target or target == own_url:
            return False
        target_canonical = canonical_map.get(target, "").strip()
        return bool(target_canonical) and target_canonical != target

    mask = pages_df.apply(_is_chain, axis=1)
    return pages_df.loc[mask, ["URL", "Canonical URL"]].drop_duplicates().reset_index(drop=True)


PAGINATION_URL_PATTERN = re.compile(r"[?&](?:page|p)=\d+|/page/\d+", re.IGNORECASE)


def _has_pagination_rel(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("link", attrs={"rel": re.compile(r"\b(next|prev)\b", re.IGNORECASE)}))


def check_C020(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """paginated page missing rel=next/prev or self-canonical (Notice · Page)
    Pagination signals absent. Heuristic: URL looks like a pagination page
    (?page=2, /page/2) but has neither rel=next/prev nor a self-canonical.
    """
    is_paginated = pages_df["URL"].astype(str).str.contains(PAGINATION_URL_PATTERN)
    has_pagination_rel = pages_df["HTML"].fillna("").apply(_has_pagination_rel)
    has_self_canonical = pages_df.apply(
        lambda row: str(row.get("Canonical URL", "")).strip() != ""
        and str(row.get("Canonical URL", "")).strip() == str(row.get("URL", "")).strip(),
        axis=1,
    )
    mask = is_paginated & ~has_pagination_rel & ~has_self_canonical
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {
    "C011": check_C011,
}
