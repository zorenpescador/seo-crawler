# seo_crawler_streamlit.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
import json
import re
import time
import io
import organic_research as org
import keyword_research as kr

# ---------------------------
# Helper utilities
# ---------------------------
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEO-Crawler/1.0; +https://example.com)"}

def load_robots_for_domain(domain):
    rp = RobotFileParser()
    robots_url = f"{domain.rstrip('/')}/robots.txt"
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        rp = None
    return rp, robots_url

def allowed_by_robots(url, ignore_robots=False):
    if ignore_robots:
        return True, None
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    rp, robots_url = load_robots_for_domain(domain)
    if rp is None:
        return True, robots_url
    try:
        allowed = rp.can_fetch("*", url)
        return allowed, robots_url
    except Exception:
        return True, robots_url

def extract_schema_types(soup):
    schema_types = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            raw = tag.string
            if not raw:
                continue
            data = json.loads(raw)
            if isinstance(data, dict):
                t = data.get("@type") or data.get("type")
                if isinstance(t, list):
                    schema_types.extend(t)
                elif t:
                    schema_types.append(t)
            elif isinstance(data, list):
                for d in data:
                    if isinstance(d, dict):
                        t = d.get("@type") or d.get("type")
                        if t:
                            schema_types.append(t)
        except Exception:
            continue
    return ", ".join(schema_types)

def detect_content_type(url, soup):
    u = url.lower()
    if re.search(r"/blog/|/news/|/posts/|/articles/", u) or soup.find("article"):
        return "Blog / Article"
    if re.search(r"/product/|/shop/|/item/|/store/|/collections/", u):
        return "Product"
    if re.search(r"/about|/contact|/service|/services|/pricing|/features", u):
        return "Landing Page"
    if soup.find("meta", attrs={"property":"og:type"}) and soup.find("meta", attrs={"property":"og:type"})["content"] == "product":
        return "Product"
    return "Other"

def normalize_url(u):
    if not u:
        return u
    u = u.split('#')[0].strip()
    return u

