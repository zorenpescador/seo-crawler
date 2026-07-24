"""Stubs for checks_catalog.csv category: HTTPS & Security.

See checks/crawlability.py for the pattern these stubs follow.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pandas as pd
from bs4 import BeautifulSoup

MIXED_CONTENT_TAG_ATTRS = (("img", "src"), ("script", "src"), ("link", "href"))
SSL_EXPIRY_WARNING_DAYS = 30


def check_C022(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """HTTP URLs present in sitemap (Error · Site)
    Sitemap lists http:// instead of https://.
    """
    site_ctx = site_ctx or {}
    sitemap_urls = site_ctx.get("sitemap_urls") or []
    if any(str(u).startswith("http://") for u in sitemap_urls):
        return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)
    return pages_df.iloc[0:0][["URL"]]


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


def check_C024(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """no automatic HTTP->HTTPS redirect (Error · Site)
    http:// version does not redirect to https://. Only checks http://
    URLs actually encountered during the crawl; doesn't proactively fetch
    the http:// variant of every https:// page.
    """
    http_urls = pages_df["URL"].astype(str).str.startswith("http://")
    if not http_urls.any():
        return pages_df.iloc[0:0][["URL"]]
    redirect_target = pages_df.get("Redirect Target", pd.Series([""] * len(pages_df), index=pages_df.index))
    redirect_target = redirect_target.fillna("").astype(str)
    is_redirect = pages_df["Status"].astype(str).str.startswith(("301", "302", "303", "307", "308"))
    upgrades_to_https = is_redirect & redirect_target.str.startswith("https://")
    mask = http_urls & ~upgrades_to_https
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C025(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """missing HSTS header (Warning · Site)
    Strict-Transport-Security header absent. Only meaningful for HTTPS
    pages; requires the crawler to have captured response headers.
    """
    if "Strict-Transport-Security" not in pages_df.columns:
        return pages_df.iloc[0:0][["URL"]]
    is_https = pages_df["URL"].astype(str).str.startswith("https://")
    missing_hsts = pages_df["Strict-Transport-Security"].fillna("").astype(str).str.strip().eq("")
    mask = is_https & missing_hsts
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C026(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """SSL certificate expired (Error · Site)
    Certificate validity end date has passed. An expired cert fails the
    handshake before notAfter can be read, so this relies on the
    "expired" flag classified from the handshake's own error message.
    """
    site_ctx = site_ctx or {}
    ssl_info = site_ctx.get("ssl_info") or {}
    not_after = ssl_info.get("not_after")
    is_expired = ssl_info.get("expired") or (not_after and not_after < datetime.now(timezone.utc))
    if is_expired:
        return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)
    return pages_df.iloc[0:0][["URL"]]


def check_C027(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """SSL certificate expiring soon (<30 days) (Warning · Site)
    Certificate nearing expiry.
    """
    site_ctx = site_ctx or {}
    not_after = (site_ctx.get("ssl_info") or {}).get("not_after")
    if not not_after:
        return pages_df.iloc[0:0][["URL"]]
    now = datetime.now(timezone.utc)
    if now <= not_after < now + timedelta(days=SSL_EXPIRY_WARNING_DAYS):
        return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)
    return pages_df.iloc[0:0][["URL"]]


def check_C028(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """SSL certificate hostname mismatch (Error · Site)
    Cert CN/SAN doesn't match requested host.
    """
    site_ctx = site_ctx or {}
    ssl_info = site_ctx.get("ssl_info") or {}
    if ssl_info.get("checked") and ssl_info.get("hostname_matches") is False:
        return pages_df[["URL"]].drop_duplicates().reset_index(drop=True)
    return pages_df.iloc[0:0][["URL"]]


def check_C029(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """outdated TLS protocol supported (TLS 1.0/1.1) (Warning · Site)
    Legacy insecure protocol still negotiable.
    """
    raise NotImplementedError("C029 not yet implemented")


SECURITY_HEADER_COLUMNS = ["X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy"]


def check_C030(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """missing security headers (X-Content-Type-Options, X-Frame-Options, CSP) (Notice · Page)
    Common hardening headers absent. Flags pages missing all three,
    rather than any one, to avoid noise from the fact that CSP in
    particular is uncommon even on well-secured sites.
    """
    for col in SECURITY_HEADER_COLUMNS:
        if col not in pages_df.columns:
            return pages_df.iloc[0:0][["URL"]]
    missing_all = pages_df[SECURITY_HEADER_COLUMNS].fillna("").apply(
        lambda row: all(str(v).strip() == "" for v in row), axis=1
    )
    return pages_df.loc[missing_all, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {
    "C029": check_C029,
}
