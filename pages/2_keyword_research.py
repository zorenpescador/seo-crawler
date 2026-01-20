"""
Keyword Research Page
"""

import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

# Import keyword research module
try:
    import keyword_research as kr
except ImportError:
    try:
        # Try alternate import path
        from .. import keyword_research as kr
    except:
        st.error("❌ Could not load keyword research module")
        st.stop()

st.title("🔍 Keyword Research Tool")
st.markdown("Discover high-value keywords from your content with comprehensive analysis.")

st.markdown("---")

# Input methods
st.markdown("## 📝 Content Input")
input_method = st.radio(
    "Select input method:",
    options=["Paste Content", "Use Crawl Results", "Upload File"],
    horizontal=True
)

all_keywords = []

if input_method == "Paste Content":
    st.subheader("Paste Text or HTML Content")
    content = st.text_area("Enter your content:", height=200)
    
    if content.strip():
        try:
            soup = BeautifulSoup(content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
        except:
            text = content
        
        all_keywords = kr.extract_keywords_from_text(text)
        if all_keywords:
            st.success(f"✅ Extracted {len(all_keywords)} keywords")

elif input_method == "Use Crawl Results":
    if "crawl_results" in st.session_state and st.session_state.crawl_results is not None:
        df = st.session_state.crawl_results
        st.success(f"✅ Using {len(df)} pages from crawl")
        
        for html in df["HTML"].fillna(""):
            keywords = kr.extract_keywords_from_text(str(html))
            all_keywords.extend(keywords)
    else:
        st.info("Run a crawl first on the main page")

elif input_method == "Upload File":
    file = st.file_uploader("Upload text file", type=["txt", "csv", "md"])
    if file:
        try:
            content = file.read().decode("utf-8")
            all_keywords = kr.extract_keywords_from_text(content)
            st.success(f"✅ Extracted {len(all_keywords)} keywords")
        except Exception as e:
            st.error(f"Error: {e}")

# Show research if keywords available
if all_keywords:
    st.markdown("---")
    kr.render_streamlit_keyword_research_ui(st, all_keywords)
else:
    if input_method == "Paste Content":
        st.info("💡 Paste content above to begin analysis")
