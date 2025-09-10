import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
import json
import re

# ---------------------------
# Helper Functions
# ---------------------------

def can_fetch(url, user_agent="*"):
    """Check robots.txt permission for given URL"""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url), robots_url
    except:
        return True, robots_url  # fallback allow


def detect_content_type(url, soup):
    """Categorize page type by URL patterns and tags"""
    url_lower = url.lower()
    if "blog" in url_lower or soup.find_all("article"):
        return "Blog"
    elif re.search(r"product|item|shop", url_lower):
        return "Product"
    elif re.search(r"about|contact|service|solutions", url_lower):
        return "Landing Page"
    else:
        return "Other"


def extract_schema(soup):
    """Extract JSON-LD schema blocks"""
    schemas = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict):
                schemas.append(data.get("@type", "Unknown"))
            elif isinstance(data, list):
                schemas.extend([d.get("@type", "Unknown") for d in data if isinstance(d, dict)])
        except:
            continue
    return ", ".join(schemas) if schemas else ""


def crawl_site(start_url, max_pages=50):
    visited = set()
    to_visit = [start_url]
    results = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        allowed, robots_url = can_fetch(url)
        if not allowed:
            st.error(f"🚫 Blocked by robots.txt: {robots_url}")
            break

        try:
            res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            status_code = res.status_code

            soup = BeautifulSoup(res.text, "html.parser")

            title = soup.title.string.strip() if soup.title else ""
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc = desc_tag["content"].strip() if desc_tag and "content" in desc_tag.attrs else ""

            h_tags = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}
            h1 = h_tags["h1"][0] if h_tags["h1"] else ""

            word_count = len(soup.get_text(" ", strip=True).split())
            links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
            internal_links = [l for l in links if urlparse(l).netloc == urlparse(start_url).netloc]
            external_links = [l for l in links if urlparse(l).netloc != urlparse(start_url).netloc]

            schema = extract_schema(soup)
            page_type = detect_content_type(url, soup)

            results.append({
                "URL": url,
                "Status": status_code,
                "Title": title,
                "Title Length": len(title),
                "Description": desc,
                "Description Length": len(desc),
                "H1": h1,
                "Word Count": word_count,
                "Internal Links": len(internal_links),
                "External Links": len(external_links),
                "Link-to-Word Ratio": round(len(links) / word_count, 3) if word_count else 0,
                "Schema": schema,
                "Content Type": page_type,
                "H Tags": str(h_tags)
            })

            # Add new internal links to crawl queue
            for l in internal_links:
                if l not in visited and l not in to_visit:
                    to_visit.append(l)

            visited.add(url)

        except Exception as e:
            st.warning(f"⚠️ Failed to fetch {url} ({e})")

    return pd.DataFrame(results)


# ---------------------------
# Streamlit App
# ---------------------------

st.title("🔎 Advanced SEO Site Crawler")

url = st.text_input("Enter a website URL:", "https://example.com")
max_pages = st.slider("Max pages to crawl:", 10, 500, 50)

if st.button("Start Crawl"):
    with st.spinner("Crawling in progress..."):
        crawl_df = crawl_site(url, max_pages)

    if crawl_df.empty:
        st.warning("⚠️ No pages were crawled (possibly blocked by robots.txt or network error).")
    else:
        st.success("✅ Crawl Completed!")

        # Display Crawl Results
        st.subheader("Crawl Results")
        st.dataframe(crawl_df)

        # Duplicate Content Detection
        st.subheader("🔁 Duplicate Content Issues")

        dup_titles = crawl_df[crawl_df.duplicated("Title", keep=False) & crawl_df["Title"].notna()]
        dup_desc = crawl_df[crawl_df.duplicated("Description", keep=False) & crawl_df["Description"].notna()]
        dup_h1 = crawl_df[crawl_df.duplicated("H1", keep=False) & crawl_df["H1"].notna()]

        if not dup_titles.empty:
            st.markdown("### 📝 Duplicate Titles")
            st.dataframe(dup_titles)
        else:
            st.info("No duplicate titles found ✅")

        if not dup_desc.empty:
            st.markdown("### 📝 Duplicate Meta Descriptions")
            st.dataframe(dup_desc)
        else:
            st.info("No duplicate meta descriptions found ✅")

        if not dup_h1.empty:
            st.markdown("### 📝 Duplicate H1 Tags")
            st.dataframe(dup_h1)
        else:
            st.info("No duplicate H1 tags found ✅")

        # Export to Excel
        st.subheader("📊 Export Results")
        output_file = "seo_crawl_report.xlsx"
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            crawl_df.to_excel(writer, sheet_name="Crawl Results", index=False)
            if not dup_titles.empty:
                dup_titles.to_excel(writer, sheet_name="Duplicate Titles", index=False)
            if not dup_desc.empty:
                dup_desc.to_excel(writer, sheet_name="Duplicate Descriptions", index=False)
            if not dup_h1.empty:
                dup_h1.to_excel(writer, sheet_name="Duplicate H1", index=False)

        with open(output_file, "rb") as f:
            st.download_button("⬇️ Download Excel Report", f, file_name=output_file)
