"""Stubs for checks_catalog.csv category: Markup & Structured Data (remaining checks).

health_score.py already implements missing-schema, missing Open Graph tags,
and missing viewport meta. These stubs cover the rest of the category. See
checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd
from bs4 import BeautifulSoup


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


def _has_twitter_card(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("meta", attrs={"name": "twitter:card"}))


def check_C113(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """Twitter Card tags missing (Notice · Page)"""
    mask = ~pages_df["HTML"].fillna("").apply(_has_twitter_card)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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


def _has_favicon_link(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for link in soup.find_all("link"):
        rel = link.get("rel")
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel or "")
        if "icon" in rel_str.lower():
            return True
    return False


def check_C116(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """favicon not declared via link tag (Notice · Page)"""
    mask = ~pages_df["HTML"].fillna("").apply(_has_favicon_link)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {
    "C109": check_C109,
    "C110": check_C110,
    "C111": check_C111,
    "C114": check_C114,
    "C115": check_C115,
}
