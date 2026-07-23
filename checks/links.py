"""Stubs for checks_catalog.csv category: Links.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict

import pandas as pd


def check_C081(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken external link (4XX/5XX) (Warning · Page)
    Optional: requires --check-external-links flag (slower).
    """
    raise NotImplementedError("C081 not yet implemented")


def check_C082(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """external link to a domain with no HTTPS (Notice · Page)"""
    raise NotImplementedError("C082 not yet implemented")


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


def check_C086(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """image hosted on a different (uncontrolled) domain (Notice · Page)
    Hotlinking risk / dependency risk.
    """
    raise NotImplementedError("C086 not yet implemented")


def check_C087(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken favicon (Notice · Site)"""
    raise NotImplementedError("C087 not yet implemented")


def check_C088(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken canonical target (canonical URL 4XX/5XX) (Error · Page)"""
    raise NotImplementedError("C088 not yet implemented")


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


def check_C092(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """excessive outbound links relative to word count (Notice · Page)"""
    raise NotImplementedError("C092 not yet implemented")


def check_C093(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """affiliate/sponsored links missing rel=sponsored or nofollow (Notice · Page)"""
    raise NotImplementedError("C093 not yet implemented")


def check_C094(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """link with no href fallback (javascript:void) (Notice · Page)"""
    raise NotImplementedError("C094 not yet implemented")


def check_C095(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """form action pointing to broken/insecure endpoint (Warning · Page)"""
    raise NotImplementedError("C095 not yet implemented")


CHECKS = {
    "C081": check_C081,
    "C082": check_C082,
    "C083": check_C083,
    "C084": check_C084,
    "C085": check_C085,
    "C086": check_C086,
    "C087": check_C087,
    "C088": check_C088,
    "C089": check_C089,
    "C090": check_C090,
    "C091": check_C091,
    "C092": check_C092,
    "C093": check_C093,
    "C094": check_C094,
    "C095": check_C095,
}
