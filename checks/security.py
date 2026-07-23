"""Stubs for checks_catalog.csv category: HTTPS & Security.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict

import pandas as pd


def check_C022(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """HTTP URLs present in sitemap (Error · Site)
    Sitemap lists http:// instead of https://.
    """
    raise NotImplementedError("C022 not yet implemented")


def check_C023(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """mixed content on page (Error · Page)
    HTTPS page loads http:// sub-resources (img/script/css).
    """
    raise NotImplementedError("C023 not yet implemented")


def check_C024(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """no automatic HTTP->HTTPS redirect (Error · Site)
    http:// version does not redirect to https://.
    """
    raise NotImplementedError("C024 not yet implemented")


def check_C025(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """missing HSTS header (Warning · Site)
    Strict-Transport-Security header absent.
    """
    raise NotImplementedError("C025 not yet implemented")


def check_C026(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """SSL certificate expired (Error · Site)
    Certificate validity end date has passed.
    """
    raise NotImplementedError("C026 not yet implemented")


def check_C027(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """SSL certificate expiring soon (<30 days) (Warning · Site)
    Certificate nearing expiry.
    """
    raise NotImplementedError("C027 not yet implemented")


def check_C028(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """SSL certificate hostname mismatch (Error · Site)
    Cert CN/SAN doesn't match requested host.
    """
    raise NotImplementedError("C028 not yet implemented")


def check_C029(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """outdated TLS protocol supported (TLS 1.0/1.1) (Warning · Site)
    Legacy insecure protocol still negotiable.
    """
    raise NotImplementedError("C029 not yet implemented")


def check_C030(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """missing security headers (X-Content-Type-Options, X-Frame-Options, CSP) (Notice · Page)
    Common hardening headers absent.
    """
    raise NotImplementedError("C030 not yet implemented")


CHECKS = {
    "C022": check_C022,
    "C023": check_C023,
    "C024": check_C024,
    "C025": check_C025,
    "C026": check_C026,
    "C027": check_C027,
    "C028": check_C028,
    "C029": check_C029,
    "C030": check_C030,
}
