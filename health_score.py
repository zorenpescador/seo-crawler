import hashlib
import os
import re
from collections import Counter
from typing import Any, Dict, List

import pandas as pd
from bs4 import BeautifulSoup

from checks.markup import check_C109, check_C113, check_C116
from checks.performance import check_C123, check_C124, check_C127
from checks.on_page import check_C042, check_C043, check_C046, check_C047, check_C050, check_C052, check_C058, check_C059, check_C061, check_C062, check_C064, check_C065


SEVERITY_WEIGHTS = {
    "Error": 3,
    "Warning": 2,
    "Notice": 1,
}

CATEGORY_WEIGHTS = {
    "Crawlability & Indexability": 10,
    "HTTPS & Security": 10,
    "Redirects": 10,
    "On-Page & Duplicates": 10,
    "Site Architecture & Internal Linking": 10,
    "Links": 10,
    "International SEO": 10,
    "Markup & Structured Data": 10,
    "Site Performance": 10,
    "Mobile & Accessibility": 10,
}

CATEGORY_LABELS = {
    "Crawlability & Indexability": "crawlability",
    "HTTPS & Security": "security",
    "Redirects": "redirects",
    "On-Page & Duplicates": "on_page",
    "Site Architecture & Internal Linking": "architecture",
    "Links": "links",
    "International SEO": "international",
    "Markup & Structured Data": "markup",
    "Site Performance": "performance",
    "Mobile & Accessibility": "mobile",
}

FALLBACK_CHECK_CATALOG = {
    "Orphan Pages": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "URLs are present in the crawl surface but not discovered through internal links.",
    },
    "Non-HTTPS Pages": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "Some pages are being served over an insecure HTTP URL.",
    },
    "Redirecting Pages": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "Detected 3xx redirects in the crawl results.",
    },
    "Duplicate Titles": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Multiple URLs share the same title text.",
    },
    "Duplicate Meta Descriptions": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Multiple URLs share the same description text.",
    },
    "Duplicate H1 Tags": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Multiple URLs share the same H1 text.",
    },
    "Duplicate Body Content": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Normalized body content is duplicated across pages.",
    },
    "Missing Title": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Pages are missing a title tag.",
    },
    "Missing Description": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are missing a meta description.",
    },
    "Missing H1": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Pages are missing an H1 tag.",
    },
    "Missing Canonical": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are missing a canonical link.",
    },
    "Title Too Short": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Titles are under 30 characters.",
    },
    "Title Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Titles are over 60 characters.",
    },
    "Meta Description Too Short": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Meta descriptions are under 70 characters.",
    },
    "Meta Description Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Meta descriptions are over 160 characters.",
    },
    "Multiple H1s": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages contain more than one H1 tag.",
    },
    "Missing Language Declaration": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Pages are missing an html lang attribute.",
    },
    "H1 Duplicates Title": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "The H1 text is identical to the title tag.",
    },
    "URL Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs are over 115 characters.",
    },
    "URL Contains Uppercase": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs contain uppercase characters, a case-variant duplicate risk.",
    },
    "URL Contains Underscores": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs use underscores instead of hyphens as word separators.",
    },
    "URL Excessive Parameters": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs have more than 3 query parameters, a duplicate-content risk.",
    },
    "Low Text-to-HTML Ratio": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Pages are markup-heavy relative to visible text.",
    },
    "Missing Favicon Link": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages don't declare a favicon via a <link rel=icon> tag.",
    },
    "Missing Twitter Card Tags": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages are missing a twitter:card meta tag.",
    },
    "Invalid Structured Data": {
        "category": "Markup & Structured Data",
        "severity": "Error",
        "notes": "Pages have a JSON-LD script block that fails to parse.",
    },
    "Images Missing Dimensions": {
        "category": "Site Performance",
        "severity": "Warning",
        "notes": "Images are missing explicit width/height attributes (layout shift risk).",
    },
    "Excessive DOM Size": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Pages have more than 1500 DOM nodes, approximated via tag count.",
    },
    "Legacy Image Formats": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Images use legacy formats (jpg/png/gif/bmp) instead of webp/avif.",
    },
    "Thin Content": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are below the 300-word content threshold.",
    },
    "Low Internal Link Support": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Warning",
        "notes": "Pages have very few internal links, which can weaken crawl depth and equity distribution.",
    },
    "Missing Schema": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages do not expose JSON-LD or structured data markup.",
    },
    "Missing Open Graph Tags": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages are missing Open Graph title or description metadata.",
    },
    "Slow Response Time": {
        "category": "Site Performance",
        "severity": "Warning",
        "notes": "Several pages exceed the 2.5s response threshold.",
    },
    "Missing Viewport Meta": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Pages are missing a viewport meta tag, which can hurt mobile rendering signals.",
    },
    "Images Missing Alt Text": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Pages contain images that do not have a usable alt attribute.",
    },
}

