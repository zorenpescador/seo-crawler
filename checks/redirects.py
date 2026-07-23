"""Stubs for checks_catalog.csv category: Redirects.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict

import pandas as pd


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


def check_C036(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """meta-refresh redirect used instead of HTTP redirect (Notice · Page)
    Non-standard client-side redirect pattern.
    """
    raise NotImplementedError("C036 not yet implemented")


def check_C037(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """trailing-slash and non-trailing-slash both resolve without redirect (duplicate URLs) (Warning · Site)
    Both variants return 200 instead of canonicalizing.
    """
    raise NotImplementedError("C037 not yet implemented")


def check_C038(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """www / non-www both resolve without redirect (Warning · Site)
    Host variants not canonicalized.
    """
    raise NotImplementedError("C038 not yet implemented")


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
    "C036": check_C036,
    "C037": check_C037,
    "C038": check_C038,
    "C039": check_C039,
    "C040": check_C040,
}
