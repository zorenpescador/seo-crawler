"""Stubs for checks_catalog.csv category: Mobile & Accessibility (remaining checks).

health_score.py already implements images-missing-alt-text. These stubs
cover the rest of the category. See checks/crawlability.py for the pattern.
"""
from typing import Any, Dict

import pandas as pd
from bs4 import BeautifulSoup


def _has_viewport_meta(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("meta", attrs={"name": "viewport"}))


def check_C129(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """no viewport meta tag (duplicate of Markup check, surfaced here for mobile UX lens) (Warning · Page)
    Same underlying detection as Missing Viewport Meta (C117); the catalog
    intentionally lists it twice for two different reporting lenses.
    """
    mask = ~pages_df["HTML"].fillna("").apply(_has_viewport_meta)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


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


NON_LABELABLE_INPUT_TYPES = {"hidden", "submit", "button", "image", "reset"}


def _has_unlabeled_form_field(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    label_fors = {lbl.get("for") for lbl in soup.find_all("label") if lbl.get("for")}
    for field in soup.find_all(["input", "select", "textarea"]):
        if field.name == "input" and str(field.get("type", "text")).lower() in NON_LABELABLE_INPUT_TYPES:
            continue
        field_id = field.get("id")
        if field_id and field_id in label_fors:
            continue
        if field.find_parent("label"):
            continue
        if field.get("aria-label") or field.get("aria-labelledby"):
            continue
        return True
    return False


def check_C134(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """form fields missing associated <label> (Warning · Page)
    A field counts as labeled if it has a matching <label for=id>, is
    wrapped in a <label>, or carries aria-label/aria-labelledby.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_unlabeled_form_field)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C135(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """color contrast cannot be assessed without rendering (flagged as unverified) (Notice · Page)
    Static HTML parse only — no rendering, see Non-Goals.
    """
    raise NotImplementedError("C135 not yet implemented")


CHECKS = {
    "C131": check_C131,
    "C132": check_C132,
    "C133": check_C133,
    "C135": check_C135,
}
