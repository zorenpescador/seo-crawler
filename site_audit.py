import hashlib
import re
from collections import Counter
from typing import Any, Dict, List

import pandas as pd
from bs4 import BeautifulSoup


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


def build_site_audit_report(df: pd.DataFrame) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            "site_health_score": 100,
            "issues": [],
            "duplicate_titles": pd.DataFrame(columns=["URL", "Title"]),
            "duplicate_descriptions": pd.DataFrame(columns=["URL", "Description"]),
            "duplicate_h1": pd.DataFrame(columns=["URL", "H1"]),
            "duplicate_body_content": pd.DataFrame(columns=["URL", "Content Hash"]),
            "orphan_pages": pd.DataFrame(columns=["URL"]),
            "quick_wins": pd.DataFrame(columns=["Issue", "Impact", "Affected Pages"]),
        }

    work_df = df.copy()
    work_df["Content Text"] = work_df.get("Content Text", work_df.get("HTML", "")).fillna("")
    work_df["Body Text"] = work_df["Content Text"].apply(_html_to_text)
    work_df["Content Hash"] = work_df["Body Text"].apply(_content_hash)

    dup_titles = work_df[
        work_df.duplicated(subset=["Title"], keep=False) & work_df["Title"].astype(str).str.strip().astype(bool)
    ][["URL", "Title"]].drop_duplicates().reset_index(drop=True)
    dup_desc = work_df[
        work_df.duplicated(subset=["Description"], keep=False) & work_df["Description"].astype(str).str.strip().astype(bool)
    ][["URL", "Description"]].drop_duplicates().reset_index(drop=True)
    dup_h1 = work_df[
        work_df.duplicated(subset=["H1"], keep=False) & work_df["H1"].astype(str).str.strip().astype(bool)
    ][["URL", "H1"]].drop_duplicates().reset_index(drop=True)

    dup_body = work_df[work_df["Content Hash"].duplicated(keep=False) & work_df["Content Hash"].astype(str).str.strip().astype(bool)]
    dup_body = dup_body[["URL", "Content Hash"]].drop_duplicates().reset_index(drop=True)

    internal_link_counts: Counter = Counter()
    for html in work_df.get("HTML", pd.Series([""] * len(work_df))).fillna(""):
        internal_link_counts.update(_extract_internal_targets(html))

    orphan_pages = work_df.loc[
        work_df["URL"].isin(
            [url for url in work_df["URL"].astype(str) if url not in internal_link_counts]
        )
    ][["URL"]].drop_duplicates().reset_index(drop=True)

    issue_rows = []
    if not dup_titles.empty:
        issue_rows.append({"Issue": "Duplicate Titles", "Impact": len(dup_titles), "Affected Pages": len(dup_titles["URL"].unique())})
    if not dup_desc.empty:
        issue_rows.append({"Issue": "Duplicate Meta Descriptions", "Impact": len(dup_desc), "Affected Pages": len(dup_desc["URL"].unique())})
    if not dup_h1.empty:
        issue_rows.append({"Issue": "Duplicate H1 Tags", "Impact": len(dup_h1), "Affected Pages": len(dup_h1["URL"].unique())})
    if not dup_body.empty:
        issue_rows.append({"Issue": "Duplicate Body Content", "Impact": len(dup_body), "Affected Pages": len(dup_body["URL"].unique())})
    if not orphan_pages.empty:
        issue_rows.append({"Issue": "Orphan Pages", "Impact": len(orphan_pages), "Affected Pages": len(orphan_pages["URL"].unique())})

    quick_wins = pd.DataFrame(issue_rows, columns=["Issue", "Impact", "Affected Pages"])
    if quick_wins.empty:
        quick_wins = pd.DataFrame(columns=["Issue", "Impact", "Affected Pages"])

    total_issues = float(max(1, len(issue_rows)))
    severity_score = min(100, round(100 - (sum(row["Impact"] for row in issue_rows) / total_issues), 1))

    return {
        "site_health_score": int(max(0, min(100, severity_score))),
        "issues": issue_rows,
        "duplicate_titles": dup_titles,
        "duplicate_descriptions": dup_desc,
        "duplicate_h1": dup_h1,
        "duplicate_body_content": dup_body,
        "orphan_pages": orphan_pages,
        "quick_wins": quick_wins,
    }


def render_streamlit_site_audit_ui(st, df: pd.DataFrame):
    st.subheader("🧭 Site Audit")
    st.markdown("Site-wide health signals based on duplicate content, orphan pages, and crawl structure heuristics.")

    audit = build_site_audit_report(df)
    st.metric("Site Health Score", audit["site_health_score"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Duplicate Titles", len(audit["duplicate_titles"]))
    with col2:
        st.metric("Duplicate Descriptions", len(audit["duplicate_descriptions"]))
    with col3:
        st.metric("Duplicate Body Content", len(audit["duplicate_body_content"]))

    st.markdown("---")
    st.markdown("**Quick Wins**")
    if audit["quick_wins"].empty:
        st.success("No major site-wide issues detected in this pass.")
    else:
        st.dataframe(audit["quick_wins"], width="stretch")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Duplicate Titles", "Duplicate Descriptions", "Orphan Pages"])
    with tab1:
        st.dataframe(audit["duplicate_titles"], width="stretch")
    with tab2:
        st.dataframe(audit["duplicate_descriptions"], width="stretch")
    with tab3:
        st.dataframe(audit["orphan_pages"], width="stretch")
