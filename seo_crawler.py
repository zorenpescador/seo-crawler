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
                "Crawl Time (s)": crawl_time
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
st.set_page_config(page_title="Advanced SEO Site Crawler", layout="wide")
st.title("🔎 Advanced SEO Site Crawler")

with st.sidebar:
    st.markdown("### Crawl Settings")
    seed_url = st.text_input("Enter site URL (include https://):", value="https://example.com")
    max_pages = st.number_input("Max pages to crawl", min_value=1, max_value=2000, value=200, step=10)
    delay = st.slider("Delay between requests (seconds)", 0.0, 5.0, 0.5, 0.1)
    ignore_robots = st.checkbox("Ignore robots.txt (testing only; use responsibly)", value=False)
    run_button = st.button("Start Crawl", key="start")

status_area = st.empty()
progress_bar = st.progress(0.0)

if run_button:
    if not seed_url.startswith("http"):
        st.error("Please provide a valid URL starting with http:// or https://")
    else:
        def show_progress(pct, message):
            try:
                progress_bar.progress(min(max(pct, 0.0), 1.0))
            except Exception:
                pass
            status_area.markdown(f"**{message}**")

        status_area.info("Preparing to crawl...")
        df, meta = crawl_site(seed_url, max_pages=max_pages, delay=delay, ignore_robots=ignore_robots, show_progress_cb=show_progress)

        if meta.get("blocked"):
            st.error(f"⛔ Crawling blocked by robots.txt: {meta.get('robots_url')}")
            st.warning("You may toggle 'Ignore robots.txt' to override (use responsibly).")
        elif df is None or df.empty:
            st.warning("⚠️ No pages crawled.")
        else:
            progress_bar.progress(1.0)
            st.success(f"✅ Crawl completed — {len(df)} pages collected")

            df_display = df.copy()
            cols_order = ["URL", "Status", "Crawl Status", "Title", "Title Length",
                          "Description", "Description Length", "H1", "Word Count",
                          "Internal Links", "External Links", "Link-to-Word Ratio",
                          "Schema", "Content Type", "MIME Type", "Crawl Time (s)"]
            cols_order = [c for c in cols_order if c in df_display.columns] + \
                         [c for c in df_display.columns if c not in cols_order]
            df_display = df_display[cols_order]

            # MIME filter
            st.subheader("Crawl Results")
            mime_options = sorted(df_display["MIME Type"].dropna().unique())
            selected_mime = st.multiselect("Filter by MIME Type:", mime_options, default=mime_options)
            df_filtered = df_display[df_display["MIME Type"].isin(selected_mime)]
            st.dataframe(df_filtered, use_container_width=True)

            # Charts
            st.subheader("📊 Visual Insights")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**MIME Type Distribution**")
                st.bar_chart(df_filtered["MIME Type"].value_counts())
            with col2:
                st.markdown("**Content Type Distribution**")
                st.bar_chart(df_filtered["Content Type"].value_counts())

            # Duplicate detection
            st.subheader("🔁 Duplicate Content Detection")
            df_dup = df_filtered.fillna("")
            dup_titles = df_dup[df_dup.duplicated("Title", keep=False) & df_dup["Title"].str.strip().astype(bool)]
            dup_desc = df_dup[df_dup.duplicated("Description", keep=False) & df_dup["Description"].str.strip().astype(bool)]
            dup_h1 = df_dup[df_dup.duplicated("H1", keep=False) & df_dup["H1"].str.strip().astype(bool)]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Duplicate Titles**")
                st.dataframe(dup_titles[["URL", "Title"]]) if not dup_titles.empty else st.info("None ✅")
            with col2:
                st.markdown("**Duplicate Meta Descriptions**")
                st.dataframe(dup_desc[["URL", "Description"]]) if not dup_desc.empty else st.info("None ✅")
            with col3:
                st.markdown("**Duplicate H1s**")
                st.dataframe(dup_h1[["URL", "H1"]]) if not dup_h1.empty else st.info("None ✅")

            # Summary
            st.subheader("📊 Site Summary")
            st.markdown(f"- Pages crawled: **{len(df_filtered)}**")
            st.markdown(f"- Avg title length: **{int(df_filtered['Title Length'].mean())}** chars")
            st.markdown(f"- Avg description length: **{int(df_filtered['Description Length'].mean())}** chars")
            st.markdown(f"- Avg word count: **{int(df_filtered['Word Count'].mean())}** words")
            st.markdown(f"- Avg crawl time: **{round(df_filtered['Crawl Time (s)'].mean(),2)}s/page**")

            # Excel export
            st.subheader("📥 Export / Download")
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
            st.download_button(
                label="⬇️ Download Excel Report",
                data=towrite.getvalue(),
                file_name="seo_crawl_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
