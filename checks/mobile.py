"""Stubs for checks_catalog.csv category: Mobile & Accessibility (remaining checks).

health_score.py already implements images-missing-alt-text. These stubs
cover the rest of the category. See checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd


def check_C129(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """no viewport meta tag (duplicate of Markup check, surfaced here for mobile UX lens) (Warning · Page)"""
    raise NotImplementedError("C129 not yet implemented")


def check_C131(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """empty alt attribute on a non-decorative image (heuristic) (Notice · Page)"""
    raise NotImplementedError("C131 not yet implemented")


def check_C132(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """tap targets likely too small/close (heuristic: many inline <a> in dense text) (Notice · Page)
    Best-effort heuristic, not a full a11y audit.
    """
    raise NotImplementedError("C132 not yet implemented")


def check_C133(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """text likely too small (heuristic: no explicit font-size and small viewport) (Notice · Page)"""
    raise NotImplementedError("C133 not yet implemented")


def check_C134(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """form fields missing associated <label> (Warning · Page)"""
    raise NotImplementedError("C134 not yet implemented")


def check_C135(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """color contrast cannot be assessed without rendering (flagged as unverified) (Notice · Page)
    Static HTML parse only — no rendering, see Non-Goals.
    """
    raise NotImplementedError("C135 not yet implemented")


CHECKS = {
    "C129": check_C129,
    "C131": check_C131,
    "C132": check_C132,
    "C133": check_C133,
    "C134": check_C134,
    "C135": check_C135,
}
