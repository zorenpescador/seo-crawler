"""Stubs for checks_catalog.csv category: Crawlability & Indexability.

Each function is a placeholder for a check not yet implemented in
health_score.py / site_audit.py. Fill in the body and remove the
NotImplementedError once real logic lands, then wire the check_id into
health_score.CHECK_NAME_TO_CATALOG_ID so it feeds the health score.
"""
from typing import Any, Dict

import pandas as pd


def check_C001(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt missing (Warning · Site)
    No robots.txt found at domain root.
    """
    raise NotImplementedError("C001 not yet implemented")


def check_C002(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt not valid (syntax errors) (Warning · Site)
    robots.txt contains malformed directives.
    """
    raise NotImplementedError("C002 not yet implemented")


def check_C003(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt blocks entire site (Error · Site)
    Disallow: / found for relevant user-agents.
    """
    raise NotImplementedError("C003 not yet implemented")


def check_C004(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """robots.txt blocks CSS/JS resources (Warning · Site)
    Rendering-critical assets disallowed.
    """
    raise NotImplementedError("C004 not yet implemented")


def check_C005(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap.xml missing (Warning · Site)
    No sitemap referenced in robots.txt or at /sitemap.xml.
    """
    raise NotImplementedError("C005 not yet implemented")


def check_C006(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap.xml not valid XML (Error · Site)
    Sitemap fails to parse.
    """
    raise NotImplementedError("C006 not yet implemented")


def check_C007(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains 4XX/5XX URLs (Error · Site)
    URLs listed in sitemap return client/server errors.
    """
    raise NotImplementedError("C007 not yet implemented")


def check_C008(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains redirected URLs (Warning · Site)
    URLs listed in sitemap 3XX-redirect elsewhere.
    """
    raise NotImplementedError("C008 not yet implemented")


def check_C009(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap contains noindex URLs (Warning · Site)
    URLs in sitemap carry a noindex directive.
    """
    raise NotImplementedError("C009 not yet implemented")


def check_C010(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """sitemap not referenced in robots.txt (Notice · Site)
    Sitemap exists but isn't declared.
    """
    raise NotImplementedError("C010 not yet implemented")


def check_C011(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page blocked by robots.txt (Error · Page)
    Crawler already checks this via robotparser; not yet surfaced as a finding.
    """
    raise NotImplementedError("C011 not yet implemented")


def check_C012(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page has noindex directive (Warning · Page)
    meta robots or X-Robots-Tag contains noindex.
    """
    raise NotImplementedError("C012 not yet implemented")


def check_C013(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page has nofollow on all outlinks (Warning · Page)
    meta robots nofollow prevents link equity flow.
    """
    raise NotImplementedError("C013 not yet implemented")


def check_C014(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page not crawlable (timeout/DNS/conn error) (Error · Page)
    Request failed outright.
    """
    raise NotImplementedError("C014 not yet implemented")


def check_C015(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page returns soft 404 (200 status, error-like content) (Warning · Page)
    Heuristic: thin/empty body with 'not found' language but HTTP 200.
    """
    raise NotImplementedError("C015 not yet implemented")


def check_C016(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """conflicting robots signals (meta vs X-Robots-Tag) (Warning · Page)
    HTTP header and HTML meta robots disagree.
    """
    raise NotImplementedError("C016 not yet implemented")


def check_C017(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """canonical points to a blocked/noindex page (Error · Page)
    Canonical target is itself non-indexable.
    """
    raise NotImplementedError("C017 not yet implemented")


def check_C018(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """canonical points to a different domain (Warning · Page)
    Cross-domain canonical, verify intent.
    """
    raise NotImplementedError("C018 not yet implemented")


def check_C019(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """canonical chain (canonical points to a page with its own different canonical) (Warning · Page)
    Canonical does not resolve to a stable target.
    """
    raise NotImplementedError("C019 not yet implemented")


def check_C020(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """paginated page missing rel=next/prev or self-canonical (Notice · Page)
    Pagination signals absent.
    """
    raise NotImplementedError("C020 not yet implemented")


CHECKS = {
    "C001": check_C001,
    "C002": check_C002,
    "C003": check_C003,
    "C004": check_C004,
    "C005": check_C005,
    "C006": check_C006,
    "C007": check_C007,
    "C008": check_C008,
    "C009": check_C009,
    "C010": check_C010,
    "C011": check_C011,
    "C012": check_C012,
    "C013": check_C013,
    "C014": check_C014,
    "C015": check_C015,
    "C016": check_C016,
    "C017": check_C017,
    "C018": check_C018,
    "C019": check_C019,
    "C020": check_C020,
}
