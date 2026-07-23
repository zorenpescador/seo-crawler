"""Stubs for checks_catalog.csv category: Site Architecture & Internal Linking (remaining checks).

health_score.py already implements orphan pages and low-internal-link-support.
These stubs cover the rest of the category. See checks/crawlability.py for
the pattern.
"""
from typing import Any, Dict

import pandas as pd


def check_C067(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page more than 3 clicks from homepage (Warning · Site)
    Crawl-depth graph analysis.
    """
    raise NotImplementedError("C067 not yet implemented")


def check_C068(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """page more than 5 clicks from homepage (Error · Site)
    Severe depth.
    """
    raise NotImplementedError("C068 not yet implemented")


def check_C069(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """too few internal links to an important page (Warning · Site)
    Priority page (per target-keyword map) under-linked.
    """
    raise NotImplementedError("C069 not yet implemented")


def check_C070(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """too many internal links on a single page (Notice · Page)
    >100 internal links dilutes equity.
    """
    raise NotImplementedError("C070 not yet implemented")


def check_C071(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken internal link (Error · Page)
    <a href> internal target returns 4XX/5XX.
    """
    raise NotImplementedError("C071 not yet implemented")


def check_C072(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal link to a redirected URL (Warning · Page)"""
    raise NotImplementedError("C072 not yet implemented")


def check_C073(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal link uses nofollow (Notice · Page)
    Unusual for internal navigation, verify intent.
    """
    raise NotImplementedError("C073 not yet implemented")


def check_C074(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal link with empty or generic anchor text ('click here', 'read more') (Notice · Page)"""
    raise NotImplementedError("C074 not yet implemented")


def check_C075(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """internal link anchor text mismatch vs destination topic (Notice · Page)
    Heuristic keyword overlap check.
    """
    raise NotImplementedError("C075 not yet implemented")


def check_C077(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """navigation/footer link count anomaly vs sitewide pattern (Notice · Site)
    Outlier page missing standard nav.
    """
    raise NotImplementedError("C077 not yet implemented")


def check_C078(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """breadcrumb missing on deep page (Notice · Page)"""
    raise NotImplementedError("C078 not yet implemented")


def check_C079(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """pagination series missing links to first/last page (Notice · Page)"""
    raise NotImplementedError("C079 not yet implemented")


def check_C080(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """subdomain treated as separate crawl root without cross-linking (Notice · Site)"""
    raise NotImplementedError("C080 not yet implemented")


CHECKS = {
    "C067": check_C067,
    "C068": check_C068,
    "C069": check_C069,
    "C070": check_C070,
    "C071": check_C071,
    "C072": check_C072,
    "C073": check_C073,
    "C074": check_C074,
    "C075": check_C075,
    "C077": check_C077,
    "C078": check_C078,
    "C079": check_C079,
    "C080": check_C080,
}
