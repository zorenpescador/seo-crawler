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
        # return a permissive stub if can't read robots
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
            # handle dict or list
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
    # URL-based heuristics
    if re.search(r"/blog/|/news/|/posts/|/articles/", u) or soup.find("article"):
        return "Blog / Article"
    if re.search(r"/product/|/shop/|/item/|/store/|/collections/", u):
        return "Product"
    if re.search(r"/about|/contact|/service|/services|/pricing|/features", u):
        return "Landing Page"
    # Meta/type hints
    if soup.find("meta", attrs={"property":"og:type"}) and soup.find("meta", attrs={"property":"og:type"})["content"] == "product":
        return "Product"
    return "Other"

def normalize_url(u):
    # remove fragments and whitespace
    if not u:
        return u
    u = u.split('#')[0].strip()
    return u

# ---------------------------
# Core crawler
# ---------------------------

def crawl_site(seed_url, max_pages=100, delay=0.5, ignore_robots=False, show_progress_cb=None):
    """
    Returns pandas.DataFrame with collected data.
    show_progress_cb: optional callback(progress_float, message) - where progress_float in [0,1]
    """
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
        if not url:
            continue
        if url in visited:
            continue

        allowed, robots_url = allowed_by_robots(url, ignore_robots=ignore_robots)
        if not allowed:
            # Stop crawling for blocked seed domain or skip this URL
            # We'll skip and continue
            # Note: for user clarity we return robots_url so UI can show it
            return pd.DataFrame(), {"blocked": True, "robots_url": robots_url}

        # status update
        if show_progress_cb:
            show_progress_cb(min(len(visited)/max_pages, 1.0), f"Crawling: {url}")

        try:
            r = session.get(url, timeout=12)
            status_code = r.status_code
            if status_code >= 400:
                # record but skip parsing heavy pages
                results.append({
                    "URL": url,
                    "Status": status_code,
                    "Crawl Status": "HTTP Error",
                    "Title": "",
                    "Title Length": 0,
                    "Description": "",
                    "Description Length": 0,
                    "H1": "",
                    "H Tags": "",
                    "Word Count": 0,
                    "Internal Links": 0,
                    "External Links": 0,
                    "Link-to-Word Ratio": 0,
                    "Schema": "",
                    "Content Type": "",
                })
                visited.add(url)
                time.sleep(delay)
                continue

            soup = BeautifulSoup(r.text, "lxml")

            # Title & description
            title = (soup.title.string.strip() if soup.title and soup.title.string else "").strip()
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

            # Headings
            h_tags = {}
            for i in range(1,7):
                hs = [h.get_text(" ", strip=True) for h in soup.find_all(f"h{i}")]
                h_tags[f"h{i}"] = hs
            h1 = h_tags["h1"][0] if h_tags["h1"] else ""

            # Links
            anchors = []
            internal_links = []
            external_links = []
            for a in soup.find_all("a", href=True):
                raw_href = a.get("href")
                if raw_href is None:
                    continue
                href = urljoin(url, raw_href)
                href = normalize_url(href)
                if not href:
                    continue
                anchors.append({"href": href, "text": a.get_text(" ", strip=True)})
                parsed = urlparse(href)
                if parsed.netloc == seed_domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)

            # Word count
            text = soup.get_text(" ", strip=True)
            words = text.split()
            word_count = len(words)

            # Link-to-word ratio
            total_links = len(internal_links) + len(external_links)
            link_to_word = round(total_links / word_count, 3) if word_count else 0

            schema = extract_schema_types(soup)
            content_type = detect_content_type(url, soup)

            results.append({
                "URL": url,
                "Status": status_code,
                "Crawl Status": "Success",
                "Title": title,
                "Title Length": len(title),
                "Description": desc,
                "Description Length": len(desc),
                "H1": h1,
                "H Tags": json.dumps(h_tags, ensure_ascii=False),
                "Word Count": word_count,
                "Internal Links": len(set(internal_links)),
                "External Links": len(set(external_links)),
                "Link-to-Word Ratio": link_to_word,
                "Schema": schema,
                "Content Type": content_type,
            })

            # add internal links to queue
            for link in internal_links:
                if link not in visited and link not in to_visit:
                    # restrict to same scheme+domain (avoid mailto, tel)
                    p = urlparse(link)
                    if p.scheme in ("http", "https"):
                        to_visit.append(link)

            visited.add(url)
            time.sleep(delay)

        except Exception as e:
            # On network parse error record the URL with error
            results.append({
                "URL": url,
                "Status": "Error",
                "Crawl Status": f"Error: {e}",
                "Title": "",
                "Title Length": 0,
                "Description": "",
                "Description Length": 0,
                "H1": "",
                "H Tags": "",
                "Word Count": 0,
                "Internal Links": 0,
                "External Links": 0,
                "Link-to-Word Ratio": 0,
                "Schema": "",
                "Content Type": "",
            })
            visited.add(url)
            time.sleep(delay)
            continue

    df = pd.DataFrame(results)
    return df, {"blocked": False}

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
        # small helper to update progress area
        def show_progress(pct, message):
            try:
                progress_bar.progress(min(max(pct, 0.0), 1.0))
            except Exception:
                pass
            status_area.markdown(f"**{message}**")

        status_area.info("Preparing to crawl...")
        df, meta = crawl_site(seed_url, max_pages=max_pages, delay=delay, ignore_robots=ignore_robots, show_progress_cb=show_progress)

        # If blocked by robots.txt
        if meta.get("blocked"):
            robots_url = meta.get("robots_url")
            st.error(f"⛔ Crawling blocked by robots.txt: {robots_url}")
            st.warning("You may toggle 'Ignore robots.txt' (testing only) to override. Do not use irresponsibly.")
        elif df is None or df.empty:
            st.warning("⚠️ No pages crawled (network error, no allowed pages, or site blocked).")
        else:
            progress_bar.progress(1.0)
            st.success(f"✅ Crawl completed — {len(df)} pages collected")

            # Clean columns
            df_display = df.copy()
            # Show friendly column order
            cols_order = ["URL", "Status", "Crawl Status", "Title", "Title Length", "Description", "Description Length", "H1", "Word Count", "Internal Links", "External Links", "Link-to-Word Ratio", "Schema", "Content Type"]
            cols_order = [c for c in cols_order if c in df_display.columns] + [c for c in df_display.columns if c not in cols_order]
            df_display = df_display[cols_order]

            st.subheader("Crawl Results")
            st.dataframe(df_display, use_container_width=True)

            # Duplicate detection
            st.subheader("🔁 Duplicate Content Detection")
            # fillna with empty strings so duplicated detection works
            df_dup = df_display.fillna("")
            dup_titles = df_dup[df_dup.duplicated("Title", keep=False) & df_dup["Title"].str.strip().astype(bool)]
            dup_desc = df_dup[df_dup.duplicated("Description", keep=False) & df_dup["Description"].str.strip().astype(bool)]
            dup_h1 = df_dup[df_dup.duplicated("H1", keep=False) & df_dup["H1"].str.strip().astype(bool)]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Duplicate Titles**")
                if not dup_titles.empty:
                    st.dataframe(dup_titles[["URL", "Title"]], height=250)
                else:
                    st.info("No duplicate titles found ✅")
            with col2:
                st.markdown("**Duplicate Meta Descriptions**")
                if not dup_desc.empty:
                    st.dataframe(dup_desc[["URL", "Description"]], height=250)
                else:
                    st.info("No duplicate meta descriptions ✅")
            with col3:
                st.markdown("**Duplicate H1s**")
                if not dup_h1.empty:
                    st.dataframe(dup_h1[["URL", "H1"]], height=250)
                else:
                    st.info("No duplicate H1s ✅")

            # Simple summary metrics
            st.subheader("📊 Site Summary")
            total_pages = len(df)
            avg_title_len = int(df["Title Length"].replace("", 0).astype(int).mean()) if "Title Length" in df.columns and not df["Title Length"].empty else 0
            avg_desc_len = int(df["Description Length"].replace("", 0).astype(int).mean()) if "Description Length" in df.columns and not df["Description Length"].empty else 0
            avg_wc = int(df["Word Count"].replace("", 0).astype(int).mean()) if "Word Count" in df.columns and not df["Word Count"].empty else 0

            st.markdown(f"- Pages crawled: **{total_pages}**")
            st.markdown(f"- Average title length: **{avg_title_len}** chars")
            st.markdown(f"- Average description length: **{avg_desc_len}** chars")
            st.markdown(f"- Average word count: **{avg_wc}** words")

            # Export to Excel in-memory
            st.subheader("📥 Export / Download")
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                df_display.to_excel(writer, sheet_name="Crawl Results", index=False)
                if not dup_titles.empty:
                    dup_titles.to_excel(writer, sheet_name="Duplicate Titles", index=False)
                if not dup_desc.empty:
                    dup_desc.to_excel(writer, sheet_name="Duplicate Descriptions", index=False)
                if not dup_h1.empty:
                    dup_h1.to_excel(writer, sheet_name="Duplicate H1s", index=False)

                # Add a small dashboard sheet
                summary = {
                    "Pages Crawled": [total_pages],
                    "Avg Title Length": [avg_title_len],
                    "Avg Description Length": [avg_desc_len],
                    "Avg Word Count": [avg_wc]
                }
                pd.DataFrame(summary).to_excel(writer, sheet_name="Summary", index=False)

                writer.save()
            towrite.seek(0)

            st.download_button(
                label="⬇️ Download Excel Report",
                data=towrite.getvalue(),
                file_name="seo_crawl_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
