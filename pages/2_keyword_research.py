"""
Keyword Research Page
Dedicated page for comprehensive keyword analysis and research.
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import keyword_research as kr
except ImportError as e:
    st.error(f"❌ Error importing keyword_research module: {e}")
    st.stop()

import pandas as pd
from bs4 import BeautifulSoup

# Configure page
st.set_page_config(page_title="Keyword Research", layout="wide")

st.title("🔍 Keyword Research Tool")
st.markdown("**Comprehensive keyword analysis and optimization opportunities** - Discover high-value keywords from your content.", unsafe_allow_html=True)

# Input methods
st.markdown("## 📝 Content Input")
st.markdown("Choose how you'd like to analyze keywords:")

input_method = st.radio(
    "Select input method:",
    options=["Paste Content", "Use Crawl Results", "Upload Text File"],
    horizontal=True,
    key="keyword_input_method"
)

all_keywords = []

if input_method == "Paste Content":
    st.markdown("### Paste Text or HTML Content")
    content_input = st.text_area(
        "Paste your content here (text or HTML):",
        height=200,
        placeholder="Enter text, HTML content, or multiple paragraphs...",
        help="You can paste plain text or HTML code"
    )
    
    if content_input.strip():
        # Extract text from HTML if needed
        try:
            soup = BeautifulSoup(content_input, "html.parser")
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
        except Exception as e:
            st.warning(f"Could not parse as HTML, treating as plain text: {e}")
            text_content = content_input
        
        try:
            all_keywords = kr.extract_keywords_from_text(text_content)
            
            if all_keywords:
                st.success(f"✅ Extracted {len(all_keywords)} keywords")
            else:
                st.warning("⚠️ No keywords could be extracted from the content")
        except Exception as e:
            st.error(f"❌ Error extracting keywords: {e}")
            all_keywords = []

elif input_method == "Use Crawl Results":
    if "crawl_results" not in st.session_state or st.session_state.crawl_results is None:
        st.info("📌 No crawl results available yet.")
        st.markdown("**To use crawl results:**")
        st.markdown("1. Go to **Crawl Results** page")
        st.markdown("2. Enter your URL and click 'Start Crawl'")
        st.markdown("3. Return here and select 'Use Crawl Results'")
    else:
        df_filtered = st.session_state.crawl_results.copy()
        
        st.success(f"✅ Using crawl results from {len(df_filtered)} pages")
        
        # Option to filter by content type
        content_types = df_filtered["Content Type"].unique()
        selected_types = st.multiselect(
            "Filter by content type:",
            options=sorted(content_types),
            default=sorted(content_types),
            key="keyword_content_filter"
        )
        
        df_filtered = df_filtered[df_filtered["Content Type"].isin(selected_types)]
        
        # Extract keywords from all pages
        for html in df_filtered["HTML"].fillna("").astype(str):
            page_keywords = kr.extract_keywords_from_text(html)
            all_keywords.extend(page_keywords)
        
        if all_keywords:
            st.success(f"✅ Extracted {len(all_keywords)} keywords from {len(df_filtered)} pages")
        else:
            st.warning("⚠️ No keywords could be extracted from the crawl results")

elif input_method == "Upload Text File":
    st.markdown("### Upload a Text File")
    uploaded_file = st.file_uploader(
        "Choose a text file (.txt, .csv, .md):",
        type=["txt", "csv", "md"],
        help="Upload a text file containing content to analyze"
    )
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode("utf-8")
            all_keywords = kr.extract_keywords_from_text(content)
            
            if all_keywords:
                st.success(f"✅ Extracted {len(all_keywords)} keywords from file '{uploaded_file.name}'")
            else:
                st.warning("⚠️ No keywords could be extracted from the file")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# Display keyword research if keywords are available
if all_keywords:
    st.markdown("---")
    kr.render_streamlit_keyword_research_ui(st, all_keywords)
else:
    if input_method == "Paste Content":
        st.info("💡 Paste content above to analyze keywords")
    elif input_method == "Upload Text File":
        st.info("💡 Upload a text file to analyze keywords")
