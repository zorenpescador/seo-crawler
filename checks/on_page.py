"""Stubs for checks_catalog.csv category: On-Page & Duplicates (remaining checks).

health_score.py already implements: missing title/description/H1/canonical,
thin content, and duplicate titles/descriptions/H1/body. These stubs cover
the rest of the category. See checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd


def check_C042(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """title too short (Warning · Page)
    <30 chars.
    """
    raise NotImplementedError("C042 not yet implemented")


def check_C043(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """title too long (Warning · Page)
    >60 chars.
    """
    raise NotImplementedError("C043 not yet implemented")


def check_C046(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """meta description too short (Notice · Page)
    <70 chars.
    """
    raise NotImplementedError("C046 not yet implemented")


def check_C047(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """meta description too long (Notice · Page)
    >160 chars.
    """
    raise NotImplementedError("C047 not yet implemented")


def check_C050(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """multiple H1s (Warning · Page)"""
    raise NotImplementedError("C050 not yet implemented")


def check_C052(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """H1 duplicates the title exactly (Notice · Page)
    Missed opportunity for complementary signal.
    """
    raise NotImplementedError("C052 not yet implemented")


def check_C055(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """exact-duplicate page (same content hash, different URL) (Error · Site)
    Byte-identical or near-identical body.
    """
    raise NotImplementedError("C055 not yet implemented")


def check_C057(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """keyword cannibalization (2+ pages targeting same priority keyword) (Warning · Site)
    Cross-reference priority_keywords.csv target mapping.
    """
    raise NotImplementedError("C057 not yet implemented")


def check_C058(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """low text-to-HTML ratio (Notice · Page)
    Page is markup-heavy relative to visible text.
    """
    raise NotImplementedError("C058 not yet implemented")


def check_C059(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """missing language declaration (html lang attribute) (Notice · Page)"""
    raise NotImplementedError("C059 not yet implemented")


def check_C060(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """broken heading hierarchy (e.g. H1 -> H3, skipping H2) (Notice · Page)"""
    raise NotImplementedError("C060 not yet implemented")


def check_C061(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """URL contains excessive parameters (Notice · Page)
    >3 query parameters, duplicate-content risk.
    """
    raise NotImplementedError("C061 not yet implemented")


def check_C062(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """URL is excessively long (Notice · Page)
    >115 characters.
    """
    raise NotImplementedError("C062 not yet implemented")


def check_C063(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """non-descriptive URL (auto-generated IDs/slugs) (Notice · Page)"""
    raise NotImplementedError("C063 not yet implemented")


def check_C064(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """underscores used in URL instead of hyphens (Notice · Page)"""
    raise NotImplementedError("C064 not yet implemented")


def check_C065(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """uppercase characters in URL (Notice · Page)
    Case-variant duplicate risk.
    """
    raise NotImplementedError("C065 not yet implemented")


CHECKS = {
    "C042": check_C042,
    "C043": check_C043,
    "C046": check_C046,
    "C047": check_C047,
    "C050": check_C050,
    "C052": check_C052,
    "C055": check_C055,
    "C057": check_C057,
    "C058": check_C058,
    "C059": check_C059,
    "C060": check_C060,
    "C061": check_C061,
    "C062": check_C062,
    "C063": check_C063,
    "C064": check_C064,
    "C065": check_C065,
}
