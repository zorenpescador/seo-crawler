"""Stubs for checks_catalog.csv category: Links.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup


def check_C081(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken external link (4XX/5XX) (Warning · Page)
    Optional: requires --check-external-links flag (slower).
    """
    raise NotImplementedError("C081 not yet implemented")


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


def check_C083(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """external link redirect chain (Notice · Page)"""
    raise NotImplementedError("C083 not yet implemented")


def check_C084(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """link to a disallowed/blocked-by-robots external resource (Notice · Page)"""
    raise NotImplementedError("C084 not yet implemented")


def check_C085(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken image source (4XX/5XX) (Error · Page)
    <img src> fails to load.
    """
    raise NotImplementedError("C085 not yet implemented")


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


def check_C087(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken favicon (Notice · Site)"""
    raise NotImplementedError("C087 not yet implemented")


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


def check_C089(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken hreflang target (Error · Page)
    See International SEO category for full hreflang set.
    """
    raise NotImplementedError("C089 not yet implemented")


def check_C090(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """link to a URL with tracking parameters not canonicalized (Notice · Page)"""
    raise NotImplementedError("C090 not yet implemented")


def check_C091(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """dead outbound link in footer/nav (site-wide template) (Warning · Site)
    Same broken link repeated across many pages.
    """
    raise NotImplementedError("C091 not yet implemented")


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


def check_C093(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """affiliate/sponsored links missing rel=sponsored or nofollow (Notice · Page)"""
    raise NotImplementedError("C093 not yet implemented")


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


CHECKS = {
    "C081": check_C081,
    "C083": check_C083,
    "C084": check_C084,
    "C085": check_C085,
    "C087": check_C087,
    "C089": check_C089,
    "C090": check_C090,
    "C091": check_C091,
    "C093": check_C093,
}
