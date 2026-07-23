"""Stubs for checks_catalog.csv category: Markup & Structured Data (remaining checks).

health_score.py already implements missing-schema, missing Open Graph tags,
and missing viewport meta. These stubs cover the rest of the category. See
checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd


def check_C109(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """structured data has invalid/malformed JSON-LD (Error · Page)
    JSON parse failure.
    """
    raise NotImplementedError("C109 not yet implemented")


def check_C110(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """structured data missing required fields for declared @type (Warning · Page)
    e.g. Organization missing 'name'.
    """
    raise NotImplementedError("C110 not yet implemented")


def check_C111(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """structured data type mismatch vs visible page content (Notice · Page)
    e.g. Product schema on a blog post.
    """
    raise NotImplementedError("C111 not yet implemented")


def check_C113(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """Twitter Card tags missing (Notice · Page)"""
    raise NotImplementedError("C113 not yet implemented")


def check_C114(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """AMP page missing amphtml link on canonical (Notice · Page)
    Only relevant if AMP is in use.
    """
    raise NotImplementedError("C114 not yet implemented")


def check_C115(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """AMP page has validation errors (Warning · Page)
    Requires AMP validator dependency.
    """
    raise NotImplementedError("C115 not yet implemented")


def check_C116(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """favicon not declared via link tag (Notice · Page)"""
    raise NotImplementedError("C116 not yet implemented")


CHECKS = {
    "C109": check_C109,
    "C110": check_C110,
    "C111": check_C111,
    "C113": check_C113,
    "C114": check_C114,
    "C115": check_C115,
    "C116": check_C116,
}
