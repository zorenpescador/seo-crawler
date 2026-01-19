from typing import List, Dict, Any
from bs4 import BeautifulSoup
import pandas as pd
import re

# sklearn import wrapped for graceful error if not installed
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception as e:
    TfidfVectorizer = None  # will raise helpful error later


# ---------- Extraction helpers ----------
def extract_text_from_html(html: str) -> Dict[str, str]:
    """
    Extracts key text fields from an HTML string:
      - title, meta_description, h1, body_text
    Returns a dict of strings (empty when nothing found).
    """
    result = {"title": "", "meta_description": "", "h1": "", "body_text": ""}
    if not html:
        return result

    soup = BeautifulSoup(html, "html.parser")

    # title
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""

    # meta description
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    if meta and meta.get("content"):
        result["meta_description"] = meta["content"].strip()
    else:
        # try og:description fallback
        og = soup.find("meta", attrs={"property": lambda v: v and v.lower() == "og:description"})
        if og and og.get("content"):
            result["meta_description"] = og["content"].strip()

    # first h1
    h1 = soup.find("h1")
    result["h1"] = h1.get_text(strip=True) if h1 else ""

    # body text (safe, collapse whitespace)
    for script in soup(["script", "style", "noscript"]):
        script.extract()
    body = soup.get_text(separator=" ", strip=True)
    body = re.sub(r"\s+", " ", body)
    result["body_text"] = body

    return result


# ---------- Keyword candidate extraction ----------
def _ensure_vectorizer_available():
    if TfidfVectorizer is None:
        raise RuntimeError(
            "scikit-learn is required for organic research. Install with: pip install scikit-learn"
        )


def build_document_corpus(df: pd.DataFrame, html_col: str = "HTML") -> pd.DataFrame:
    """
    Given a DataFrame with an HTML column, returns a new DataFrame
    with columns: title, meta_description, h1, body_text, doc_text (concatenated).
    Leaves original index intact.
    """
    data = []
    for html in df[html_col].fillna("").astype(str):
        extracted = extract_text_from_html(html)
        # Prefer title + meta + h1 + body concatenated
        doc = " ".join(
            [
                extracted.get("title", ""),
                extracted.get("meta_description", ""),
                extracted.get("h1", ""),
                extracted.get("body_text", ""),
            ]
        ).strip()
        data.append({**extracted, "doc_text": doc})
    return pd.DataFrame(data, index=df.index)


