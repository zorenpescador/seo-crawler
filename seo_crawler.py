import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
import time
from tabulate import tabulate
from collections import Counter

class SEOCrawler:
    def __init__(self, seed_url, max_pages=50, delay=1):
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
        """Load and parse robots.txt rules"""
        robots_url = urljoin(self.base_url, "/robots.txt")
        rp = RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            print(f"📜 Loaded robots.txt from {robots_url}")
        except Exception as e:
            print(f"⚠️ Could not read robots.txt: {e}")
        return rp

    def crawl(self):
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.pop(0)

            # Skip already visited
            if url in self.visited:
                continue

            # Respect robots.txt
            if not self.robots.can_fetch("*", url):
                print(f"⛔ Blocked by robots.txt: {url}")
                continue

            print(f"🔎 Crawling: {url}")
            self.visited.add(url)
            result, new_links = self.crawl_page(url)
            self.data.append(result)

            # Queue new internal links
            for link in new_links:
                if link not in self.visited and link not in self.to_visit:
                    self.to_visit.append(link)

            time.sleep(self.delay)

        # Save results
        self.save_results()

    def crawl_page(self, url):
        result = {
            "url": url,
            "status_code": None,
            "crawl_status": "Fail",
            "meta_title": None,
            "meta_title_length": 0,
            "meta_description": None,
            "meta_description_length": 0,
            "h1": [],
            "h_tags": [],
            "internal_links": [],
            "external_links": [],
            "anchor_texts": [],
            "word_count": 0,
            "schema": []
        }
        new_links = []

        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            result["status_code"] = r.status_code
            if r.status_code != 200:
                return result, []

            result["crawl_status"] = "Success"
            soup = BeautifulSoup(r.text, "lxml")

            # Meta title
            if soup.title:
                result["meta_title"] = soup.title.string.strip()
                result["meta_title_length"] = len(result["meta_title"])

            # Meta description
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                result["meta_description"] = desc["content"].strip()
                result["meta_description_length"] = len(result["meta_description"])

            # H tags
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                for h in soup.find_all(tag):
                    text = h.get_text(strip=True)
                    result["h_tags"].append({tag: text})
                    if tag == "h1":
                        result["h1"].append(text)

            # Links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if link.startswith("mailto:") or link.startswith("tel:"):
                    continue
                anchor = a.get_text(strip=True)
                result["anchor_texts"].append(anchor)
                if urlparse(link).netloc == self.domain:
                    result["internal_links"].append(link)
                    new_links.append(link)
                else:
                    result["external_links"].append(link)

            # Word count
            text = soup.get_text(separator=" ", strip=True)
            result["word_count"] = len(text.split())

            # Schema
            schema_scripts = soup.find_all("script", type="application/ld+json")
            for sc in schema_scripts:
                if sc.string:
                    result["schema"].append(sc.string.strip())

        except Exception as e:
            result["crawl_status"] = f"Error: {e}"

        return result, new_links

    def detect_duplicates(self, df):
        """Detect duplicate titles, descriptions, H1s"""
        duplicates = {
            "Duplicate Titles": df[df.duplicated("meta_title", keep=False) & df["meta_title"].notna()][["url", "meta_title"]],
            "Duplicate Descriptions": df[df.duplicated("meta_description", keep=False) & df["meta_description"].notna()][["url", "meta_description"]],
            "Duplicate H1s": df[df.duplicated("h1", keep=False) & df["h1"].notna()][["url", "h1"]],
        }
        return duplicates

    def save_results(self):
        df = pd.DataFrame(self.data)

        # Detect duplicates
        duplicates = self.detect_duplicates(df)

        # Save to Excel with multiple sheets
        with pd.ExcelWriter("seo_crawl_results.xlsx", engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Crawl Data", index=False)
            for name, dup_df in duplicates.items():
                dup_df.to_excel(writer, sheet_name=name, index=False)

        # Pretty print summary
        summary_cols = ["url", "status_code", "meta_title_length", "meta_description_length", "word_count"]
        print("\n📊 Crawl Summary:\n")
        print(tabulate(df[summary_cols], headers="keys", tablefmt="grid", showindex=False))
        print("\n✅ Crawl completed. Results saved to seo_crawl_results.xlsx")


# Run the crawler
if __name__ == "__main__":
    seed = "https://example.com"  # Change to your website
    crawler = SEOCrawler(seed_url=seed, max_pages=50, delay=1)
    crawler.crawl()
