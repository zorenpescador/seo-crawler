"""Stubs for checks_catalog.csv category: Site Performance (remaining checks).

health_score.py already implements slow-response-time. These stubs cover
the rest of the category. See checks/crawlability.py for the pattern.
"""
from typing import Any, Dict
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup

LEGACY_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")


def check_C119(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """uncompressed HTML response (no gzip/br Content-Encoding) (Warning · Page)"""
    if "Content-Encoding" not in pages_df.columns:
        return pages_df.iloc[0:0][["URL"]]
    mask = pages_df["Content-Encoding"].fillna("").astype(str).str.strip().eq("")
    if "Crawl Status" in pages_df.columns:
        mask = mask & pages_df["Crawl Status"].astype(str).eq("Success")
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C120(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """large HTML document size (Notice · Page)
    >2MB.
    """
    raise NotImplementedError("C120 not yet implemented")


INFERRED_REQUEST_COUNT_MAX = 100


def _inferred_request_count(html: Any) -> int:
    if not html:
        return 0
    soup = BeautifulSoup(str(html), "html.parser")
    return len(soup.find_all(["script", "link", "img"]))


def check_C121(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """excessive number of on-page requests inferred (script/link/img tag count) (Notice · Page)
    Proxy metric, not real waterfall.
    """
    counts = pages_df["HTML"].fillna("").apply(_inferred_request_count)
    return pages_df.loc[counts.gt(INFERRED_REQUEST_COUNT_MAX), ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_render_blocking_script(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    head = soup.find("head")
    if not head:
        return False
    for script in head.find_all("script", src=True):
        if not script.has_attr("async") and not script.has_attr("defer"):
            return True
    return False


def check_C122(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """render-blocking CSS/JS in <head> (Notice · Page)
    Heuristic: <script src> in <head> without async/defer before body content.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_render_blocking_script)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_image_missing_dimensions(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return any(not img.get("width") or not img.get("height") for img in soup.find_all("img"))


def check_C123(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """images without explicit width/height (layout shift risk) (Warning · Page)"""
    mask = pages_df["HTML"].fillna("").apply(_has_image_missing_dimensions)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def _has_legacy_format_image(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        path = urlparse(src).path.lower()
        if path.endswith(LEGACY_IMAGE_EXTENSIONS):
            return True
    return False


def check_C124(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """images not using modern formats (webp/avif) where alternatives exist (Notice · Page)
    Heuristic based on file extension only; doesn't verify a webp/avif
    alternative is actually available server-side.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_legacy_format_image)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


ABOVE_FOLD_IMAGE_COUNT = 1


def _has_unlazy_below_fold_image(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    images = soup.find_all("img")
    below_fold = images[ABOVE_FOLD_IMAGE_COUNT:]
    return any(str(img.get("loading", "")).lower() != "lazy" for img in below_fold)


def check_C125(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """no lazy-loading attribute on below-fold images (Notice · Page)
    Without rendering, "below-fold" is approximated as every image after
    the first one in document order.
    """
    mask = pages_df["HTML"].fillna("").apply(_has_unlazy_below_fold_image)
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C126(pages_df: pd.DataFrame, site_ctx: Dict[str, Any]) -> None:
    """Core Web Vitals (LCP/INP/CLS) not measured — lab data only (Notice · Site)
    Requires PageSpeed Insights / CrUX API integration, see Open Questions.
    """
    raise NotImplementedError("C126 not yet implemented")


DOM_SIZE_MAX_NODES = 1500


def _tag_count(html: Any) -> int:
    if not html:
        return 0
    soup = BeautifulSoup(str(html), "html.parser")
    return len(soup.find_all(True))


def check_C127(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """excessive DOM size (Notice · Page)
    >1500 nodes, approximated via tag count. Pages beyond the crawler's
    12,000-character HTML excerpt will undercount, same caveat as the
    other HTML-derived checks in this package.
    """
    counts = pages_df["HTML"].fillna("").apply(_tag_count)
    return pages_df.loc[counts.gt(DOM_SIZE_MAX_NODES), ["URL"]].drop_duplicates().reset_index(drop=True)


def check_C128(pages_df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> pd.DataFrame:
    """favicon/static asset caching headers missing (Notice · Page)
    Cache-Control absent on static resources. Proxy: uses the page's own
    Cache-Control header, since the crawler doesn't separately request
    static assets (images/CSS/JS/favicon) to read their own headers.
    """
    if "Cache-Control" not in pages_df.columns:
        return pages_df.iloc[0:0][["URL"]]
    mask = pages_df["Cache-Control"].fillna("").astype(str).str.strip().eq("")
    if "Crawl Status" in pages_df.columns:
        mask = mask & pages_df["Crawl Status"].astype(str).eq("Success")
    return pages_df.loc[mask, ["URL"]].drop_duplicates().reset_index(drop=True)


CHECKS = {
    "C120": check_C120,
    "C126": check_C126,
}