def compute_tfidf_keywords(
    docs: List[str],
    top_n: int = 10,
    ngram_range=(1, 2),
    max_features: int = 10000,
    stop_words: str = "english",
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Compute TF-IDF on a list of documents and return top_n terms for each doc.
    Returns a dict mapping doc index -> list of {"term": str, "score": float}
    """
    _ensure_vectorizer_available()
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range, max_features=max_features, stop_words=stop_words, token_pattern=r"(?u)\b\w[\w\-]+\b"
    )
    X = vectorizer.fit_transform(docs)
    feature_names = vectorizer.get_feature_names_out()

    results = {}
    for i in range(X.shape[0]):
        row = X.getrow(i)
        if row.nnz == 0:
            results[i] = []
            continue
        # get (feature_index, score) pairs
        coo = row.tocoo()
        pairs = sorted(zip(coo.col, coo.data), key=lambda x: -x[1])[:top_n]
        results[i] = [{"term": feature_names[idx], "score": float(score)} for idx, score in pairs]
    return results


# ---------- Intent heuristics ----------
def guess_search_intent_for_term(term: str) -> str:
    """
    Basic heuristic to guess intent:
      - transactional: contains buy, price, coupon, discount, order, shop
      - navigational: brand or site navigational words (contains 'login', 'facebook', 'twitter', domain-like)
      - informational: question words or long-tail how/what/why/guide/tutorial/learn
    """
    t = term.lower()
    transactional_keywords = {"buy", "price", "coupon", "discount", "order", "shop", "compare", "sale"}
    navigational_keywords = {"login", "signin", "signup", "facebook", "twitter", "instagram", "youtube"}
    info_triggers = {"how", "what", "why", "guide", "tutorial", "best", "tips", "how to"}

    if any(k in t for k in transactional_keywords):
        return "transactional"
    if any(k in t for k in navigational_keywords):
        return "navigational"
    if any(k in t for k in info_triggers) or t.endswith("?") or "?" in t:
        return "informational"
    return "unknown"


# ---------- High-level integration function ----------
def analyze_organic_candidates(
    df: pd.DataFrame,
    html_col: str = "HTML",
    top_n_per_doc: int = 10,
    ngram_range=(1, 2),
) -> pd.DataFrame:
    """
    Run the full on-page/corpus analysis and return a DataFrame with:
      - title, meta_description, h1, doc_text
      - keywords (list of dicts with term/score)
      - top_terms (comma-separated top terms)
      - top_term_intent (most common guessed intent among top terms)
    The returned DataFrame preserves the original index.
    """
    if html_col not in df.columns:
        raise KeyError(f"Column '{html_col}' not found in DataFrame")

    corpus_df = build_document_corpus(df, html_col=html_col)
    docs = corpus_df["doc_text"].fillna("").astype(str).tolist()

    tfidf_results = compute_tfidf_keywords(docs, top_n=top_n_per_doc, ngram_range=ngram_range)

    top_terms = []
    term_lists = []
    intents = []
    for i, row in corpus_df.iterrows():
        terms = tfidf_results.get(i, [])
        term_lists.append(terms)
        terms_only = [t["term"] for t in terms]
        top_terms.append(", ".join(terms_only[:top_n_per_doc]) if terms_only else "")
        # guess intents and pick the most frequent (or unknown)
        intent_counts = {}
        for t in terms_only:
            intent = guess_search_intent_for_term(t)
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        top_intent = max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else "unknown"
        intents.append(top_intent)

    out = corpus_df.copy()
    out["keywords"] = term_lists
    out["top_terms"] = top_terms
    out["top_term_intent"] = intents
    return out


# ---------- Streamlit UI helper ----------
def render_streamlit_organic_ui(st, df: pd.DataFrame, html_col: str = "HTML"):
    """
    Renders a compact Streamlit UI for organic research:
      - compute analysis (cached) and show per-URL top terms
      - show global top keywords across corpus
      - allow export of suggestions as CSV
    Use inside your Streamlit app where `st` is streamlit and `df` is current filtered DataFrame.
    """
    import pandas as _pd

    st.subheader("🧭 Organic Research (On-page candidates)")
    if html_col not in df.columns:
        st.info(f"Column '{html_col}' not found in dataframe. Set html_col to column with HTML.")
        return

    # cache the heavy compute
    @st.cache_data
    def _run_analysis(df_serialized):
        # df_serialized is a tuple (index_list, html_list, url_list) to avoid pickling large DataFrames
        idxs, htmls, urls = df_serialized
        tmp_df = _pd.DataFrame({"URL": urls, html_col: htmls}, index=idxs)
        return analyze_organic_candidates(tmp_df, html_col=html_col, top_n_per_doc=10)

    serialized = (list(df.index), list(df[html_col].fillna("").astype(str)), list(df.get("URL", [""] * len(df))))
    analyzed = _run_analysis(serialized)

    # let user pick a URL to inspect
    st.markdown("**Inspect pages**")
    url_map = analyzed["URL"].fillna("").tolist()
    chosen = st.selectbox("Choose a URL to inspect", options=["(none)"] + url_map)
    if chosen and chosen != "(none)":
        row = analyzed[analyzed["URL"] == chosen].iloc[0]
        st.markdown("**Top suggested keywords (TF-IDF)**")
        if row["keywords"]:
            kw_table = _pd.DataFrame(row["keywords"])
            st.dataframe(kw_table, use_container_width=True)
        else:
            st.info("No candidate keywords found for this page.")
        st.markdown("**Page excerpts**")
        st.write("Title:", row.get("title", ""))
        st.write("Meta description:", row.get("meta_description", ""))
        st.write("H1:", row.get("h1", ""))

    # show global top keywords across corpus
    st.markdown("**Global top keywords across filtered pages**")
    # flatten all keywords and aggregate scores
    agg = {}
    for kws in analyzed["keywords"]:
        for k in kws:
            agg[k["term"]] = agg.get(k["term"], 0.0) + k["score"]
    if agg:
        agg_df = _pd.DataFrame(
            sorted(agg.items(), key=lambda x: -x[1]), columns=["term", "aggregate_score"]
        ).head(50)
        st.dataframe(agg_df, use_container_width=True)
    else:
        st.info("No keywords found in the current corpus.")

    # CSV export
    st.markdown("**Export suggestions**")
    if not analyzed.empty:
        export_df = analyzed[["top_terms", "top_term_intent"]].copy()
        export_df["URL"] = analyzed.get("URL", "")
        csv = export_df.to_csv(index=False)
        st.download_button("Download CSV (top_terms)", data=csv, file_name="organic_suggestions.csv", mime="text/csv")
    else:
        st.info("No analysis to export.")