# checks_catalog.csv describes each check in prose (e.g. "missing <title>") that
# doesn't match the short display names used below (e.g. "Missing Title"), so we
# join on the stable check_id instead of the free-text check_name.
CHECK_NAME_TO_CATALOG_ID = {
    "Orphan Pages": "C066",
    "Non-HTTPS Pages": "C021",
    "Redirecting Pages": "C031",
    "Duplicate Titles": "C044",
    "Duplicate Meta Descriptions": "C048",
    "Duplicate H1 Tags": "C051",
    "Duplicate Body Content": "C054",
    "Missing Title": "C041",
    "Missing Description": "C045",
    "Missing H1": "C049",
    "Missing Canonical": "C056",
    "Title Too Short": "C042",
    "Title Too Long": "C043",
    "Meta Description Too Short": "C046",
    "Meta Description Too Long": "C047",
    "Multiple H1s": "C050",
    "Missing Language Declaration": "C059",
    "H1 Duplicates Title": "C052",
    "URL Too Long": "C062",
    "URL Contains Uppercase": "C065",
    "URL Contains Underscores": "C064",
    "URL Excessive Parameters": "C061",
    "Low Text-to-HTML Ratio": "C058",
    "Missing Favicon Link": "C116",
    "Missing Twitter Card Tags": "C113",
    "Invalid Structured Data": "C109",
    "Images Missing Dimensions": "C123",
    "Excessive DOM Size": "C127",
    "Legacy Image Formats": "C124",
    "Thin Content": "C053",
    "Low Internal Link Support": "C076",
    "Missing Schema": "C108",
    "Missing Open Graph Tags": "C112",
    "Slow Response Time": "C118",
    "Missing Viewport Meta": "C117",
    "Images Missing Alt Text": "C130",
}


def _load_check_catalog() -> Dict[str, Dict[str, str]]:
    catalog_path = os.path.join(os.path.dirname(__file__), "checks_catalog.csv")
    if not os.path.exists(catalog_path):
        return {}

    try:
        catalog_df = pd.read_csv(catalog_path)
    except Exception:
        return {}

    catalog: Dict[str, Dict[str, str]] = {}
    for _, row in catalog_df.iterrows():
        check_id = str(row.get("check_id", "")).strip()
        if not check_id:
            continue
        catalog[check_id] = {
            "category": str(row.get("category", "On-Page & Duplicates")).strip(),
            "severity": str(row.get("severity", "Notice")).strip(),
            "notes": str(row.get("notes", "")).strip(),
        }
    return catalog


