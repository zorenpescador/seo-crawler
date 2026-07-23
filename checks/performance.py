"""Stubs for checks_catalog.csv category: Site Performance (remaining checks).

health_score.py already implements slow-response-time. These stubs cover
the rest of the category. See checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd


def check_C119(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """uncompressed HTML response (no gzip/br Content-Encoding) (Warning · Page)"""
    raise NotImplementedError("C119 not yet implemented")


def check_C120(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """large HTML document size (Notice · Page)
    >2MB.
    """
    raise NotImplementedError("C120 not yet implemented")


def check_C121(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """excessive number of on-page requests inferred (script/link/img tag count) (Notice · Page)
    Proxy metric, not real waterfall.
    """
    raise NotImplementedError("C121 not yet implemented")


def check_C122(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """render-blocking CSS/JS in <head> (Notice · Page)
    Heuristic: <script> without async/defer before body content.
    """
    raise NotImplementedError("C122 not yet implemented")


def check_C123(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """images without explicit width/height (layout shift risk) (Warning · Page)"""
    raise NotImplementedError("C123 not yet implemented")


def check_C124(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """images not using modern formats (webp/avif) where alternatives exist (Notice · Page)"""
    raise NotImplementedError("C124 not yet implemented")


def check_C125(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """no lazy-loading attribute on below-fold images (Notice · Page)"""
    raise NotImplementedError("C125 not yet implemented")


def check_C126(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """Core Web Vitals (LCP/INP/CLS) not measured — lab data only (Notice · Site)
    Requires PageSpeed Insights / CrUX API integration, see Open Questions.
    """
    raise NotImplementedError("C126 not yet implemented")


def check_C127(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """excessive DOM size (Notice · Page)
    >1500 nodes, approximated via tag count.
    """
    raise NotImplementedError("C127 not yet implemented")


def check_C128(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """favicon/static asset caching headers missing (Notice · Page)
    Cache-Control absent on static resources.
    """
    raise NotImplementedError("C128 not yet implemented")


CHECKS = {
    "C119": check_C119,
    "C120": check_C120,
    "C121": check_C121,
    "C122": check_C122,
    "C123": check_C123,
    "C124": check_C124,
    "C125": check_C125,
    "C126": check_C126,
    "C127": check_C127,
    "C128": check_C128,
}
