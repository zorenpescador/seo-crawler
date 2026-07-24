"""Stubs for checks_catalog.csv category: Redirects.

See checks/crawlability.py for the pattern these stubs follow.
"""
import re
from typing import Any, Dict
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup


def check_C032(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """redirect loop (Error · Page)
    Redirect chain returns to a previously visited URL.
    """
    raise NotImplementedError("C032 not yet implemented")


def check_C033(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """temporary redirect (302/307) used where permanent intended (Warning · Page)
    3XX semantics likely mismatched with intent.
    """
    raise NotImplementedError("C033 not yet implemented")


def check_C034(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal links pointing to a redirecting URL instead of final target (Warning · Page)
    Wastes crawl budget / link equity.
    """
    raise NotImplementedError("C034 not yet implemented")


def check_C035(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """redirect to a 4XX/5XX destination (Error · Page)
    Redirect resolves to a broken page.
    """
    raise NotImplementedError("C035 not yet implemented")


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


def check_C039(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """HTTP->HTTPS redirect chain longer than 1 hop (Warning · Page)
    Protocol upgrade adds unnecessary hops.
    """
    raise NotImplementedError("C039 not yet implemented")


def check_C040(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """excessive redirects site-wide (>5% of crawled URLs) (Warning · Site)
    Aggregate signal of unmanaged redirect debt.
    """
    raise NotImplementedError("C040 not yet implemented")


CHECKS = {
    "C032": check_C032,
    "C033": check_C033,
    "C034": check_C034,
    "C035": check_C035,
    "C039": check_C039,
    "C040": check_C040,
}
