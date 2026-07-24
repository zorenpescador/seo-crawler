"""Stubs for checks_catalog.csv category: HTTPS & Security.

See checks/crawlability.py for the pattern these stubs follow.
"""
from typing import Any, Dict

import pandas as pd
from bs4 import BeautifulSoup

MIXED_CONTENT_TAG_ATTRS = (("img", "src"), ("script", "src"), ("link", "href"))


def check_C022(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """HTTP URLs present in sitemap (Error · Site)
    Sitemap lists http:// instead of https://.
    """
    raise NotImplementedError("C022 not yet implemented")


def _has_mixed_content(row: pd.Series) -> bool:
    url = str(row.get("URL", ""))
    html = row.get("HTML")
    if not url.startswith("https://") or not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for tag, attr in MIXED_CONTENT_TAG_ATTRS:
        for element in soup.find_all(tag):
            value = element.get(attr) or ""
            if value.startswith("http://"):
                return True
    return False


def check_C023(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """mixed content on page (Error · Page)
    HTTPS page loads http:// sub-resources (img/script/css).
    """
    mask = pages_df.apply(_has_mixed_content, axis=1)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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
    "C024": check_C024,
    "C025": check_C025,
    "C026": check_C026,
    "C027": check_C027,
    "C028": check_C028,
    "C029": check_C029,
    "C030": check_C030,
}
