"""Stubs for checks_catalog.csv category: Redirects.

See checks/crawlability.py for the pattern these stubs follow.
"""
import re
from typing import Any, Dict
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup

from checks.architecture import _internal_links

REDIRECT_STATUS_PREFIXES = ("301", "302", "303", "307", "308")
MAX_REDIRECT_CHAIN_HOPS = 20


def _redirect_target_map(pages_df: pd.DataFrame) -> Dict[str, str]:
    if "Redirect Target" not in pages_df.columns:
        return {}
    is_redirect = pages_df["Status"].astype(str).str.startswith(REDIRECT_STATUS_PREFIXES)
    targets = pages_df.loc[is_redirect, "Redirect Target"].fillna("").astype(str)
    urls = pages_df.loc[is_redirect, "URL"].astype(str)
    return {url: target for url, target in zip(urls, targets) if target}


def check_C032(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """redirect loop (Error · Page)
    Redirect chain returns to a previously visited URL. Only detects
    loops fully contained within the crawled set (up to 20 hops).
    """
    redirect_map = _redirect_target_map(pages_df)
    if not redirect_map:
        return pages_df.iloc[0:0][["URL"]]

    def _is_loop(start_url: str) -> bool:
        seen = {start_url}
        current = start_url
        for _ in range(MAX_REDIRECT_CHAIN_HOPS):
            next_url = redirect_map.get(current)
            if not next_url:
                return False
            if next_url in seen:
                return True
            seen.add(next_url)
            current = next_url
        return False

    mask = pages_df["URL"].astype(str).apply(lambda u: u in redirect_map and _is_loop(u))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C033(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """temporary redirect (302/307) used where permanent intended (Warning · Page)
    3XX semantics likely mismatched with intent.
    """
    raise NotImplementedError("C033 not yet implemented")


def check_C034(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """internal links pointing to a redirecting URL instead of final target (Warning · Page)
    Same underlying detection as Internal Link To Redirect (C072); the
    catalog lists it under both Redirects and Site Architecture lenses.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))

    def _has_redirect_link(row: pd.Series) -> bool:
        for link in _internal_links(row.get("HTML"), row.get("URL")):
            status = status_map.get(link["href"])
            if status and status.startswith(REDIRECT_STATUS_PREFIXES):
                return True
        return False

    mask = pages_df.apply(_has_redirect_link, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C035(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """redirect to a 4XX/5XX destination (Error · Page)
    Only catches destinations that are themselves in the crawled set.
    """
    status_map = dict(zip(pages_df["URL"].astype(str), pages_df["Status"].astype(str)))
    redirect_map = _redirect_target_map(pages_df)

    def _target_is_broken(url: str) -> bool:
        target = redirect_map.get(url)
        if not target:
            return False
        target_status = status_map.get(target)
        return bool(target_status) and target_status.startswith(("4", "5"))

    mask = pages_df["URL"].astype(str).apply(_target_is_broken)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_meta_refresh(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("meta", attrs={"http-equiv": re.compile("^refresh$", re.IGNORECASE)}))


def check_C036(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """meta-refresh redirect used instead of HTTP redirect (Notice · Page)
    Non-standard client-side redirect pattern.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_meta_refresh)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C037(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """trailing-slash and non-trailing-slash both resolve without redirect (duplicate URLs) (Warning · Site)
    Both variants return 200 instead of canonicalizing.
    """
    urls = set(pages_df["URL"].astype(str))
    affected = set()
    for url in urls:
        if url.endswith("/"):
            bare = url[:-1]
            if bare in urls:
                affected.add(url)
                affected.add(bare)
    return pages_df[pages_df["URL"].astype(str).isin(affected)][["URL"]].drop_duplicates().reset_index(drop=True)


def check_C038(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """www / non-www both resolve without redirect (Warning · Site)
    Host variants not canonicalized.
    """
    urls = list(pages_df["URL"].astype(str).unique())
    netlocs = {urlparse(u).netloc.lower() for u in urls}
    affected_netlocs = set()
    for netloc in netlocs:
        if netloc.startswith("www.") and netloc[4:] in netlocs:
            affected_netlocs.add(netloc)
            affected_netlocs.add(netloc[4:])
    affected_urls = {u for u in urls if urlparse(u).netloc.lower() in affected_netlocs}
    return pages_df[pages_df["URL"].astype(str).isin(affected_urls)][["URL"]].drop_duplicates().reset_index(drop=True)


def _is_multi_hop_https_upgrade(url: str, redirect_map: Dict[str, str]) -> bool:
    if not url.startswith("http://"):
        return False
    hops = 0
    current = url
    seen = {url}
    for _ in range(MAX_REDIRECT_CHAIN_HOPS):
        next_url = redirect_map.get(current)
        if not next_url or next_url in seen:
            break
        hops += 1
        current = next_url
        seen.add(current)
    return hops > 1 and current.startswith("https://")


def check_C039(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """HTTP->HTTPS redirect chain longer than 1 hop (Warning · Page)
    Protocol upgrade adds unnecessary hops. Only detectable when the
    whole chain is within the crawled set.
    """
    redirect_map = _redirect_target_map(pages_df)
    if not redirect_map:
        return pages_df.iloc[0:0][["URL"]]
    mask = pages_df["URL"].astype(str).apply(lambda u: _is_multi_hop_https_upgrade(u, redirect_map))
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C040(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """excessive redirects site-wide (>5% of crawled URLs) (Warning · Site)
    Aggregate signal of unmanaged redirect debt.
    """
    raise NotImplementedError("C040 not yet implemented")


CHECKS = {
    "C033": check_C033,
    "C040": check_C040,
}
