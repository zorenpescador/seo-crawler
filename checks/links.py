"""Stubs for checks_catalog.csv category: Links.

See checks/crawlability.py for the pattern these stubs follow.
"""
from collections import Counter
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

SKIPPED_HREF_PREFIXES = ("javascript:", "mailto:", "tel:", "#")


def _external_links(html: Any, page_url: Any) -> List[str]:
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
        if parsed.netloc and parsed.netloc.lower() != own_domain:
            links.append(absolute)
    return links


def check_C081(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken external link (4XX/5XX) (Warning · Page)
    Optional: requires the "Check external links" option to be enabled
    during crawl. Without it, site_ctx has no external-link probe data
    and this check finds nothing.
    """
    site_ctx = site_ctx or {}
    status_map = site_ctx.get("external_link_status") or {}
    if not status_map:
        return pages_df.iloc[0:0][["URL"]]

    def _has_broken_external_link(row: pd.Series) -> bool:
        for link in _external_links(row.get("HTML"), row.get("URL")):
            status = status_map.get(link)
            if status is not None and status >= 400:
                return True
        return False

    mask = pages_df.apply(_has_broken_external_link, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_insecure_external_link(html: Any, page_url: Any) -> bool:
    if not html:
        return False
    own_domain = urlparse(str(page_url)).netloc.lower()
    soup = BeautifulSoup(str(html), "html.parser")
    for a in soup.find_all("a", href=True):
        parsed = urlparse(a["href"])
        if parsed.scheme == "http" and parsed.netloc and parsed.netloc.lower() != own_domain:
            return True
    return False


def check_C082(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """external link to a domain with no HTTPS (Notice · Page)"""
    mask = pages_df.apply(lambda row: _has_insecure_external_link(row.get("HTML"), row.get("URL")), axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C083(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """external link redirect chain (Notice · Page)
    Requires the "Check external links" option to be enabled during crawl.
    """
    site_ctx = site_ctx or {}
    redirected_map = site_ctx.get("external_link_redirected") or {}
    if not redirected_map:
        return pages_df.iloc[0:0][["URL"]]

    def _has_redirecting_external_link(row: pd.Series) -> bool:
        return any(redirected_map.get(link) for link in _external_links(row.get("HTML"), row.get("URL")))

    mask = pages_df.apply(_has_redirecting_external_link, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C084(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """link to a disallowed/blocked-by-robots external resource (Notice · Page)
    Requires the "Check external links" option to be enabled during crawl.
    """
    site_ctx = site_ctx or {}
    blocked_map = site_ctx.get("external_link_robots_blocked") or {}
    if not blocked_map:
        return pages_df.iloc[0:0][["URL"]]

    def _links_to_blocked(row: pd.Series) -> bool:
        return any(blocked_map.get(link) for link in _external_links(row.get("HTML"), row.get("URL")))

    mask = pages_df.apply(_links_to_blocked, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _image_urls(html: Any, page_url: Any) -> List[str]:
    if not html:
        return []
    soup = BeautifulSoup(str(html), "html.parser")
    return [urljoin(str(page_url), img["src"].strip()) for img in soup.find_all("img", src=True) if img["src"].strip()]


def check_C085(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken image source (4XX/5XX) (Error · Page)
    <img src> fails to load. Requires the "Check external links" option
    to be enabled during crawl (it probes all images, not just external
    ones, despite the option's name).
    """
    site_ctx = site_ctx or {}
    status_map = site_ctx.get("image_status") or {}
    if not status_map:
        return pages_df.iloc[0:0][["URL"]]

    def _has_broken_image(row: pd.Series) -> bool:
        for img_url in _image_urls(row.get("HTML"), row.get("URL")):
            status = status_map.get(img_url)
            if status is not None and status >= 400:
                return True
        return False

    mask = pages_df.apply(_has_broken_image, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_offsite_image(html: Any, page_url: Any) -> bool:
    if not html:
        return False
    own_domain = urlparse(str(page_url)).netloc.lower()
    soup = BeautifulSoup(str(html), "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        parsed = urlparse(src)
        if parsed.netloc and parsed.netloc.lower() != own_domain:
            return True
    return False


def check_C086(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """image hosted on a different (uncontrolled) domain (Notice · Page)
    Hotlinking risk / dependency risk.
    """
    mask = pages_df.apply(lambda row: _has_offsite_image(row.get("HTML"), row.get("URL")), axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C087(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken favicon (Notice · Site)
    Requires the "Check external links" option to be enabled during crawl.
    """
    site_ctx = site_ctx or {}
    status = site_ctx.get("favicon_status")
    if status is not None and status >= 400:
        return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)
    return pages_df.iloc[0:0][["URL"]]


def check_C088(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken canonical target (canonical URL 4XX/5XX) (Error · Page)
    Only catches targets that are themselves in the crawled URL set.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))

    def _is_broken(canonical: Any) -> bool:
        status = status_map.get(str(canonical).strip())
        return bool(status) and status.startswith(("4", "5"))

    mask = pages_df["Canonical URL"].apply(_is_broken)
    return pages_df.loc[mask, ["URL", "Canonical URL"]].drop_duplicates().reset_index(drop=True)


def _hreflang_targets(html: Any) -> Dict[str, str]:
    if not html:
        return {}
    soup = BeautifulSoup(str(html), "html.parser")
    targets = {}
    for link in soup.find_all("link", attrs={"hreflang": True}):
        rel = link.get("rel") or []
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
        if "alternate" not in rel_str.lower():
            continue
        href = str(link.get("href", "")).strip()
        if href:
            targets[href] = str(link.get("hreflang", "")).strip()
    return targets


def check_C089(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """broken hreflang target (Error · Page)
    Only catches targets that are themselves in the crawled URL set.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))

    def _has_broken_hreflang(html: Any) -> bool:
        for href in _hreflang_targets(html):
            status = status_map.get(href)
            if status and status.startswith(("4", "5")):
                return True
        return False

    mask = pages_df["HTML"].fillna("").apply(_has_broken_hreflang)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


TRACKING_PARAM_NAMES = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid", "msclkid"}


def _has_tracking_param_link(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for a in soup.find_all("a", href=True):
        query = urlparse(a["href"]).query.lower()
        if any(f"{param}=" in query for param in TRACKING_PARAM_NAMES):
            return True
    return False


def check_C090(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """link to a URL with tracking parameters not canonicalized (Notice · Page)"""
    mask = pages_df["HTML"].fillna("").apply(_has_tracking_param_link)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


DEAD_LINK_MIN_REFERRING_PAGES = 3


def check_C091(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """dead outbound link in footer/nav (site-wide template) (Warning · Site)
    Same broken link repeated across many pages. Heuristic: a broken
    external link referenced by 3+ crawled pages, as a proxy for a
    site-wide template link (footer/nav specifically isn't distinguished
    from other page regions). Requires "Check external links" to be
    enabled during crawl.
    """
    site_ctx = site_ctx or {}
    status_map = site_ctx.get("external_link_status") or {}
    broken_links = {url for url, status in status_map.items() if status is not None and status >= 400}
    if not broken_links:
        return pages_df.iloc[0:0][["URL"]]

    referrer_count = Counter()
    referrers_by_link = {}
    for _, row in pages_df.iterrows():
        page_url = str(row["URL"])
        for link in _external_links(row.get("HTML"), row.get("URL")):
            if link in broken_links:
                referrer_count[link] += 1
                referrers_by_link.setdefault(link, set()).add(page_url)

    repeated_links = {link for link, count in referrer_count.items() if count >= DEAD_LINK_MIN_REFERRING_PAGES}
    if not repeated_links:
        return pages_df.iloc[0:0][["URL"]]

    affected_pages = set()
    for link in repeated_links:
        affected_pages.update(referrers_by_link[link])

    return pages_df[pages_df["URL"].astype(str).isin(affected_pages)][["URL"]].drop_duplicates().reset_index(drop=True)


OUTBOUND_LINKS_PER_WORD_MAX = 0.02
OUTBOUND_LINK_COUNT_MIN = 5


def _external_link_count(html: Any, page_url: Any) -> int:
    if not html:
        return 0
    own_domain = urlparse(str(page_url)).netloc.lower()
    soup = BeautifulSoup(str(html), "html.parser")
    count = 0
    for a in soup.find_all("a", href=True):
        parsed = urlparse(a["href"])
        if parsed.netloc and parsed.netloc.lower() != own_domain:
            count += 1
    return count


def check_C092(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """excessive outbound links relative to word count (Notice · Page)
    Heuristic: at least 5 outbound links, and more than 1 per 50 words.
    """
    def _is_excessive(row: pd.Series) -> bool:
        word_count = int(row.get("Word Count") or 0)
        if word_count <= 0:
            return False
        ext_count = _external_link_count(row.get("HTML"), row.get("URL"))
        return ext_count >= OUTBOUND_LINK_COUNT_MIN and (ext_count / word_count) > OUTBOUND_LINKS_PER_WORD_MAX

    mask = pages_df.apply(_is_excessive, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


KNOWN_AFFILIATE_DOMAINS = (
    "amzn.to", "amazon.", "awin1.com", "shareasale.com", "cj.com", "clickbank.net",
    "rakuten", "linksynergy.com", "impact.com", "partnerize.com",
)


def _is_known_affiliate_link(href: str) -> bool:
    parsed = urlparse(href)
    netloc = parsed.netloc.lower()
    if any(domain in netloc for domain in KNOWN_AFFILIATE_DOMAINS):
        return True
    return "tag=" in parsed.query.lower() and "amazon." in netloc


def check_C093(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """affiliate/sponsored links missing rel=sponsored or nofollow (Notice · Page)
    Narrow heuristic: only flags links to a small set of well-known
    affiliate networks/domains, not a general affiliate-link detector.
    """
    def _has_unmarked_affiliate_link(html: Any) -> bool:
        if not html:
            return False
        soup = BeautifulSoup(str(html), "html.parser")
        for a in soup.find_all("a", href=True):
            if not _is_known_affiliate_link(a["href"]):
                continue
            rel = a.get("rel") or []
            rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
            if "sponsored" not in rel_str.lower() and "nofollow" not in rel_str.lower():
                return True
        return False

    mask = pages_df["HTML"].fillna("").apply(_has_unmarked_affiliate_link)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_javascript_void_link(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for a in soup.find_all("a", href=True):
        if a["href"].strip().lower().startswith("javascript:"):
            return True
    return False


def check_C094(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """link with no href fallback (javascript:void) (Notice · Page)"""
    mask = pages_df["HTML"].fillna("").apply(_has_javascript_void_link)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_insecure_form_action(html: Any, page_url: Any) -> bool:
    if not html or not str(page_url).startswith("https://"):
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for form in soup.find_all("form"):
        action = form.get("action") or ""
        if action.startswith("http://"):
            return True
    return False


def check_C095(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """form action pointing to broken/insecure endpoint (Warning · Page)
    Only checks the insecure (http:// action on an https page) case;
    verifying "broken" would require an actual request to the endpoint.
    """
    mask = pages_df.apply(lambda row: _has_insecure_form_action(row.get("HTML"), row.get("URL")), axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {}
