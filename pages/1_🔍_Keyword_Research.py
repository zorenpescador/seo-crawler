"""
Keyword Research Page
Dedicated page for comprehensive keyword analysis and research.
"""

import streamlit as st
import keyword_research as kr
import pandas as pd

# Configure page
st.set_page_config(page_title="Keyword Research", layout="wide")

st.title("🔍 Keyword Research Tool")
st.markdown("**Comprehensive keyword analysis and optimization opportunities** - Discover high-value keywords with TF-IDF and advanced keyword research.", unsafe_allow_html=True)

# Check if crawl results exist in session state
if "crawl_results" not in st.session_state or st.session_state.crawl_results is None:
    st.warning("⚠️ No crawl results available. Please run a crawl first on the **Crawl Results** page.")
    st.info("💡 Steps: 1) Go to Crawl Results page 2) Enter URL and click 'Start Crawl' 3) Return here to analyze keywords")
else:
    df_filtered = st.session_state.crawl_results.copy()
    
    # Extract keywords from all pages
    all_keywords = []
    for html in df_filtered["HTML"].fillna("").astype(str):
        page_keywords = kr.extract_keywords_from_text(html)
        all_keywords.extend(page_keywords)
    
    if all_keywords:
        st.markdown("---")
        kr.render_streamlit_keyword_research_ui(st, all_keywords)
    else:
        st.error("❌ No keywords could be extracted from the crawl results.")
        st.info("This might happen if the crawled pages have minimal text content.")