CHECK_CATALOG_BY_ID = _load_check_catalog()


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _html_to_text(html: Any) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(str(html), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return _normalize_text(soup.get_text(" ", strip=True))


def _content_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha1(text.lower().encode("utf-8")).hexdigest()


def _extract_internal_targets(html: Any) -> List[str]:
    if not html:
        return []
    soup = BeautifulSoup(str(html), "html.parser")
    targets = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if href.startswith("http://") or href.startswith("https://"):
            targets.append(href)
    return targets


def _has_viewport_meta(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("meta", attrs={"name": "viewport"}))


def _missing_alt_image_pages(html_series: pd.Series) -> pd.DataFrame:
    page_urls = []
    for url, html in html_series.items():
        if not html:
            continue
        soup = BeautifulSoup(str(html), "html.parser")
        missing_alt = [img for img in soup.find_all("img") if not img.get("alt") or not img.get("alt").strip()]
        if missing_alt:
            page_urls.append(url)
    return pd.DataFrame({"URL": page_urls})


def _grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _catalog_reference(check_name: str) -> Dict[str, Any]:
    catalog_id = CHECK_NAME_TO_CATALOG_ID.get(check_name)
    templated = CHECK_CATALOG_BY_ID.get(catalog_id, {}) if catalog_id else {}
    if not templated:
        templated = FALLBACK_CHECK_CATALOG.get(check_name, {})
    return {
        "category": templated.get("category", "On-Page & Duplicates"),
        "severity": templated.get("severity", "Notice"),
        "notes": templated.get("notes", ""),
    }


def _add_finding(findings: List[Dict[str, Any]], *, category: str, check: str, severity: str, affected_pages: int, total_pages: int, notes: str = ""):
    if affected_pages <= 0 or total_pages <= 0:
        return
    deduction = round((affected_pages / total_pages) * SEVERITY_WEIGHTS[severity], 4)
    findings.append({
        "Category": category,
        "Check": check,
        "Severity": severity,
        "Affected Pages": affected_pages,
        "Deduction": deduction,
        "Impact Score": int(affected_pages * SEVERITY_WEIGHTS[severity]),
        "Notes": notes,
    })


def build_site_health_report(df: pd.DataFrame) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            "health_score": 100,
            "grade": "A",
            "pages_crawled": 0,
            "issues_found": 0,
            "checks": pd.DataFrame(columns=["Category", "Check", "Severity", "Affected Pages", "Deduction", "Impact Score", "Notes"]),
            "quick_wins": pd.DataFrame(columns=["Issue", "Impact", "Affected Pages", "Category", "Priority"]),
            "category_scores": pd.DataFrame(columns=["Category", "Weight", "Score"]),
        }

    work_df = df.copy()
    work_df["Content Text"] = work_df.get("Content Text", work_df.get("HTML", "")).fillna("")
    work_df["Body Text"] = work_df["Content Text"].apply(_html_to_text)
    work_df["Content Hash"] = work_df["Body Text"].apply(_content_hash)

    total_pages = len(work_df)
    findings: List[Dict[str, Any]] = []

    dup_titles = work_df[
        work_df.duplicated(subset=["Title"], keep=False)
        & work_df["Title"].astype(str).str.strip().astype(bool)
    ][["URL", "Title"]].drop_duplicates().reset_index(drop=True)

    dup_desc = work_df[
        work_df.duplicated(subset=["Description"], keep=False)
        & work_df["Description"].astype(str).str.strip().astype(bool)
    ][["URL", "Description"]].drop_duplicates().reset_index(drop=True)

    dup_h1 = work_df[
        work_df.duplicated(subset=["H1"], keep=False)
        & work_df["H1"].astype(str).str.strip().astype(bool)
    ][["URL", "H1"]].drop_duplicates().reset_index(drop=True)

    dup_body = work_df[
        work_df["Content Hash"].duplicated(keep=False)
        & work_df["Content Hash"].astype(str).str.strip().astype(bool)
    ][["URL", "Content Hash"]].drop_duplicates().reset_index(drop=True)

    missing_title = work_df[work_df["Title"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_desc = work_df[work_df["Description"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_h1 = work_df[work_df["H1"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_canonical = work_df[work_df["Canonical URL"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    title_too_short = check_C042(work_df)
    title_too_long = check_C043(work_df)
    desc_too_short = check_C046(work_df)
    desc_too_long = check_C047(work_df)
    multiple_h1 = check_C050(work_df)
    missing_lang = check_C059(work_df)
    h1_dup_title = check_C052(work_df)
    url_too_long = check_C062(work_df)
    url_uppercase = check_C065(work_df)
    url_underscores = check_C064(work_df)
    url_excessive_params = check_C061(work_df)
    low_text_ratio = check_C058(work_df)
    thin_content = work_df[work_df["Word Count"].astype(int) < 300][["URL"]].drop_duplicates().reset_index(drop=True)
    slow_pages = work_df[work_df["Crawl Time (s)"].astype(float) > 2.5][["URL"]].drop_duplicates().reset_index(drop=True)
    images_missing_dimensions = check_C123(work_df)
    excessive_dom_size = check_C127(work_df)
    legacy_image_formats = check_C124(work_df)
    non_https_pages = work_df[~work_df["URL"].astype(str).str.startswith("https://")][["URL"]].drop_duplicates().reset_index(drop=True)
    redirect_pages = work_df[work_df["Status"].astype(str).str.startswith(("301", "302", "303", "307", "308"))][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_schema = work_df[work_df["Schema"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_og = work_df[
        work_df["OG Title"].astype(str).str.strip().eq("")
        | work_df["OG Description"].astype(str).str.strip().eq("")
    ][["URL"]].drop_duplicates().reset_index(drop=True)
    pages_with_low_internal_links = work_df[work_df["Internal Links"].astype(int) <= 1][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_viewport = work_df[
        ~work_df["HTML"].fillna("").apply(_has_viewport_meta)
    ][["URL"]].drop_duplicates().reset_index(drop=True)
    pages_missing_alt = _missing_alt_image_pages(work_df.set_index("URL")["HTML"])
    missing_favicon = check_C116(work_df)
    missing_twitter_card = check_C113(work_df)
    invalid_structured_data = check_C109(work_df)

    internal_link_counts: Counter = Counter()
    for html in work_df.get("HTML", pd.Series([""] * len(work_df))).fillna(""):
        internal_link_counts.update(_extract_internal_targets(html))

    orphan_pages = work_df.loc[
        work_df["URL"].astype(str).isin(
            [url for url in work_df["URL"].astype(str) if url not in internal_link_counts]
        )
    ][["URL"]].drop_duplicates().reset_index(drop=True)

    _add_finding(
        findings,
        category=_catalog_reference("Orphan Pages")["category"],
        check="Orphan Pages",
        severity=_catalog_reference("Orphan Pages")["severity"],
        affected_pages=len(orphan_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Orphan Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Non-HTTPS Pages")["category"],
        check="Non-HTTPS Pages",
        severity=_catalog_reference("Non-HTTPS Pages")["severity"],
        affected_pages=len(non_https_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Non-HTTPS Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Redirecting Pages")["category"],
        check="Redirecting Pages",
        severity=_catalog_reference("Redirecting Pages")["severity"],
        affected_pages=len(redirect_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Redirecting Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Titles")["category"],
        check="Duplicate Titles",
        severity=_catalog_reference("Duplicate Titles")["severity"],
        affected_pages=len(dup_titles["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Titles")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Meta Descriptions")["category"],
        check="Duplicate Meta Descriptions",
        severity=_catalog_reference("Duplicate Meta Descriptions")["severity"],
        affected_pages=len(dup_desc["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Meta Descriptions")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate H1 Tags")["category"],
        check="Duplicate H1 Tags",
        severity=_catalog_reference("Duplicate H1 Tags")["severity"],
        affected_pages=len(dup_h1["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate H1 Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Body Content")["category"],
        check="Duplicate Body Content",
        severity=_catalog_reference("Duplicate Body Content")["severity"],
        affected_pages=len(dup_body["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Body Content")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Title")["category"],
        check="Missing Title",
        severity=_catalog_reference("Missing Title")["severity"],
        affected_pages=len(missing_title),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Title")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Description")["category"],
        check="Missing Description",
        severity=_catalog_reference("Missing Description")["severity"],
        affected_pages=len(missing_desc),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Description")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing H1")["category"],
        check="Missing H1",
        severity=_catalog_reference("Missing H1")["severity"],
        affected_pages=len(missing_h1),
        total_pages=total_pages,
        notes=_catalog_reference("Missing H1")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Canonical")["category"],
        check="Missing Canonical",
        severity=_catalog_reference("Missing Canonical")["severity"],
        affected_pages=len(missing_canonical),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Canonical")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Title Too Short")["category"],
        check="Title Too Short",
        severity=_catalog_reference("Title Too Short")["severity"],
        affected_pages=len(title_too_short),
        total_pages=total_pages,
        notes=_catalog_reference("Title Too Short")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Title Too Long")["category"],
        check="Title Too Long",
        severity=_catalog_reference("Title Too Long")["severity"],
        affected_pages=len(title_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("Title Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Description Too Short")["category"],
        check="Meta Description Too Short",
        severity=_catalog_reference("Meta Description Too Short")["severity"],
        affected_pages=len(desc_too_short),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Description Too Short")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Description Too Long")["category"],
        check="Meta Description Too Long",
        severity=_catalog_reference("Meta Description Too Long")["severity"],
        affected_pages=len(desc_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Description Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Multiple H1s")["category"],
        check="Multiple H1s",
        severity=_catalog_reference("Multiple H1s")["severity"],
        affected_pages=len(multiple_h1),
        total_pages=total_pages,
        notes=_catalog_reference("Multiple H1s")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Language Declaration")["category"],
        check="Missing Language Declaration",
        severity=_catalog_reference("Missing Language Declaration")["severity"],
        affected_pages=len(missing_lang),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Language Declaration")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("H1 Duplicates Title")["category"],
        check="H1 Duplicates Title",
        severity=_catalog_reference("H1 Duplicates Title")["severity"],
        affected_pages=len(h1_dup_title),
        total_pages=total_pages,
        notes=_catalog_reference("H1 Duplicates Title")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Too Long")["category"],
        check="URL Too Long",
        severity=_catalog_reference("URL Too Long")["severity"],
        affected_pages=len(url_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("URL Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Contains Uppercase")["category"],
        check="URL Contains Uppercase",
        severity=_catalog_reference("URL Contains Uppercase")["severity"],
        affected_pages=len(url_uppercase),
        total_pages=total_pages,
        notes=_catalog_reference("URL Contains Uppercase")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Contains Underscores")["category"],
        check="URL Contains Underscores",
        severity=_catalog_reference("URL Contains Underscores")["severity"],
        affected_pages=len(url_underscores),
        total_pages=total_pages,
        notes=_catalog_reference("URL Contains Underscores")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Excessive Parameters")["category"],
        check="URL Excessive Parameters",
        severity=_catalog_reference("URL Excessive Parameters")["severity"],
        affected_pages=len(url_excessive_params),
        total_pages=total_pages,
        notes=_catalog_reference("URL Excessive Parameters")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Low Text-to-HTML Ratio")["category"],
        check="Low Text-to-HTML Ratio",
        severity=_catalog_reference("Low Text-to-HTML Ratio")["severity"],
        affected_pages=len(low_text_ratio),
        total_pages=total_pages,
        notes=_catalog_reference("Low Text-to-HTML Ratio")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Thin Content")["category"],
        check="Thin Content",
        severity=_catalog_reference("Thin Content")["severity"],
        affected_pages=len(thin_content),
        total_pages=total_pages,
        notes=_catalog_reference("Thin Content")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Low Internal Link Support")["category"],
        check="Low Internal Link Support",
        severity=_catalog_reference("Low Internal Link Support")["severity"],
        affected_pages=len(pages_with_low_internal_links),
        total_pages=total_pages,
        notes=_catalog_reference("Low Internal Link Support")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Schema")["category"],
        check="Missing Schema",
        severity=_catalog_reference("Missing Schema")["severity"],
        affected_pages=len(missing_schema),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Schema")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Open Graph Tags")["category"],
        check="Missing Open Graph Tags",
        severity=_catalog_reference("Missing Open Graph Tags")["severity"],
        affected_pages=len(missing_og),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Open Graph Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Favicon Link")["category"],
        check="Missing Favicon Link",
        severity=_catalog_reference("Missing Favicon Link")["severity"],
        affected_pages=len(missing_favicon),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Favicon Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Twitter Card Tags")["category"],
        check="Missing Twitter Card Tags",
        severity=_catalog_reference("Missing Twitter Card Tags")["severity"],
        affected_pages=len(missing_twitter_card),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Twitter Card Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Invalid Structured Data")["category"],
        check="Invalid Structured Data",
        severity=_catalog_reference("Invalid Structured Data")["severity"],
        affected_pages=len(invalid_structured_data),
        total_pages=total_pages,
        notes=_catalog_reference("Invalid Structured Data")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Slow Response Time")["category"],
        check="Slow Response Time",
        severity=_catalog_reference("Slow Response Time")["severity"],
        affected_pages=len(slow_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Slow Response Time")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Images Missing Dimensions")["category"],
        check="Images Missing Dimensions",
        severity=_catalog_reference("Images Missing Dimensions")["severity"],
        affected_pages=len(images_missing_dimensions),
        total_pages=total_pages,
        notes=_catalog_reference("Images Missing Dimensions")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive DOM Size")["category"],
        check="Excessive DOM Size",
        severity=_catalog_reference("Excessive DOM Size")["severity"],
        affected_pages=len(excessive_dom_size),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive DOM Size")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Legacy Image Formats")["category"],
        check="Legacy Image Formats",
        severity=_catalog_reference("Legacy Image Formats")["severity"],
        affected_pages=len(legacy_image_formats),
        total_pages=total_pages,
        notes=_catalog_reference("Legacy Image Formats")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Viewport Meta")["category"],
        check="Missing Viewport Meta",
        severity=_catalog_reference("Missing Viewport Meta")["severity"],
        affected_pages=len(missing_viewport),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Viewport Meta")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Images Missing Alt Text")["category"],
        check="Images Missing Alt Text",
        severity=_catalog_reference("Images Missing Alt Text")["severity"],
        affected_pages=len(pages_missing_alt),
        total_pages=total_pages,
        notes=_catalog_reference("Images Missing Alt Text")["notes"],
    )

    checks_df = pd.DataFrame(findings)
    if checks_df.empty:
        checks_df = pd.DataFrame(columns=["Category", "Check", "Severity", "Affected Pages", "Deduction", "Impact Score", "Notes"])

    category_scores = []
    for category, weight in CATEGORY_WEIGHTS.items():
        category_checks = checks_df[checks_df["Category"] == category]
        if category_checks.empty:
            score = 100
        else:
            average_deduction = category_checks["Deduction"].mean()
            score = int(max(0, min(100, round(100 - (average_deduction * 100), 1))))
        category_scores.append({"Category": category, "Weight": weight, "Score": score, "Label": CATEGORY_LABELS[category]})

    category_scores_df = pd.DataFrame(category_scores)
    weighted_total = sum((row["Score"] * row["Weight"]) for _, row in category_scores_df.iterrows())
    health_score = int(round(weighted_total / sum(CATEGORY_WEIGHTS.values())))
    grade = _grade_for_score(health_score)

    quick_wins = checks_df.sort_values(["Impact Score", "Affected Pages"], ascending=False).reset_index(drop=True)
    quick_wins = quick_wins[["Check", "Impact Score", "Affected Pages", "Category"]].rename(
        columns={"Check": "Issue", "Impact Score": "Impact", "Affected Pages": "Affected Pages", "Category": "Category"}
    )
    quick_wins.insert(len(quick_wins.columns), "Priority", range(1, len(quick_wins) + 1))

    if quick_wins.empty:
        quick_wins = pd.DataFrame(columns=["Issue", "Impact", "Affected Pages", "Category", "Priority"])

    findings_count = len(checks_df)

    return {
        "health_score": health_score,
        "grade": grade,
        "pages_crawled": total_pages,
        "issues_found": findings_count,
        "checks": checks_df,
        "quick_wins": quick_wins,
        "category_scores": category_scores_df,
        "duplicate_titles": dup_titles,
        "duplicate_descriptions": dup_desc,
        "duplicate_h1": dup_h1,
        "duplicate_body_content": dup_body,
        "orphan_pages": orphan_pages,
    }


def render_streamlit_health_score_ui(st, df: pd.DataFrame):
    st.subheader("🩺 Site Health")
    st.markdown("WEM-style site health scoring built from category deductions, quick wins, and site-wide crawl patterns.")

    report = build_site_health_report(df)
    health_score = report["health_score"]

    score_col, grade_col, pages_col, issues_col = st.columns(4)
    with score_col:
        st.metric("Health Score", health_score)
    with grade_col:
        st.metric("Grade", report["grade"])
    with pages_col:
        st.metric("Pages Crawled", report["pages_crawled"])
    with issues_col:
        st.metric("Issues Found", report["issues_found"])

    st.progress(min(1.0, max(0.0, health_score / 100)))

    st.markdown("---")
    health_tab1, health_tab2, health_tab3 = st.tabs(["Health Score", "Quick Wins", "Category Breakdown"])

    with health_tab1:
        st.markdown(
            f"The current site health score is {health_score}/100, which maps to a grade of **{report['grade']}**."
        )
        st.caption(
            "This score is derived from the WEM-style weighted model: category-level penalties are averaged and then combined into one overall health score."
        )
        st.dataframe(report["category_scores"], use_container_width=True)

    with health_tab2:
        if report["quick_wins"].empty:
            st.success("No quick wins detected in this crawl pass.")
        else:
            st.dataframe(report["quick_wins"], use_container_width=True)

    with health_tab3:
        st.dataframe(report["checks"], use_container_width=True)
