import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
import time
from collections import Counter
import io

# ------------------------
# SEO Crawler Class
# ------------------------
class SEOCrawler:
    def __init__(self, seed_url, max_pages=30, delay=1):
        self.seed_url = seed_url
        self.domain = urlparse(seed_url).netloc
        self.base_url = f"{urlparse(seed_url).scheme}://{self.domain}"
        self.visited = set()
        self.to_visit = [seed_url]
        self.data = []
        self.max_pages = max_pages
        self.delay = delay
        self.robots = self.load_robots()

    def load_robots(self):
        robots_url = urljoin(self.base_url, "/robots.txt")
        rp = RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
        except Exception as e:
            st.warning(f"⚠️ Could not read robots.txt: {e}")
        return rp

    def crawl(self, progress_bar, status_text):
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.pop(0)
            if url in self.visited:
                continue

            if not self.robots.can_fetch("*", url):
                st.write(f"⛔ Blocked by robots.txt: {url}")
                continue

            status_text.text(f"Crawling: {url}")
            self.visited.add(url)
            result, new_links = self.crawl_page(url)
            self.data.append(result)

            for link in new_links:
                if link not in self.visited and link not in self.to_visit:
                    self.to_visit.append(link)

            progress = len(self.visited) / self.max_pages
            progress_bar.progress(progress)
            time.sleep(self.delay)

        df = pd.DataFrame(self.data)
        return df

    def crawl_page(self, url):
        result = {
            "url": url,
            "status_code": None,
            "meta_title": None,
            "meta_title_length": 0,
            "meta_description": None,
            "meta_description_length": 0,
            "h1": [],
            "word_count": 0
        }
        new_links = []

        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            result["status_code"] = r.status_code
            if r.status_code != 200:
                return result, []

            soup = BeautifulSoup(r.text, "lxml")

            if soup.title:
                result["meta_title"] = soup.title.string.strip()
                result["meta_title_length"] = len(result["meta_title"])

            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                result["meta_description"] = desc["content"].strip()
                result["meta_description_length"] = len(result["meta_description"])

            for h in soup.find_all("h1"):
                result["h1"].append(h.get_text(strip=True))

            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if urlparse(link).netloc == self.domain:
                    new_links.append(link)

            text = soup.get_text(separator=" ", strip=True)
            result["word_count"] = len(text.split())

        except Exception as e:
            result["status_code"] = f"Error: {e}"

        return result, new_links


# ------------------------
# Streamlit App
# ------------------------
st.title("🔎 SEO Site Crawler")

seed_url = st.text_input("Enter a website URL:", "https://example.com")
max_pages = st.slider("Max pages to crawl:", 10, 200, 30)

if st.button("Start Crawl"):
    crawler = SEOCrawler(seed_url=seed_url, max_pages=max_pages, delay=1)

    progress_bar = st.progress(0)
    status_text = st.empty()

    with st.spinner("Crawling site..."):
        df = crawler.crawl(progress_bar, status_text)

    st.success("✅ Crawl Completed!")

    # Show results in Streamlit
    st.subheader("Crawl Results")
    st.dataframe(df)

    # Duplicate detection
    st.subheader("Duplicate Content Issues")
    if not df.empty:
        dup_titles = df[df.duplicated("meta_title", keep=False) & df["meta_title"].notna()]
        dup_desc = df[df.duplicated("meta_description", keep=False) & df["meta_description"].notna()]
        dup_h1 = df[df.duplicated("h1", keep=False) & df["h1"].notna()]

        if not dup_titles.empty:
            st.write("🔁 Duplicate Titles")
            st.dataframe(dup_titles[["url", "meta_title"]])

        if not dup_desc.empty:
            st.write("🔁 Duplicate Descriptions")
            st.dataframe(dup_desc[["url", "meta_description"]])

        if not dup_h1.empty:
            st.write("🔁 Duplicate H1s")
            st.dataframe(dup_h1[["url", "h1"]])

    # Download Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Crawl Data", index=False)
        if not dup_titles.empty:
            dup_titles.to_excel(writer, sheet_name="Duplicate Titles", index=False)
        if not dup_desc.empty:
            dup_desc.to_excel(writer, sheet_name="Duplicate Descriptions", index=False)
        if not dup_h1.empty:
            dup_h1.to_excel(writer, sheet_name="Duplicate H1s", index=False)

    st.download_button(
        label="📥 Download Excel Report",
        data=output.getvalue(),
        file_name="seo_crawl_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
