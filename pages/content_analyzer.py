import streamlit as st
from content_analyzer import render_streamlit_content_analyzer_ui

st.set_page_config(page_title="Content Analyzer", layout="wide")
st.title("🧠 Content Analyzer")

content_input = st.text_area(
    "Paste content to analyze",
    height=220,
    placeholder="Paste article text, landing page copy, or any content here...",
)
source_name = st.text_input("Source label", value="Content")

if st.button("Analyze content", use_container_width=True):
    render_streamlit_content_analyzer_ui(st, content_input, source_name=source_name)
else:
    render_streamlit_content_analyzer_ui(st, content_input, source_name=source_name)