# ---------------------------
# Core crawler
# ---------------------------
def crawl_site(seed_url, max_pages=100, delay=0.5, ignore_robots=False, show_progress_cb=None):
    seed_url = seed_url.rstrip('/')
    parsed_seed = urlparse(seed_url)
    seed_domain = parsed_seed.netloc
    scheme = parsed_seed.scheme or "https"
    base = f"{scheme}://{seed_domain}"

    visited = set()
    to_visit = [seed_url]
    results = []

    session = requests.Session()
    session.headers.update(HEADERS)

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        url = normalize_url(url)
        if not url or url in visited:
            continue

        allowed, robots_url = allowed_by_robots(url, ignore_robots=ignore_robots)
        if not allowed:
            return pd.DataFrame(), {"blocked": True, "robots_url": robots_url}

        if show_progress_cb:
            show_progress_cb(min(len(visited)/max_pages, 1.0), f"Crawling: {url}")

        try:
            start_time = time.time()
            r = session.get(url, timeout=12)
            crawl_time = round(time.time() - start_time, 2)  # seconds
            status_code = r.status_code

            if status_code >= 400:
                results.append({
                    "URL": url, "Status": status_code, "Crawl Status": "HTTP Error",
                    "Title": "", "Title Length": 0, "Description": "", "Description Length": 0,
                    "H1": "", "H Tags": "", "Word Count": 0,
                    "Internal Links": 0, "External Links": 0, "Link-to-Word Ratio": 0,
                    "Schema": "", "Content Type": "", "MIME Type": r.headers.get("Content-Type", ""),
                    "Crawl Time (s)": crawl_time
                })
                visited.add(url)
                time.sleep(delay)
                continue

            soup = BeautifulSoup(r.text, "lxml")
            title = (soup.title.string.strip() if soup.title and soup.title.string else "")
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

            h_tags = {f"h{i}": [h.get_text(" ", strip=True) for h in soup.find_all(f"h{i}")] for i in range(1,7)}
            h1 = h_tags["h1"][0] if h_tags["h1"] else ""

            anchors = []
            internal_links, external_links = [], []
            for a in soup.find_all("a", href=True):
                href = normalize_url(urljoin(url, a.get("href")))
                if not href:
                    continue
                anchors.append({"href": href, "text": a.get_text(" ", strip=True)})
                parsed = urlparse(href)
                if parsed.netloc == seed_domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)

            text = soup.get_text(" ", strip=True)
            word_count = len(text.split())
            total_links = len(internal_links) + len(external_links)
            link_to_word = round(total_links / word_count, 3) if word_count else 0

            schema = extract_schema_types(soup)
            content_type = detect_content_type(url, soup)
            mime_type = r.headers.get("Content-Type", "")

            results.append({
                "URL": url, "Status": status_code, "Crawl Status": "Success",
                "Title": title, "Title Length": len(title),
                "Description": desc, "Description Length": len(desc),
                "H1": h1, "H Tags": json.dumps(h_tags, ensure_ascii=False),
                "Word Count": word_count, "Internal Links": len(set(internal_links)),
                "External Links": len(set(external_links)), "Link-to-Word Ratio": link_to_word,
                "Schema": schema, "Content Type": content_type, "MIME Type": mime_type,
                "Crawl Time (s)": crawl_time, "HTML": r.text
            })

            for link in internal_links:
                if link not in visited and link not in to_visit:
                    p = urlparse(link)
                    if p.scheme in ("http", "https"):
                        to_visit.append(link)

            visited.add(url)
            time.sleep(delay)

        except Exception as e:
            results.append({
                "URL": url, "Status": "Error", "Crawl Status": f"Error: {e}",
                "Title": "", "Title Length": 0, "Description": "", "Description Length": 0,
                "H1": "", "H Tags": "", "Word Count": 0, "Internal Links": 0, "External Links": 0,
                "Link-to-Word Ratio": 0, "Schema": "", "Content Type": "", "MIME Type": "",
                "Crawl Time (s)": 0
            })
            visited.add(url)
            time.sleep(delay)
            continue

    return pd.DataFrame(results), {"blocked": False}

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Advanced SEO Site Crawler", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main heading styling */
    h1 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f77b4;
    }
    
    h2 {
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #34495e;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        height: 2.5rem;
        font-size: 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #1f77b4 0%, #1a5fa0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1a5fa0 0%, #14468a 100%);
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3);
        transform: translateY(-2px);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSlider > div > div {
        border-radius: 6px;
        border: 2px solid #e0e0e0;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border: 2px solid #1f77b4;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
    }
    
    /* Info/warning/error box styling */
    .stAlert {
        border-radius: 8px;
        padding: 1.25rem;
        border-left: 5px solid;
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1f77b4, #4da6ff);
    }
    
    /* Metric boxes */
    [data-testid="stMetric"] {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #d4e9ff;
    }
    
    /* General spacing improvement */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    /* Better separation between sections */
    hr {
        margin: 2rem 0;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔎 Advanced SEO Site Crawler")
st.markdown("**Comprehensive SEO analysis and site crawling tool** - Analyze your website's structure, content, and optimization metrics.", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Crawl Settings")
    st.markdown("---")
    
    seed_url = st.text_input(
        "Enter site URL",
        value="https://example.com",
        placeholder="https://example.com",
        help="Include the protocol (http:// or https://)"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input(
            "Max pages",
            min_value=1,
            max_value=2000,
            value=200,
            step=10,
            help="Maximum number of pages to crawl"
        )
    with col2:
        delay = st.slider(
            "Request delay",
            0.0,
            5.0,
            0.5,
            0.1,
            help="Delay between requests in seconds (be respectful)"
        )
    
    ignore_robots = st.checkbox(
        "Ignore robots.txt",
        value=False,
        help="⚠️ Testing only - respects site's crawling rules by default"
    )
    
    st.markdown("---")
    run_button = st.button("🚀 Start Crawl", key="start", use_container_width=True)

status_area = st.empty()
progress_bar = st.progress(0.0)
status_text = st.empty()

# Initialize session state for crawl results
if "crawl_results" not in st.session_state:
    st.session_state.crawl_results = None
if "crawl_metadata" not in st.session_state:
    st.session_state.crawl_metadata = None

if run_button:
    if not seed_url.startswith("http"):
        st.error("❌ Please provide a valid URL starting with http:// or https://")
    else:
        def show_progress(pct, message):
            try:
                progress_bar.progress(min(max(pct, 0.0), 1.0))
            except Exception:
                pass
            status_text.markdown(f"⏳ **{message}**")

        status_area.info("🔍 Preparing to crawl...")
        df, meta = crawl_site(seed_url, max_pages=max_pages, delay=delay, ignore_robots=ignore_robots, show_progress_cb=show_progress)
        
        # Store results in session state for persistence across reruns
        st.session_state.crawl_results = df
        st.session_state.crawl_metadata = meta
        st.rerun()

# Display results from session state if available
if st.session_state.crawl_results is not None:
    df = st.session_state.crawl_results
    meta = st.session_state.crawl_metadata

    if meta.get("blocked"):
        st.error(f"🚫 Crawling blocked by robots.txt: {meta.get('robots_url')}")
        st.warning("💡 You may toggle 'Ignore robots.txt' to override (use responsibly).")
    elif df is None or df.empty:
        st.warning("⚠️ No pages were crawled. Please check your URL and try again.")
    else:
        progress_bar.progress(1.0)
        status_text.empty()
        
        # Success message with stats
        with st.container():
            st.success(f"✅ Crawl completed successfully")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pages Crawled", len(df), "")
            with col2:
                successful = len(df[df["Crawl Status"] == "Success"])
                st.metric("Successful", successful, f"{int(successful/len(df)*100)}%")
            with col3:
                errors = len(df[df["Crawl Status"] != "Success"])
                st.metric("Errors/Blocked", errors, "")
        
        st.markdown("---")

        df_display = df.copy()
        cols_order = ["URL", "Status", "Crawl Status", "Title", "Title Length",
                      "Description", "Description Length", "H1", "Word Count",
                      "Internal Links", "External Links", "Link-to-Word Ratio",
                      "Schema", "Content Type", "MIME Type", "Crawl Time (s)"]
        cols_order = [c for c in cols_order if c in df_display.columns] + \
                     [c for c in df_display.columns if c not in cols_order]
        df_display = df_display[cols_order]

        # Crawl Results with tabs
        st.subheader("📋 Crawl Results")
        tab1, tab2, tab3 = st.tabs(["All Pages", "By Content Type", "By Status"])
        
        with tab1:
            # MIME filter
            mime_options = sorted(df_display["MIME Type"].dropna().unique())
            selected_mime = st.multiselect(
                "Filter by MIME Type:",
                mime_options,
                default=mime_options,
                key="mime_filter"
            )
            df_filtered = df_display[df_display["MIME Type"].isin(selected_mime)]
            st.dataframe(df_filtered, use_container_width=True, height=400)
        
        with tab2:
            content_types = df_display["Content Type"].dropna().unique()
            selected_type = st.selectbox(
                "Select content type:",
                options=content_types,
                key="content_type_filter"
            )
            df_content = df_display[df_display["Content Type"] == selected_type]
            st.dataframe(df_content, use_container_width=True, height=400)
            st.caption(f"Showing {len(df_content)} pages of type '{selected_type}'")
        
        with tab3:
            status_types = sorted(df_display["Crawl Status"].dropna().unique())
            selected_status = st.selectbox(
                "Select crawl status:",
                options=status_types,
                key="status_filter"
            )
            df_status = df_display[df_display["Crawl Status"] == selected_status]
            st.dataframe(df_status, use_container_width=True, height=400)
            st.caption(f"Showing {len(df_status)} pages with status '{selected_status}'")

        # Charts
        st.subheader("📊 Visual Insights")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**MIME Type Distribution**")
            mime_dist = df_display["MIME Type"].value_counts()
            st.bar_chart(mime_dist)
        
        with chart_col2:
            st.markdown("**Content Type Distribution**")
            content_dist = df_display["Content Type"].value_counts()
            st.bar_chart(content_dist)
        
        # Additional charts
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            st.markdown("**HTTP Status Codes**")
            status_dist = df_display["Status"].value_counts()
            st.bar_chart(status_dist)
        
        with chart_col4:
            st.markdown("**Average Crawl Time by Content Type**")
            crawl_time_avg = df_display.groupby("Content Type")["Crawl Time (s)"].mean()
            st.bar_chart(crawl_time_avg)

        # Duplicate detection
        st.subheader("🔁 Duplicate Content Detection")
        st.markdown("Identify pages with duplicate titles, descriptions, and H1 tags.")
        
        df_dup = df_display.fillna("")
        dup_titles = df_dup[
            df_dup.duplicated("Title", keep=False) & df_dup["Title"].str.strip().astype(bool)
        ]
        dup_desc = df_dup[
        df_dup.duplicated("Description", keep=False) & df_dup["Description"].str.strip().astype(bool)
        ]
        dup_h1 = df_dup[
        df_dup.duplicated("H1", keep=False) & df_dup["H1"].str.strip().astype(bool)
        ]
        
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Duplicate Titles**")
            if not dup_titles.empty:
                st.dataframe(dup_titles[["URL", "Title"]], height=220, use_container_width=True)
                st.metric("Count", len(dup_titles))
            else:
                st.success("None ✅")
                st.metric("Count", "0")

        with col2:
            st.markdown("**Duplicate Descriptions**")
            if not dup_desc.empty:
                st.dataframe(dup_desc[["URL", "Description"]], height=220, use_container_width=True)
                st.metric("Count", len(dup_desc))
            else:
                st.success("None ✅")
                st.metric("Count", "0")

        with col3:
            st.markdown("**Duplicate H1s**")
            if not dup_h1.empty:
                st.dataframe(dup_h1[["URL", "H1"]], height=220, use_container_width=True)
                st.metric("Count", len(dup_h1))
            else:
                st.success("None ✅")
                st.metric("Count", "0")

        st.markdown("---")

        # Main Analysis Tabs
        analysis_tab1, analysis_tab2 = st.tabs([
            "📊 Organic Research",
            "📈 Advanced Metrics"
        ])
        
        with analysis_tab1:
            # after df_filtered is computed (and it contains the HTML column):
            org.render_streamlit_organic_ui(st, df_filtered, html_col="HTML")
        
        with analysis_tab2:
            st.markdown("---")

        st.markdown("---")

        # Summary
        st.subheader("📈 Site Summary & Metrics")
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            st.metric("Avg Title Length", f"{int(df_filtered['Title Length'].mean())} chars")
        with summary_col2:
            st.metric("Avg Meta Length", f"{int(df_filtered['Description Length'].mean())} chars")
        with summary_col3:
            st.metric("Avg Word Count", f"{int(df_filtered['Word Count'].mean())} words")
        with summary_col4:
            st.metric("Avg Crawl Time", f"{round(df_filtered['Crawl Time (s)'].mean(), 2)}s")

        st.markdown("---")

        # Excel export
        st.subheader("📥 Export Reports")
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            df_filtered.to_excel(writer, sheet_name="Crawl Results", index=False)
            if not dup_titles.empty:
                dup_titles.to_excel(writer, sheet_name="Duplicate Titles", index=False)
            if not dup_desc.empty:
                dup_desc.to_excel(writer, sheet_name="Duplicate Descriptions", index=False)
            if not dup_h1.empty:
                dup_h1.to_excel(writer, sheet_name="Duplicate H1s", index=False)
            summary = {
                "Pages Crawled": [len(df_filtered)],
                "Avg Title Length": [int(df_filtered['Title Length'].mean())],
                "Avg Description Length": [int(df_filtered['Description Length'].mean())],
                "Avg Word Count": [int(df_filtered['Word Count'].mean())],
                "Avg Crawl Time (s)": [round(df_filtered['Crawl Time (s)'].mean(), 2)]
            }
            pd.DataFrame(summary).to_excel(writer, sheet_name="Summary", index=False)
            writer.close()
        towrite.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📊 Download Excel Report",
                data=towrite.getvalue(),
                file_name="seo_crawl_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col2:
            csv_data = df_filtered.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name="seo_crawl_results.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")

        # Promote Keyword Research Tool
        st.subheader("🔍 Next Steps: Keyword Research")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            Ready to dive deeper into keyword analysis? Use the **Keyword Research Tool** to:
            - 📊 Analyze keyword frequency across your site
            - 🎯 Identify high-value optimization opportunities
            - 📈 Discover search intent patterns
            - 🔗 Find related keyword clusters
            - 📄 Generate keyword variations
            
            The tool is **independent** and can also analyze competitor content or custom text!
            """)
        with col2:
            st.markdown("")
            st.markdown("")
            if st.button("🔍 Go to Keyword Research →", use_container_width=True, key="nav_to_kr"):
                st.switch_page("pages/2_kw_research_view.py")
