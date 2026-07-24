import hashlib
import os
import re
from collections import Counter
from typing import Any, Dict, List

import pandas as pd
from bs4 import BeautifulSoup

from checks.architecture import (
    check_C067, check_C068, check_C070, check_C071, check_C072, check_C073, check_C074,
    check_C075, check_C077, check_C078, check_C079,
)
from checks.crawlability import (
    check_C001, check_C002, check_C003, check_C004, check_C005, check_C006, check_C007,
    check_C008, check_C009, check_C010, check_C012, check_C013, check_C014, check_C015,
    check_C016, check_C017, check_C018, check_C019, check_C020,
)
from checks.international import (
    check_C096, check_C097, check_C098, check_C099, check_C100, check_C101, check_C102,
    check_C103, check_C104, check_C105, check_C106, check_C107,
)
from checks.links import (
    check_C081, check_C082, check_C083, check_C084, check_C085, check_C086, check_C087,
    check_C088, check_C089, check_C090, check_C091, check_C092, check_C093, check_C094, check_C095,
)
from checks.markup import check_C109, check_C110, check_C111, check_C113, check_C116
from checks.mobile import check_C129, check_C131, check_C132, check_C134
from checks.performance import (
    check_C119, check_C121, check_C122, check_C123, check_C124, check_C125, check_C127, check_C128,
)
from checks.on_page import check_C042, check_C043, check_C046, check_C047, check_C050, check_C052, check_C058, check_C059, check_C060, check_C061, check_C062, check_C063, check_C064, check_C065
from checks.redirects import check_C032, check_C034, check_C035, check_C036, check_C037, check_C038, check_C039
from checks.security import check_C022, check_C023, check_C024, check_C025, check_C026, check_C027, check_C028, check_C030


SEVERITY_WEIGHTS = {
    "Error": 3,
    "Warning": 2,
    "Notice": 1,
}

CATEGORY_WEIGHTS = {
    "Crawlability & Indexability": 10,
    "HTTPS & Security": 10,
    "Redirects": 10,
    "On-Page & Duplicates": 10,
    "Site Architecture & Internal Linking": 10,
    "Links": 10,
    "International SEO": 10,
    "Markup & Structured Data": 10,
    "Site Performance": 10,
    "Mobile & Accessibility": 10,
}

CATEGORY_LABELS = {
    "Crawlability & Indexability": "crawlability",
    "HTTPS & Security": "security",
    "Redirects": "redirects",
    "On-Page & Duplicates": "on_page",
    "Site Architecture & Internal Linking": "architecture",
    "Links": "links",
    "International SEO": "international",
    "Markup & Structured Data": "markup",
    "Site Performance": "performance",
    "Mobile & Accessibility": "mobile",
}

FALLBACK_CHECK_CATALOG = {
    "Orphan Pages": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "URLs are present in the crawl surface but not discovered through internal links.",
    },
    "Non-HTTPS Pages": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "Some pages are being served over an insecure HTTP URL.",
    },
    "Redirecting Pages": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "Detected 3xx redirects in the crawl results.",
    },
    "Duplicate Titles": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Multiple URLs share the same title text.",
    },
    "Duplicate Meta Descriptions": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Multiple URLs share the same description text.",
    },
    "Duplicate H1 Tags": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Multiple URLs share the same H1 text.",
    },
    "Duplicate Body Content": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Normalized body content is duplicated across pages.",
    },
    "Missing Title": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Pages are missing a title tag.",
    },
    "Missing Description": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are missing a meta description.",
    },
    "Missing H1": {
        "category": "On-Page & Duplicates",
        "severity": "Error",
        "notes": "Pages are missing an H1 tag.",
    },
    "Missing Canonical": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are missing a canonical link.",
    },
    "Title Too Short": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Titles are under 30 characters.",
    },
    "Title Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Titles are over 60 characters.",
    },
    "Meta Description Too Short": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Meta descriptions are under 70 characters.",
    },
    "Meta Description Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Meta descriptions are over 160 characters.",
    },
    "Multiple H1s": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages contain more than one H1 tag.",
    },
    "Missing Language Declaration": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Pages are missing an html lang attribute.",
    },
    "H1 Duplicates Title": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "The H1 text is identical to the title tag.",
    },
    "URL Too Long": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs are over 115 characters.",
    },
    "URL Contains Uppercase": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs contain uppercase characters, a case-variant duplicate risk.",
    },
    "URL Contains Underscores": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs use underscores instead of hyphens as word separators.",
    },
    "URL Excessive Parameters": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs have more than 3 query parameters, a duplicate-content risk.",
    },
    "Low Text-to-HTML Ratio": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Pages are markup-heavy relative to visible text.",
    },
    "Missing Favicon Link": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages don't declare a favicon via a <link rel=icon> tag.",
    },
    "Missing Twitter Card Tags": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages are missing a twitter:card meta tag.",
    },
    "Invalid Structured Data": {
        "category": "Markup & Structured Data",
        "severity": "Error",
        "notes": "Pages have a JSON-LD script block that fails to parse.",
    },
    "Images Missing Dimensions": {
        "category": "Site Performance",
        "severity": "Warning",
        "notes": "Images are missing explicit width/height attributes (layout shift risk).",
    },
    "Excessive DOM Size": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Pages have more than 1500 DOM nodes, approximated via tag count.",
    },
    "Legacy Image Formats": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Images use legacy formats (jpg/png/gif/bmp) instead of webp/avif.",
    },
    "Broken Heading Hierarchy": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "Heading levels skip more than one step (e.g. H1 straight to H3).",
    },
    "Non-Descriptive URL": {
        "category": "On-Page & Duplicates",
        "severity": "Notice",
        "notes": "URLs end in an auto-generated numeric or hex ID rather than a descriptive slug.",
    },
    "Insecure External Link": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Pages link out to an external domain over plain HTTP.",
    },
    "Offsite Image Hosting": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Images are hosted on a different, uncontrolled domain (hotlinking risk).",
    },
    "JavaScript Void Link": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Links use a javascript:void href with no real fallback target.",
    },
    "Excessive Inferred Requests": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Pages have more than 100 script/link/img tags, a proxy for request count.",
    },
    "Render-Blocking Script": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "A <script src> in <head> lacks async/defer, blocking rendering.",
    },
    "Missing Viewport Meta (Mobile)": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Pages are missing a viewport meta tag (mobile UX lens).",
    },
    "Form Fields Missing Label": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Form fields have no associated <label>, aria-label, or aria-labelledby.",
    },
    "Noindex Directive": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "Pages carry a meta robots noindex directive.",
    },
    "Meta Nofollow": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "Pages carry a meta robots nofollow directive, blocking link equity flow.",
    },
    "Soft 404": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "Pages return HTTP 200 but have thin, error-like content.",
    },
    "Cross-Domain Canonical": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "The canonical tag points to a different domain than the page itself.",
    },
    "Mixed Content": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "HTTPS pages load http:// sub-resources (img/script/link).",
    },
    "Meta Refresh Redirect": {
        "category": "Redirects",
        "severity": "Notice",
        "notes": "Pages use a meta-refresh redirect instead of a standard HTTP redirect.",
    },
    "Trailing Slash Duplicate": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "Both the trailing-slash and non-trailing-slash URL variants resolve without redirecting.",
    },
    "WWW Non-WWW Duplicate": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "Both the www and non-www host variants resolve without redirecting.",
    },
    "Excessive Internal Links": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "Pages have more than 100 internal links, diluting link equity.",
    },
    "Broken Internal Link": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Error",
        "notes": "Pages link internally to a URL that returns a 4XX/5XX status.",
    },
    "Internal Link To Redirect": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Warning",
        "notes": "Pages link internally to a URL that redirects instead of the final target.",
    },
    "Internal Link Nofollow": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "Pages use rel=nofollow on an internal link, unusual for site navigation.",
    },
    "Generic Anchor Text": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "Pages have an internal link with empty or generic anchor text (e.g. 'click here').",
    },
    "Broken Canonical Target": {
        "category": "Links",
        "severity": "Error",
        "notes": "The canonical URL returns a 4XX/5XX status in the crawled set.",
    },
    "Excessive Outbound Links": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Pages have a high ratio of outbound links relative to word count.",
    },
    "Insecure Form Action": {
        "category": "Links",
        "severity": "Warning",
        "notes": "A form on an HTTPS page submits to a plain http:// action.",
    },
    "Invalid Hreflang Code": {
        "category": "International SEO",
        "severity": "Error",
        "notes": "A hreflang attribute uses a malformed language/region code.",
    },
    "Multiple X-Default Hreflang": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "Pages declare more than one x-default hreflang entry.",
    },
    "Missing X-Default Hreflang": {
        "category": "International SEO",
        "severity": "Notice",
        "notes": "Pages have multiple hreflang entries but no x-default.",
    },
    "Duplicate Hreflang": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "Pages declare the same hreflang language/region code more than once.",
    },
    "Not Crawlable": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "The request itself failed (timeout/DNS/connection error), not an HTTP error status.",
    },
    "Canonical Points To Noindex": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "The canonical target carries a meta robots noindex directive.",
    },
    "Canonical Chain": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "The canonical target has its own different canonical, so it doesn't resolve to a stable page.",
    },
    "Pagination Signals Missing": {
        "category": "Crawlability & Indexability",
        "severity": "Notice",
        "notes": "A paginated-looking URL has neither rel=next/prev nor a self-referencing canonical.",
    },
    "Excessive Click Depth": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Warning",
        "notes": "Pages are more than 3 clicks from the homepage.",
    },
    "Severe Click Depth": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Error",
        "notes": "Pages are more than 5 clicks from the homepage.",
    },
    "Navigation Link Count Anomaly": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "A page's total link count is far below the sitewide median, suggesting missing standard navigation.",
    },
    "Breadcrumb Missing On Deep Page": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "Pages more than 2 clicks deep have no breadcrumb markup.",
    },
    "Pagination Missing First/Last": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "Pages in a pagination series (rel=next/prev) have no link to the first or last page.",
    },
    "Broken Hreflang Target": {
        "category": "Links",
        "severity": "Error",
        "notes": "An hreflang link points to a URL that returns a 4XX/5XX status in the crawled set.",
    },
    "Tracking Parameters In Link": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Pages link to a URL carrying tracking parameters (utm_*, fbclid, gclid, etc.) that isn't canonicalized.",
    },
    "Hreflang Missing Return Link": {
        "category": "International SEO",
        "severity": "Error",
        "notes": "A hreflang target doesn't link back to the page that references it.",
    },
    "Hreflang Points To Non-Canonical": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "An hreflang target has its own different canonical URL.",
    },
    "Hreflang Points To Broken URL": {
        "category": "International SEO",
        "severity": "Error",
        "notes": "An hreflang link points to a URL that returns a 4XX/5XX status in the crawled set.",
    },
    "Hreflang Language Conflict": {
        "category": "International SEO",
        "severity": "Notice",
        "notes": "The html lang attribute disagrees with the page's own hreflang self-reference.",
    },
    "Structured Data Missing Fields": {
        "category": "Markup & Structured Data",
        "severity": "Warning",
        "notes": "Structured data is missing fields normally required for its declared @type.",
    },
    "Structured Data Type Mismatch": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "A Product schema type is declared on a page with no images.",
    },
    "Unlazy Below-Fold Images": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "Images beyond the first in document order have no loading=lazy attribute.",
    },
    "Empty Alt Attribute": {
        "category": "Mobile & Accessibility",
        "severity": "Notice",
        "notes": "Images explicitly carry alt=\"\", valid for decorative images but risky on content images.",
    },
    "Dense Tap Targets": {
        "category": "Mobile & Accessibility",
        "severity": "Notice",
        "notes": "Pages have a high density of inline links relative to word count, a tap-target risk.",
    },
    "Robots Txt Missing": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "No robots.txt found at the domain root.",
    },
    "Robots Txt Invalid": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "robots.txt contains a line that isn't a recognized directive.",
    },
    "Robots Txt Blocks Site": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "robots.txt disallows the entire site for all user-agents.",
    },
    "Robots Txt Blocks Assets": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "robots.txt disallows a common CSS/JS asset path.",
    },
    "Sitemap Missing": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "No sitemap found, whether declared in robots.txt or at /sitemap.xml.",
    },
    "Sitemap Invalid": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "The sitemap was found but failed to parse as XML.",
    },
    "Sitemap Contains Broken URLs": {
        "category": "Crawlability & Indexability",
        "severity": "Error",
        "notes": "URLs listed in the sitemap return a 4XX/5XX status in the crawled set.",
    },
    "Sitemap Contains Redirected URLs": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "URLs listed in the sitemap redirect elsewhere in the crawled set.",
    },
    "Sitemap Contains Noindex URLs": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "URLs listed in the sitemap carry a noindex directive.",
    },
    "Sitemap Not In Robots": {
        "category": "Crawlability & Indexability",
        "severity": "Notice",
        "notes": "A sitemap exists but isn't declared in robots.txt.",
    },
    "No HTTP-To-HTTPS Redirect": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "The http:// version of a crawled URL doesn't redirect to https://.",
    },
    "Missing HSTS Header": {
        "category": "HTTPS & Security",
        "severity": "Warning",
        "notes": "HTTPS pages don't send a Strict-Transport-Security header.",
    },
    "Missing Security Headers": {
        "category": "HTTPS & Security",
        "severity": "Notice",
        "notes": "Pages send none of X-Content-Type-Options, X-Frame-Options, or Content-Security-Policy.",
    },
    "Redirect Loop": {
        "category": "Redirects",
        "severity": "Error",
        "notes": "A redirect chain returns to a previously visited URL.",
    },
    "Internal Link To Redirect (Redirects Lens)": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "Pages link internally to a URL that redirects instead of the final target.",
    },
    "Redirect To Broken Destination": {
        "category": "Redirects",
        "severity": "Error",
        "notes": "A redirect resolves to a URL that returns a 4XX/5XX status in the crawled set.",
    },
    "Multi-Hop HTTPS Upgrade": {
        "category": "Redirects",
        "severity": "Warning",
        "notes": "The http:// to https:// upgrade takes more than one redirect hop.",
    },
    "Anchor Text Mismatch": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Notice",
        "notes": "An internal link's anchor text shares no significant words with its destination's title/H1.",
    },
    "Unmarked Affiliate Link": {
        "category": "Links",
        "severity": "Notice",
        "notes": "A link to a known affiliate network lacks rel=sponsored or rel=nofollow.",
    },
    "Hreflang Points To Redirect": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "An hreflang target redirects instead of resolving directly, in the crawled set.",
    },
    "Conflicting Robots Signals": {
        "category": "Crawlability & Indexability",
        "severity": "Warning",
        "notes": "The X-Robots-Tag header and meta robots tag disagree on noindex/nofollow.",
    },
    "HTTP URLs In Sitemap": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "The sitemap lists http:// URLs instead of https://.",
    },
    "SSL Certificate Expired": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "The site's TLS certificate validity end date has passed.",
    },
    "SSL Certificate Expiring Soon": {
        "category": "HTTPS & Security",
        "severity": "Warning",
        "notes": "The site's TLS certificate expires within 30 days.",
    },
    "SSL Certificate Hostname Mismatch": {
        "category": "HTTPS & Security",
        "severity": "Error",
        "notes": "The TLS certificate's CN/SAN doesn't match the crawled hostname.",
    },
    "Hreflang Cluster Inconsistent": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "A page's hreflang set doesn't match every other member of its hreflang cluster.",
    },
    "Hreflang Sitemap Disagreement": {
        "category": "International SEO",
        "severity": "Warning",
        "notes": "The hreflang set declared in the HTML disagrees with the sitemap's per-URL hreflang annotations.",
    },
    "Content Language Mismatch": {
        "category": "International SEO",
        "severity": "Notice",
        "notes": "The declared html lang doesn't match the auto-detected content language.",
    },
    "Uncompressed HTML Response": {
        "category": "Site Performance",
        "severity": "Warning",
        "notes": "The response has no gzip/br Content-Encoding.",
    },
    "Missing Caching Headers": {
        "category": "Site Performance",
        "severity": "Notice",
        "notes": "The response has no Cache-Control header.",
    },
    "Broken External Link": {
        "category": "Links",
        "severity": "Warning",
        "notes": "Pages link to an external URL that returns a 4XX/5XX status.",
    },
    "External Link Redirect Chain": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Pages link to an external URL that redirects before resolving.",
    },
    "External Resource Blocked By Robots": {
        "category": "Links",
        "severity": "Notice",
        "notes": "Pages link to an external resource disallowed by that domain's robots.txt.",
    },
    "Broken Image Source": {
        "category": "Links",
        "severity": "Error",
        "notes": "An <img src> fails to load (4XX/5XX).",
    },
    "Broken Favicon": {
        "category": "Links",
        "severity": "Notice",
        "notes": "The site's favicon returns a 4XX/5XX status.",
    },
    "Repeated Dead Outbound Link": {
        "category": "Links",
        "severity": "Warning",
        "notes": "The same broken external link is referenced by 3+ crawled pages (likely a site-wide template link).",
    },
    "Thin Content": {
        "category": "On-Page & Duplicates",
        "severity": "Warning",
        "notes": "Pages are below the 300-word content threshold.",
    },
    "Low Internal Link Support": {
        "category": "Site Architecture & Internal Linking",
        "severity": "Warning",
        "notes": "Pages have very few internal links, which can weaken crawl depth and equity distribution.",
    },
    "Missing Schema": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages do not expose JSON-LD or structured data markup.",
    },
    "Missing Open Graph Tags": {
        "category": "Markup & Structured Data",
        "severity": "Notice",
        "notes": "Pages are missing Open Graph title or description metadata.",
    },
    "Slow Response Time": {
        "category": "Site Performance",
        "severity": "Warning",
        "notes": "Several pages exceed the 2.5s response threshold.",
    },
    "Missing Viewport Meta": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Pages are missing a viewport meta tag, which can hurt mobile rendering signals.",
    },
    "Images Missing Alt Text": {
        "category": "Mobile & Accessibility",
        "severity": "Warning",
        "notes": "Pages contain images that do not have a usable alt attribute.",
    },
}

# checks_catalog.csv describes each check in prose (e.g. "missing <title>") that
# doesn't match the short display names used below (e.g. "Missing Title"), so we
# join on the stable check_id instead of the free-text check_name.
CHECK_NAME_TO_CATALOG_ID = {
    "Orphan Pages": "C066",
    "Non-HTTPS Pages": "C021",
    "Redirecting Pages": "C031",
    "Duplicate Titles": "C044",
    "Duplicate Meta Descriptions": "C048",
    "Duplicate H1 Tags": "C051",
    "Duplicate Body Content": "C054",
    "Missing Title": "C041",
    "Missing Description": "C045",
    "Missing H1": "C049",
    "Missing Canonical": "C056",
    "Title Too Short": "C042",
    "Title Too Long": "C043",
    "Meta Description Too Short": "C046",
    "Meta Description Too Long": "C047",
    "Multiple H1s": "C050",
    "Missing Language Declaration": "C059",
    "H1 Duplicates Title": "C052",
    "URL Too Long": "C062",
    "URL Contains Uppercase": "C065",
    "URL Contains Underscores": "C064",
    "URL Excessive Parameters": "C061",
    "Low Text-to-HTML Ratio": "C058",
    "Missing Favicon Link": "C116",
    "Missing Twitter Card Tags": "C113",
    "Invalid Structured Data": "C109",
    "Images Missing Dimensions": "C123",
    "Excessive DOM Size": "C127",
    "Legacy Image Formats": "C124",
    "Broken Heading Hierarchy": "C060",
    "Non-Descriptive URL": "C063",
    "Insecure External Link": "C082",
    "Offsite Image Hosting": "C086",
    "JavaScript Void Link": "C094",
    "Excessive Inferred Requests": "C121",
    "Render-Blocking Script": "C122",
    "Missing Viewport Meta (Mobile)": "C129",
    "Form Fields Missing Label": "C134",
    "Noindex Directive": "C012",
    "Meta Nofollow": "C013",
    "Soft 404": "C015",
    "Cross-Domain Canonical": "C018",
    "Mixed Content": "C023",
    "Meta Refresh Redirect": "C036",
    "Trailing Slash Duplicate": "C037",
    "WWW Non-WWW Duplicate": "C038",
    "Excessive Internal Links": "C070",
    "Broken Internal Link": "C071",
    "Internal Link To Redirect": "C072",
    "Internal Link Nofollow": "C073",
    "Generic Anchor Text": "C074",
    "Broken Canonical Target": "C088",
    "Excessive Outbound Links": "C092",
    "Insecure Form Action": "C095",
    "Invalid Hreflang Code": "C096",
    "Multiple X-Default Hreflang": "C101",
    "Missing X-Default Hreflang": "C102",
    "Duplicate Hreflang": "C106",
    "Not Crawlable": "C014",
    "Canonical Points To Noindex": "C017",
    "Canonical Chain": "C019",
    "Pagination Signals Missing": "C020",
    "Excessive Click Depth": "C067",
    "Severe Click Depth": "C068",
    "Navigation Link Count Anomaly": "C077",
    "Breadcrumb Missing On Deep Page": "C078",
    "Pagination Missing First/Last": "C079",
    "Broken Hreflang Target": "C089",
    "Tracking Parameters In Link": "C090",
    "Hreflang Missing Return Link": "C097",
    "Hreflang Points To Non-Canonical": "C098",
    "Hreflang Points To Broken URL": "C100",
    "Hreflang Language Conflict": "C104",
    "Structured Data Missing Fields": "C110",
    "Structured Data Type Mismatch": "C111",
    "Unlazy Below-Fold Images": "C125",
    "Empty Alt Attribute": "C131",
    "Dense Tap Targets": "C132",
    "Robots Txt Missing": "C001",
    "Robots Txt Invalid": "C002",
    "Robots Txt Blocks Site": "C003",
    "Robots Txt Blocks Assets": "C004",
    "Sitemap Missing": "C005",
    "Sitemap Invalid": "C006",
    "Sitemap Contains Broken URLs": "C007",
    "Sitemap Contains Redirected URLs": "C008",
    "Sitemap Contains Noindex URLs": "C009",
    "Sitemap Not In Robots": "C010",
    "No HTTP-To-HTTPS Redirect": "C024",
    "Missing HSTS Header": "C025",
    "Missing Security Headers": "C030",
    "Redirect Loop": "C032",
    "Internal Link To Redirect (Redirects Lens)": "C034",
    "Redirect To Broken Destination": "C035",
    "Multi-Hop HTTPS Upgrade": "C039",
    "Anchor Text Mismatch": "C075",
    "Unmarked Affiliate Link": "C093",
    "Hreflang Points To Redirect": "C099",
    "Conflicting Robots Signals": "C016",
    "HTTP URLs In Sitemap": "C022",
    "SSL Certificate Expired": "C026",
    "SSL Certificate Expiring Soon": "C027",
    "SSL Certificate Hostname Mismatch": "C028",
    "Hreflang Cluster Inconsistent": "C103",
    "Hreflang Sitemap Disagreement": "C105",
    "Content Language Mismatch": "C107",
    "Uncompressed HTML Response": "C119",
    "Missing Caching Headers": "C128",
    "Broken External Link": "C081",
    "External Link Redirect Chain": "C083",
    "External Resource Blocked By Robots": "C084",
    "Broken Image Source": "C085",
    "Broken Favicon": "C087",
    "Repeated Dead Outbound Link": "C091",
    "Thin Content": "C053",
    "Low Internal Link Support": "C076",
    "Missing Schema": "C108",
    "Missing Open Graph Tags": "C112",
    "Slow Response Time": "C118",
    "Missing Viewport Meta": "C117",
    "Images Missing Alt Text": "C130",
}


def _load_check_catalog() -> Dict[str, Dict[str, str]]:
    catalog_path = os.path.join(os.path.dirname(__file__), "checks_catalog.csv")
    if not os.path.exists(catalog_path):
        return {}

    try:
        catalog_df = pd.read_csv(catalog_path)
    except Exception:
        return {}

    catalog: Dict[str, Dict[str, str]] = {}
    for _, row in catalog_df.iterrows():
        check_id = str(row.get("check_id", "")).strip()
        if not check_id:
            continue
        catalog[check_id] = {
            "category": str(row.get("category", "On-Page & Duplicates")).strip(),
            "severity": str(row.get("severity", "Notice")).strip(),
            "notes": str(row.get("notes", "")).strip(),
        }
    return catalog


CHECK_CATALOG_BY_ID = _load_check_catalog()


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _html_to_text(html: Any) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(str(html), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return _normalize_text(soup.get_text(" ", strip=True))


def _content_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha1(text.lower().encode("utf-8")).hexdigest()


def _extract_internal_targets(html: Any) -> List[str]:
    if not html:
        return []
    soup = BeautifulSoup(str(html), "html.parser")
    targets = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if href.startswith("http://") or href.startswith("https://"):
            targets.append(href)
    return targets


def _has_viewport_meta(html: Any) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(str(html), "html.parser")
    return bool(soup.find("meta", attrs={"name": "viewport"}))


def _missing_alt_image_pages(html_series: pd.Series) -> pd.DataFrame:
    page_urls = []
    for url, html in html_series.items():
        if not html:
            continue
        soup = BeautifulSoup(str(html), "html.parser")
        missing_alt = [img for img in soup.find_all("img") if not img.get("alt") or not img.get("alt").strip()]
        if missing_alt:
            page_urls.append(url)
    return pd.DataFrame({"URL": page_urls})


def _grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _catalog_reference(check_name: str) -> Dict[str, Any]:
    catalog_id = CHECK_NAME_TO_CATALOG_ID.get(check_name)
    templated = CHECK_CATALOG_BY_ID.get(catalog_id, {}) if catalog_id else {}
    if not templated:
        templated = FALLBACK_CHECK_CATALOG.get(check_name, {})
    return {
        "category": templated.get("category", "On-Page & Duplicates"),
        "severity": templated.get("severity", "Notice"),
        "notes": templated.get("notes", ""),
    }


def _add_finding(findings: List[Dict[str, Any]], *, category: str, check: str, severity: str, affected_pages: int, total_pages: int, notes: str = ""):
    if affected_pages <= 0 or total_pages <= 0:
        return
    deduction = round((affected_pages / total_pages) * SEVERITY_WEIGHTS[severity], 4)
    findings.append({
        "Category": category,
        "Check": check,
        "Severity": severity,
        "Affected Pages": affected_pages,
        "Deduction": deduction,
        "Impact Score": int(affected_pages * SEVERITY_WEIGHTS[severity]),
        "Notes": notes,
    })


def build_site_health_report(df: pd.DataFrame, site_ctx: Dict[str, Any] = None) -> Dict[str, Any]:
    site_ctx = site_ctx or {}
    if df is None or df.empty:
        return {
            "health_score": 100,
            "grade": "A",
            "pages_crawled": 0,
            "issues_found": 0,
            "checks": pd.DataFrame(columns=["Category", "Check", "Severity", "Affected Pages", "Deduction", "Impact Score", "Notes"]),
            "quick_wins": pd.DataFrame(columns=["Issue", "Impact", "Affected Pages", "Category", "Priority"]),
            "category_scores": pd.DataFrame(columns=["Category", "Weight", "Score"]),
        }

    work_df = df.copy()
    work_df["Content Text"] = work_df.get("Content Text", work_df.get("HTML", "")).fillna("")
    work_df["Body Text"] = work_df["Content Text"].apply(_html_to_text)
    work_df["Content Hash"] = work_df["Body Text"].apply(_content_hash)

    total_pages = len(work_df)
    findings: List[Dict[str, Any]] = []

    dup_titles = work_df[
        work_df.duplicated(subset=["Title"], keep=False)
        & work_df["Title"].astype(str).str.strip().astype(bool)
    ][["URL", "Title"]].drop_duplicates().reset_index(drop=True)

    dup_desc = work_df[
        work_df.duplicated(subset=["Description"], keep=False)
        & work_df["Description"].astype(str).str.strip().astype(bool)
    ][["URL", "Description"]].drop_duplicates().reset_index(drop=True)

    dup_h1 = work_df[
        work_df.duplicated(subset=["H1"], keep=False)
        & work_df["H1"].astype(str).str.strip().astype(bool)
    ][["URL", "H1"]].drop_duplicates().reset_index(drop=True)

    dup_body = work_df[
        work_df["Content Hash"].duplicated(keep=False)
        & work_df["Content Hash"].astype(str).str.strip().astype(bool)
    ][["URL", "Content Hash"]].drop_duplicates().reset_index(drop=True)

    missing_title = work_df[work_df["Title"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_desc = work_df[work_df["Description"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_h1 = work_df[work_df["H1"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_canonical = work_df[work_df["Canonical URL"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    title_too_short = check_C042(work_df)
    title_too_long = check_C043(work_df)
    desc_too_short = check_C046(work_df)
    desc_too_long = check_C047(work_df)
    multiple_h1 = check_C050(work_df)
    missing_lang = check_C059(work_df)
    h1_dup_title = check_C052(work_df)
    url_too_long = check_C062(work_df)
    url_uppercase = check_C065(work_df)
    url_underscores = check_C064(work_df)
    url_excessive_params = check_C061(work_df)
    low_text_ratio = check_C058(work_df)
    thin_content = work_df[work_df["Word Count"].astype(int) < 300][["URL"]].drop_duplicates().reset_index(drop=True)
    slow_pages = work_df[work_df["Crawl Time (s)"].astype(float) > 2.5][["URL"]].drop_duplicates().reset_index(drop=True)
    images_missing_dimensions = check_C123(work_df)
    excessive_dom_size = check_C127(work_df)
    legacy_image_formats = check_C124(work_df)
    broken_heading_hierarchy = check_C060(work_df)
    non_descriptive_url = check_C063(work_df)
    insecure_external_link = check_C082(work_df)
    offsite_image_hosting = check_C086(work_df)
    javascript_void_link = check_C094(work_df)
    excessive_inferred_requests = check_C121(work_df)
    render_blocking_script = check_C122(work_df)
    missing_viewport_mobile = check_C129(work_df)
    form_fields_missing_label = check_C134(work_df)
    noindex_directive = check_C012(work_df)
    meta_nofollow = check_C013(work_df)
    soft_404 = check_C015(work_df)
    cross_domain_canonical = check_C018(work_df)
    mixed_content = check_C023(work_df)
    meta_refresh_redirect = check_C036(work_df)
    trailing_slash_duplicate = check_C037(work_df)
    www_non_www_duplicate = check_C038(work_df)
    excessive_internal_links = check_C070(work_df)
    broken_internal_link = check_C071(work_df)
    internal_link_to_redirect = check_C072(work_df)
    internal_link_nofollow = check_C073(work_df)
    generic_anchor_text = check_C074(work_df)
    broken_canonical_target = check_C088(work_df)
    excessive_outbound_links = check_C092(work_df)
    insecure_form_action = check_C095(work_df)
    invalid_hreflang_code = check_C096(work_df)
    multiple_x_default_hreflang = check_C101(work_df)
    missing_x_default_hreflang = check_C102(work_df)
    duplicate_hreflang = check_C106(work_df)
    not_crawlable = check_C014(work_df)
    canonical_points_to_noindex = check_C017(work_df)
    canonical_chain = check_C019(work_df)
    pagination_signals_missing = check_C020(work_df)
    excessive_click_depth = check_C067(work_df)
    severe_click_depth = check_C068(work_df)
    navigation_link_count_anomaly = check_C077(work_df)
    breadcrumb_missing_on_deep_page = check_C078(work_df)
    pagination_missing_first_last = check_C079(work_df)
    broken_hreflang_target = check_C089(work_df)
    tracking_parameters_in_link = check_C090(work_df)
    hreflang_missing_return_link = check_C097(work_df)
    hreflang_points_to_non_canonical = check_C098(work_df)
    hreflang_points_to_broken_url = check_C100(work_df)
    hreflang_language_conflict = check_C104(work_df)
    structured_data_missing_fields = check_C110(work_df)
    structured_data_type_mismatch = check_C111(work_df)
    unlazy_below_fold_images = check_C125(work_df)
    empty_alt_attribute = check_C131(work_df)
    dense_tap_targets = check_C132(work_df)
    robots_txt_missing = check_C001(work_df, site_ctx=site_ctx)
    robots_txt_invalid = check_C002(work_df, site_ctx=site_ctx)
    robots_txt_blocks_site = check_C003(work_df, site_ctx=site_ctx)
    robots_txt_blocks_assets = check_C004(work_df, site_ctx=site_ctx)
    sitemap_missing = check_C005(work_df, site_ctx=site_ctx)
    sitemap_invalid = check_C006(work_df, site_ctx=site_ctx)
    sitemap_contains_broken_urls = check_C007(work_df, site_ctx=site_ctx)
    sitemap_contains_redirected_urls = check_C008(work_df, site_ctx=site_ctx)
    sitemap_contains_noindex_urls = check_C009(work_df, site_ctx=site_ctx)
    sitemap_not_in_robots = check_C010(work_df, site_ctx=site_ctx)
    no_http_to_https_redirect = check_C024(work_df)
    missing_hsts_header = check_C025(work_df)
    missing_security_headers = check_C030(work_df)
    redirect_loop = check_C032(work_df)
    internal_link_to_redirect_redirects_lens = check_C034(work_df)
    redirect_to_broken_destination = check_C035(work_df)
    multi_hop_https_upgrade = check_C039(work_df)
    anchor_text_mismatch = check_C075(work_df)
    unmarked_affiliate_link = check_C093(work_df)
    hreflang_points_to_redirect = check_C099(work_df)
    conflicting_robots_signals = check_C016(work_df)
    http_urls_in_sitemap = check_C022(work_df, site_ctx=site_ctx)
    ssl_certificate_expired = check_C026(work_df, site_ctx=site_ctx)
    ssl_certificate_expiring_soon = check_C027(work_df, site_ctx=site_ctx)
    ssl_certificate_hostname_mismatch = check_C028(work_df, site_ctx=site_ctx)
    hreflang_cluster_inconsistent = check_C103(work_df)
    hreflang_sitemap_disagreement = check_C105(work_df, site_ctx=site_ctx)
    content_language_mismatch = check_C107(work_df)
    uncompressed_html_response = check_C119(work_df)
    missing_caching_headers = check_C128(work_df)
    broken_external_link = check_C081(work_df, site_ctx=site_ctx)
    external_link_redirect_chain = check_C083(work_df, site_ctx=site_ctx)
    external_resource_blocked_by_robots = check_C084(work_df, site_ctx=site_ctx)
    broken_image_source = check_C085(work_df, site_ctx=site_ctx)
    broken_favicon = check_C087(work_df, site_ctx=site_ctx)
    repeated_dead_outbound_link = check_C091(work_df, site_ctx=site_ctx)
    non_https_pages = work_df[~work_df["URL"].astype(str).str.startswith("https://")][["URL"]].drop_duplicates().reset_index(drop=True)
    redirect_pages = work_df[work_df["Status"].astype(str).str.startswith(("301", "302", "303", "307", "308"))][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_schema = work_df[work_df["Schema"].astype(str).str.strip().eq("")][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_og = work_df[
        work_df["OG Title"].astype(str).str.strip().eq("")
        | work_df["OG Description"].astype(str).str.strip().eq("")
    ][["URL"]].drop_duplicates().reset_index(drop=True)
    pages_with_low_internal_links = work_df[work_df["Internal Links"].astype(int) <= 1][["URL"]].drop_duplicates().reset_index(drop=True)
    missing_viewport = work_df[
        ~work_df["HTML"].fillna("").apply(_has_viewport_meta)
    ][["URL"]].drop_duplicates().reset_index(drop=True)
    pages_missing_alt = _missing_alt_image_pages(work_df.set_index("URL")["HTML"])
    missing_favicon = check_C116(work_df)
    missing_twitter_card = check_C113(work_df)
    invalid_structured_data = check_C109(work_df)

    internal_link_counts: Counter = Counter()
    for html in work_df.get("HTML", pd.Series([""] * len(work_df))).fillna(""):
        internal_link_counts.update(_extract_internal_targets(html))

    orphan_pages = work_df.loc[
        work_df["URL"].astype(str).isin(
            [url for url in work_df["URL"].astype(str) if url not in internal_link_counts]
        )
    ][["URL"]].drop_duplicates().reset_index(drop=True)

    _add_finding(
        findings,
        category=_catalog_reference("Orphan Pages")["category"],
        check="Orphan Pages",
        severity=_catalog_reference("Orphan Pages")["severity"],
        affected_pages=len(orphan_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Orphan Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Non-HTTPS Pages")["category"],
        check="Non-HTTPS Pages",
        severity=_catalog_reference("Non-HTTPS Pages")["severity"],
        affected_pages=len(non_https_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Non-HTTPS Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Redirecting Pages")["category"],
        check="Redirecting Pages",
        severity=_catalog_reference("Redirecting Pages")["severity"],
        affected_pages=len(redirect_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Redirecting Pages")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Titles")["category"],
        check="Duplicate Titles",
        severity=_catalog_reference("Duplicate Titles")["severity"],
        affected_pages=len(dup_titles["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Titles")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Meta Descriptions")["category"],
        check="Duplicate Meta Descriptions",
        severity=_catalog_reference("Duplicate Meta Descriptions")["severity"],
        affected_pages=len(dup_desc["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Meta Descriptions")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate H1 Tags")["category"],
        check="Duplicate H1 Tags",
        severity=_catalog_reference("Duplicate H1 Tags")["severity"],
        affected_pages=len(dup_h1["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate H1 Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Body Content")["category"],
        check="Duplicate Body Content",
        severity=_catalog_reference("Duplicate Body Content")["severity"],
        affected_pages=len(dup_body["URL"].unique()),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Body Content")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Title")["category"],
        check="Missing Title",
        severity=_catalog_reference("Missing Title")["severity"],
        affected_pages=len(missing_title),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Title")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Description")["category"],
        check="Missing Description",
        severity=_catalog_reference("Missing Description")["severity"],
        affected_pages=len(missing_desc),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Description")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing H1")["category"],
        check="Missing H1",
        severity=_catalog_reference("Missing H1")["severity"],
        affected_pages=len(missing_h1),
        total_pages=total_pages,
        notes=_catalog_reference("Missing H1")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Canonical")["category"],
        check="Missing Canonical",
        severity=_catalog_reference("Missing Canonical")["severity"],
        affected_pages=len(missing_canonical),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Canonical")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Title Too Short")["category"],
        check="Title Too Short",
        severity=_catalog_reference("Title Too Short")["severity"],
        affected_pages=len(title_too_short),
        total_pages=total_pages,
        notes=_catalog_reference("Title Too Short")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Title Too Long")["category"],
        check="Title Too Long",
        severity=_catalog_reference("Title Too Long")["severity"],
        affected_pages=len(title_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("Title Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Description Too Short")["category"],
        check="Meta Description Too Short",
        severity=_catalog_reference("Meta Description Too Short")["severity"],
        affected_pages=len(desc_too_short),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Description Too Short")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Description Too Long")["category"],
        check="Meta Description Too Long",
        severity=_catalog_reference("Meta Description Too Long")["severity"],
        affected_pages=len(desc_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Description Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Multiple H1s")["category"],
        check="Multiple H1s",
        severity=_catalog_reference("Multiple H1s")["severity"],
        affected_pages=len(multiple_h1),
        total_pages=total_pages,
        notes=_catalog_reference("Multiple H1s")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Language Declaration")["category"],
        check="Missing Language Declaration",
        severity=_catalog_reference("Missing Language Declaration")["severity"],
        affected_pages=len(missing_lang),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Language Declaration")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("H1 Duplicates Title")["category"],
        check="H1 Duplicates Title",
        severity=_catalog_reference("H1 Duplicates Title")["severity"],
        affected_pages=len(h1_dup_title),
        total_pages=total_pages,
        notes=_catalog_reference("H1 Duplicates Title")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Too Long")["category"],
        check="URL Too Long",
        severity=_catalog_reference("URL Too Long")["severity"],
        affected_pages=len(url_too_long),
        total_pages=total_pages,
        notes=_catalog_reference("URL Too Long")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Contains Uppercase")["category"],
        check="URL Contains Uppercase",
        severity=_catalog_reference("URL Contains Uppercase")["severity"],
        affected_pages=len(url_uppercase),
        total_pages=total_pages,
        notes=_catalog_reference("URL Contains Uppercase")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Contains Underscores")["category"],
        check="URL Contains Underscores",
        severity=_catalog_reference("URL Contains Underscores")["severity"],
        affected_pages=len(url_underscores),
        total_pages=total_pages,
        notes=_catalog_reference("URL Contains Underscores")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("URL Excessive Parameters")["category"],
        check="URL Excessive Parameters",
        severity=_catalog_reference("URL Excessive Parameters")["severity"],
        affected_pages=len(url_excessive_params),
        total_pages=total_pages,
        notes=_catalog_reference("URL Excessive Parameters")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Low Text-to-HTML Ratio")["category"],
        check="Low Text-to-HTML Ratio",
        severity=_catalog_reference("Low Text-to-HTML Ratio")["severity"],
        affected_pages=len(low_text_ratio),
        total_pages=total_pages,
        notes=_catalog_reference("Low Text-to-HTML Ratio")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Thin Content")["category"],
        check="Thin Content",
        severity=_catalog_reference("Thin Content")["severity"],
        affected_pages=len(thin_content),
        total_pages=total_pages,
        notes=_catalog_reference("Thin Content")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Low Internal Link Support")["category"],
        check="Low Internal Link Support",
        severity=_catalog_reference("Low Internal Link Support")["severity"],
        affected_pages=len(pages_with_low_internal_links),
        total_pages=total_pages,
        notes=_catalog_reference("Low Internal Link Support")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Schema")["category"],
        check="Missing Schema",
        severity=_catalog_reference("Missing Schema")["severity"],
        affected_pages=len(missing_schema),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Schema")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Open Graph Tags")["category"],
        check="Missing Open Graph Tags",
        severity=_catalog_reference("Missing Open Graph Tags")["severity"],
        affected_pages=len(missing_og),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Open Graph Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Favicon Link")["category"],
        check="Missing Favicon Link",
        severity=_catalog_reference("Missing Favicon Link")["severity"],
        affected_pages=len(missing_favicon),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Favicon Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Twitter Card Tags")["category"],
        check="Missing Twitter Card Tags",
        severity=_catalog_reference("Missing Twitter Card Tags")["severity"],
        affected_pages=len(missing_twitter_card),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Twitter Card Tags")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Invalid Structured Data")["category"],
        check="Invalid Structured Data",
        severity=_catalog_reference("Invalid Structured Data")["severity"],
        affected_pages=len(invalid_structured_data),
        total_pages=total_pages,
        notes=_catalog_reference("Invalid Structured Data")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Slow Response Time")["category"],
        check="Slow Response Time",
        severity=_catalog_reference("Slow Response Time")["severity"],
        affected_pages=len(slow_pages),
        total_pages=total_pages,
        notes=_catalog_reference("Slow Response Time")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Images Missing Dimensions")["category"],
        check="Images Missing Dimensions",
        severity=_catalog_reference("Images Missing Dimensions")["severity"],
        affected_pages=len(images_missing_dimensions),
        total_pages=total_pages,
        notes=_catalog_reference("Images Missing Dimensions")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive DOM Size")["category"],
        check="Excessive DOM Size",
        severity=_catalog_reference("Excessive DOM Size")["severity"],
        affected_pages=len(excessive_dom_size),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive DOM Size")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Legacy Image Formats")["category"],
        check="Legacy Image Formats",
        severity=_catalog_reference("Legacy Image Formats")["severity"],
        affected_pages=len(legacy_image_formats),
        total_pages=total_pages,
        notes=_catalog_reference("Legacy Image Formats")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Heading Hierarchy")["category"],
        check="Broken Heading Hierarchy",
        severity=_catalog_reference("Broken Heading Hierarchy")["severity"],
        affected_pages=len(broken_heading_hierarchy),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Heading Hierarchy")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Non-Descriptive URL")["category"],
        check="Non-Descriptive URL",
        severity=_catalog_reference("Non-Descriptive URL")["severity"],
        affected_pages=len(non_descriptive_url),
        total_pages=total_pages,
        notes=_catalog_reference("Non-Descriptive URL")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Insecure External Link")["category"],
        check="Insecure External Link",
        severity=_catalog_reference("Insecure External Link")["severity"],
        affected_pages=len(insecure_external_link),
        total_pages=total_pages,
        notes=_catalog_reference("Insecure External Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Offsite Image Hosting")["category"],
        check="Offsite Image Hosting",
        severity=_catalog_reference("Offsite Image Hosting")["severity"],
        affected_pages=len(offsite_image_hosting),
        total_pages=total_pages,
        notes=_catalog_reference("Offsite Image Hosting")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("JavaScript Void Link")["category"],
        check="JavaScript Void Link",
        severity=_catalog_reference("JavaScript Void Link")["severity"],
        affected_pages=len(javascript_void_link),
        total_pages=total_pages,
        notes=_catalog_reference("JavaScript Void Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive Inferred Requests")["category"],
        check="Excessive Inferred Requests",
        severity=_catalog_reference("Excessive Inferred Requests")["severity"],
        affected_pages=len(excessive_inferred_requests),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive Inferred Requests")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Render-Blocking Script")["category"],
        check="Render-Blocking Script",
        severity=_catalog_reference("Render-Blocking Script")["severity"],
        affected_pages=len(render_blocking_script),
        total_pages=total_pages,
        notes=_catalog_reference("Render-Blocking Script")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Viewport Meta (Mobile)")["category"],
        check="Missing Viewport Meta (Mobile)",
        severity=_catalog_reference("Missing Viewport Meta (Mobile)")["severity"],
        affected_pages=len(missing_viewport_mobile),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Viewport Meta (Mobile)")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Form Fields Missing Label")["category"],
        check="Form Fields Missing Label",
        severity=_catalog_reference("Form Fields Missing Label")["severity"],
        affected_pages=len(form_fields_missing_label),
        total_pages=total_pages,
        notes=_catalog_reference("Form Fields Missing Label")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Noindex Directive")["category"],
        check="Noindex Directive",
        severity=_catalog_reference("Noindex Directive")["severity"],
        affected_pages=len(noindex_directive),
        total_pages=total_pages,
        notes=_catalog_reference("Noindex Directive")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Nofollow")["category"],
        check="Meta Nofollow",
        severity=_catalog_reference("Meta Nofollow")["severity"],
        affected_pages=len(meta_nofollow),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Nofollow")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Soft 404")["category"],
        check="Soft 404",
        severity=_catalog_reference("Soft 404")["severity"],
        affected_pages=len(soft_404),
        total_pages=total_pages,
        notes=_catalog_reference("Soft 404")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Cross-Domain Canonical")["category"],
        check="Cross-Domain Canonical",
        severity=_catalog_reference("Cross-Domain Canonical")["severity"],
        affected_pages=len(cross_domain_canonical),
        total_pages=total_pages,
        notes=_catalog_reference("Cross-Domain Canonical")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Mixed Content")["category"],
        check="Mixed Content",
        severity=_catalog_reference("Mixed Content")["severity"],
        affected_pages=len(mixed_content),
        total_pages=total_pages,
        notes=_catalog_reference("Mixed Content")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Meta Refresh Redirect")["category"],
        check="Meta Refresh Redirect",
        severity=_catalog_reference("Meta Refresh Redirect")["severity"],
        affected_pages=len(meta_refresh_redirect),
        total_pages=total_pages,
        notes=_catalog_reference("Meta Refresh Redirect")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Trailing Slash Duplicate")["category"],
        check="Trailing Slash Duplicate",
        severity=_catalog_reference("Trailing Slash Duplicate")["severity"],
        affected_pages=len(trailing_slash_duplicate),
        total_pages=total_pages,
        notes=_catalog_reference("Trailing Slash Duplicate")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("WWW Non-WWW Duplicate")["category"],
        check="WWW Non-WWW Duplicate",
        severity=_catalog_reference("WWW Non-WWW Duplicate")["severity"],
        affected_pages=len(www_non_www_duplicate),
        total_pages=total_pages,
        notes=_catalog_reference("WWW Non-WWW Duplicate")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive Internal Links")["category"],
        check="Excessive Internal Links",
        severity=_catalog_reference("Excessive Internal Links")["severity"],
        affected_pages=len(excessive_internal_links),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive Internal Links")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Internal Link")["category"],
        check="Broken Internal Link",
        severity=_catalog_reference("Broken Internal Link")["severity"],
        affected_pages=len(broken_internal_link),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Internal Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Internal Link To Redirect")["category"],
        check="Internal Link To Redirect",
        severity=_catalog_reference("Internal Link To Redirect")["severity"],
        affected_pages=len(internal_link_to_redirect),
        total_pages=total_pages,
        notes=_catalog_reference("Internal Link To Redirect")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Internal Link Nofollow")["category"],
        check="Internal Link Nofollow",
        severity=_catalog_reference("Internal Link Nofollow")["severity"],
        affected_pages=len(internal_link_nofollow),
        total_pages=total_pages,
        notes=_catalog_reference("Internal Link Nofollow")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Generic Anchor Text")["category"],
        check="Generic Anchor Text",
        severity=_catalog_reference("Generic Anchor Text")["severity"],
        affected_pages=len(generic_anchor_text),
        total_pages=total_pages,
        notes=_catalog_reference("Generic Anchor Text")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Canonical Target")["category"],
        check="Broken Canonical Target",
        severity=_catalog_reference("Broken Canonical Target")["severity"],
        affected_pages=len(broken_canonical_target),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Canonical Target")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive Outbound Links")["category"],
        check="Excessive Outbound Links",
        severity=_catalog_reference("Excessive Outbound Links")["severity"],
        affected_pages=len(excessive_outbound_links),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive Outbound Links")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Insecure Form Action")["category"],
        check="Insecure Form Action",
        severity=_catalog_reference("Insecure Form Action")["severity"],
        affected_pages=len(insecure_form_action),
        total_pages=total_pages,
        notes=_catalog_reference("Insecure Form Action")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Invalid Hreflang Code")["category"],
        check="Invalid Hreflang Code",
        severity=_catalog_reference("Invalid Hreflang Code")["severity"],
        affected_pages=len(invalid_hreflang_code),
        total_pages=total_pages,
        notes=_catalog_reference("Invalid Hreflang Code")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Multiple X-Default Hreflang")["category"],
        check="Multiple X-Default Hreflang",
        severity=_catalog_reference("Multiple X-Default Hreflang")["severity"],
        affected_pages=len(multiple_x_default_hreflang),
        total_pages=total_pages,
        notes=_catalog_reference("Multiple X-Default Hreflang")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing X-Default Hreflang")["category"],
        check="Missing X-Default Hreflang",
        severity=_catalog_reference("Missing X-Default Hreflang")["severity"],
        affected_pages=len(missing_x_default_hreflang),
        total_pages=total_pages,
        notes=_catalog_reference("Missing X-Default Hreflang")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Duplicate Hreflang")["category"],
        check="Duplicate Hreflang",
        severity=_catalog_reference("Duplicate Hreflang")["severity"],
        affected_pages=len(duplicate_hreflang),
        total_pages=total_pages,
        notes=_catalog_reference("Duplicate Hreflang")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Not Crawlable")["category"],
        check="Not Crawlable",
        severity=_catalog_reference("Not Crawlable")["severity"],
        affected_pages=len(not_crawlable),
        total_pages=total_pages,
        notes=_catalog_reference("Not Crawlable")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Canonical Points To Noindex")["category"],
        check="Canonical Points To Noindex",
        severity=_catalog_reference("Canonical Points To Noindex")["severity"],
        affected_pages=len(canonical_points_to_noindex),
        total_pages=total_pages,
        notes=_catalog_reference("Canonical Points To Noindex")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Canonical Chain")["category"],
        check="Canonical Chain",
        severity=_catalog_reference("Canonical Chain")["severity"],
        affected_pages=len(canonical_chain),
        total_pages=total_pages,
        notes=_catalog_reference("Canonical Chain")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Pagination Signals Missing")["category"],
        check="Pagination Signals Missing",
        severity=_catalog_reference("Pagination Signals Missing")["severity"],
        affected_pages=len(pagination_signals_missing),
        total_pages=total_pages,
        notes=_catalog_reference("Pagination Signals Missing")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Excessive Click Depth")["category"],
        check="Excessive Click Depth",
        severity=_catalog_reference("Excessive Click Depth")["severity"],
        affected_pages=len(excessive_click_depth),
        total_pages=total_pages,
        notes=_catalog_reference("Excessive Click Depth")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Severe Click Depth")["category"],
        check="Severe Click Depth",
        severity=_catalog_reference("Severe Click Depth")["severity"],
        affected_pages=len(severe_click_depth),
        total_pages=total_pages,
        notes=_catalog_reference("Severe Click Depth")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Navigation Link Count Anomaly")["category"],
        check="Navigation Link Count Anomaly",
        severity=_catalog_reference("Navigation Link Count Anomaly")["severity"],
        affected_pages=len(navigation_link_count_anomaly),
        total_pages=total_pages,
        notes=_catalog_reference("Navigation Link Count Anomaly")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Breadcrumb Missing On Deep Page")["category"],
        check="Breadcrumb Missing On Deep Page",
        severity=_catalog_reference("Breadcrumb Missing On Deep Page")["severity"],
        affected_pages=len(breadcrumb_missing_on_deep_page),
        total_pages=total_pages,
        notes=_catalog_reference("Breadcrumb Missing On Deep Page")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Pagination Missing First/Last")["category"],
        check="Pagination Missing First/Last",
        severity=_catalog_reference("Pagination Missing First/Last")["severity"],
        affected_pages=len(pagination_missing_first_last),
        total_pages=total_pages,
        notes=_catalog_reference("Pagination Missing First/Last")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Hreflang Target")["category"],
        check="Broken Hreflang Target",
        severity=_catalog_reference("Broken Hreflang Target")["severity"],
        affected_pages=len(broken_hreflang_target),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Hreflang Target")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Tracking Parameters In Link")["category"],
        check="Tracking Parameters In Link",
        severity=_catalog_reference("Tracking Parameters In Link")["severity"],
        affected_pages=len(tracking_parameters_in_link),
        total_pages=total_pages,
        notes=_catalog_reference("Tracking Parameters In Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Missing Return Link")["category"],
        check="Hreflang Missing Return Link",
        severity=_catalog_reference("Hreflang Missing Return Link")["severity"],
        affected_pages=len(hreflang_missing_return_link),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Missing Return Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Points To Non-Canonical")["category"],
        check="Hreflang Points To Non-Canonical",
        severity=_catalog_reference("Hreflang Points To Non-Canonical")["severity"],
        affected_pages=len(hreflang_points_to_non_canonical),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Points To Non-Canonical")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Points To Broken URL")["category"],
        check="Hreflang Points To Broken URL",
        severity=_catalog_reference("Hreflang Points To Broken URL")["severity"],
        affected_pages=len(hreflang_points_to_broken_url),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Points To Broken URL")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Language Conflict")["category"],
        check="Hreflang Language Conflict",
        severity=_catalog_reference("Hreflang Language Conflict")["severity"],
        affected_pages=len(hreflang_language_conflict),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Language Conflict")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Structured Data Missing Fields")["category"],
        check="Structured Data Missing Fields",
        severity=_catalog_reference("Structured Data Missing Fields")["severity"],
        affected_pages=len(structured_data_missing_fields),
        total_pages=total_pages,
        notes=_catalog_reference("Structured Data Missing Fields")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Structured Data Type Mismatch")["category"],
        check="Structured Data Type Mismatch",
        severity=_catalog_reference("Structured Data Type Mismatch")["severity"],
        affected_pages=len(structured_data_type_mismatch),
        total_pages=total_pages,
        notes=_catalog_reference("Structured Data Type Mismatch")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Unlazy Below-Fold Images")["category"],
        check="Unlazy Below-Fold Images",
        severity=_catalog_reference("Unlazy Below-Fold Images")["severity"],
        affected_pages=len(unlazy_below_fold_images),
        total_pages=total_pages,
        notes=_catalog_reference("Unlazy Below-Fold Images")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Empty Alt Attribute")["category"],
        check="Empty Alt Attribute",
        severity=_catalog_reference("Empty Alt Attribute")["severity"],
        affected_pages=len(empty_alt_attribute),
        total_pages=total_pages,
        notes=_catalog_reference("Empty Alt Attribute")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Dense Tap Targets")["category"],
        check="Dense Tap Targets",
        severity=_catalog_reference("Dense Tap Targets")["severity"],
        affected_pages=len(dense_tap_targets),
        total_pages=total_pages,
        notes=_catalog_reference("Dense Tap Targets")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Robots Txt Missing")["category"],
        check="Robots Txt Missing",
        severity=_catalog_reference("Robots Txt Missing")["severity"],
        affected_pages=len(robots_txt_missing),
        total_pages=total_pages,
        notes=_catalog_reference("Robots Txt Missing")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Robots Txt Invalid")["category"],
        check="Robots Txt Invalid",
        severity=_catalog_reference("Robots Txt Invalid")["severity"],
        affected_pages=len(robots_txt_invalid),
        total_pages=total_pages,
        notes=_catalog_reference("Robots Txt Invalid")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Robots Txt Blocks Site")["category"],
        check="Robots Txt Blocks Site",
        severity=_catalog_reference("Robots Txt Blocks Site")["severity"],
        affected_pages=len(robots_txt_blocks_site),
        total_pages=total_pages,
        notes=_catalog_reference("Robots Txt Blocks Site")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Robots Txt Blocks Assets")["category"],
        check="Robots Txt Blocks Assets",
        severity=_catalog_reference("Robots Txt Blocks Assets")["severity"],
        affected_pages=len(robots_txt_blocks_assets),
        total_pages=total_pages,
        notes=_catalog_reference("Robots Txt Blocks Assets")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Missing")["category"],
        check="Sitemap Missing",
        severity=_catalog_reference("Sitemap Missing")["severity"],
        affected_pages=len(sitemap_missing),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Missing")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Invalid")["category"],
        check="Sitemap Invalid",
        severity=_catalog_reference("Sitemap Invalid")["severity"],
        affected_pages=len(sitemap_invalid),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Invalid")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Contains Broken URLs")["category"],
        check="Sitemap Contains Broken URLs",
        severity=_catalog_reference("Sitemap Contains Broken URLs")["severity"],
        affected_pages=len(sitemap_contains_broken_urls),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Contains Broken URLs")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Contains Redirected URLs")["category"],
        check="Sitemap Contains Redirected URLs",
        severity=_catalog_reference("Sitemap Contains Redirected URLs")["severity"],
        affected_pages=len(sitemap_contains_redirected_urls),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Contains Redirected URLs")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Contains Noindex URLs")["category"],
        check="Sitemap Contains Noindex URLs",
        severity=_catalog_reference("Sitemap Contains Noindex URLs")["severity"],
        affected_pages=len(sitemap_contains_noindex_urls),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Contains Noindex URLs")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Sitemap Not In Robots")["category"],
        check="Sitemap Not In Robots",
        severity=_catalog_reference("Sitemap Not In Robots")["severity"],
        affected_pages=len(sitemap_not_in_robots),
        total_pages=total_pages,
        notes=_catalog_reference("Sitemap Not In Robots")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("No HTTP-To-HTTPS Redirect")["category"],
        check="No HTTP-To-HTTPS Redirect",
        severity=_catalog_reference("No HTTP-To-HTTPS Redirect")["severity"],
        affected_pages=len(no_http_to_https_redirect),
        total_pages=total_pages,
        notes=_catalog_reference("No HTTP-To-HTTPS Redirect")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing HSTS Header")["category"],
        check="Missing HSTS Header",
        severity=_catalog_reference("Missing HSTS Header")["severity"],
        affected_pages=len(missing_hsts_header),
        total_pages=total_pages,
        notes=_catalog_reference("Missing HSTS Header")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Security Headers")["category"],
        check="Missing Security Headers",
        severity=_catalog_reference("Missing Security Headers")["severity"],
        affected_pages=len(missing_security_headers),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Security Headers")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Redirect Loop")["category"],
        check="Redirect Loop",
        severity=_catalog_reference("Redirect Loop")["severity"],
        affected_pages=len(redirect_loop),
        total_pages=total_pages,
        notes=_catalog_reference("Redirect Loop")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Internal Link To Redirect (Redirects Lens)")["category"],
        check="Internal Link To Redirect (Redirects Lens)",
        severity=_catalog_reference("Internal Link To Redirect (Redirects Lens)")["severity"],
        affected_pages=len(internal_link_to_redirect_redirects_lens),
        total_pages=total_pages,
        notes=_catalog_reference("Internal Link To Redirect (Redirects Lens)")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Redirect To Broken Destination")["category"],
        check="Redirect To Broken Destination",
        severity=_catalog_reference("Redirect To Broken Destination")["severity"],
        affected_pages=len(redirect_to_broken_destination),
        total_pages=total_pages,
        notes=_catalog_reference("Redirect To Broken Destination")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Multi-Hop HTTPS Upgrade")["category"],
        check="Multi-Hop HTTPS Upgrade",
        severity=_catalog_reference("Multi-Hop HTTPS Upgrade")["severity"],
        affected_pages=len(multi_hop_https_upgrade),
        total_pages=total_pages,
        notes=_catalog_reference("Multi-Hop HTTPS Upgrade")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Anchor Text Mismatch")["category"],
        check="Anchor Text Mismatch",
        severity=_catalog_reference("Anchor Text Mismatch")["severity"],
        affected_pages=len(anchor_text_mismatch),
        total_pages=total_pages,
        notes=_catalog_reference("Anchor Text Mismatch")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Unmarked Affiliate Link")["category"],
        check="Unmarked Affiliate Link",
        severity=_catalog_reference("Unmarked Affiliate Link")["severity"],
        affected_pages=len(unmarked_affiliate_link),
        total_pages=total_pages,
        notes=_catalog_reference("Unmarked Affiliate Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Points To Redirect")["category"],
        check="Hreflang Points To Redirect",
        severity=_catalog_reference("Hreflang Points To Redirect")["severity"],
        affected_pages=len(hreflang_points_to_redirect),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Points To Redirect")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Conflicting Robots Signals")["category"],
        check="Conflicting Robots Signals",
        severity=_catalog_reference("Conflicting Robots Signals")["severity"],
        affected_pages=len(conflicting_robots_signals),
        total_pages=total_pages,
        notes=_catalog_reference("Conflicting Robots Signals")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("HTTP URLs In Sitemap")["category"],
        check="HTTP URLs In Sitemap",
        severity=_catalog_reference("HTTP URLs In Sitemap")["severity"],
        affected_pages=len(http_urls_in_sitemap),
        total_pages=total_pages,
        notes=_catalog_reference("HTTP URLs In Sitemap")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("SSL Certificate Expired")["category"],
        check="SSL Certificate Expired",
        severity=_catalog_reference("SSL Certificate Expired")["severity"],
        affected_pages=len(ssl_certificate_expired),
        total_pages=total_pages,
        notes=_catalog_reference("SSL Certificate Expired")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("SSL Certificate Expiring Soon")["category"],
        check="SSL Certificate Expiring Soon",
        severity=_catalog_reference("SSL Certificate Expiring Soon")["severity"],
        affected_pages=len(ssl_certificate_expiring_soon),
        total_pages=total_pages,
        notes=_catalog_reference("SSL Certificate Expiring Soon")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("SSL Certificate Hostname Mismatch")["category"],
        check="SSL Certificate Hostname Mismatch",
        severity=_catalog_reference("SSL Certificate Hostname Mismatch")["severity"],
        affected_pages=len(ssl_certificate_hostname_mismatch),
        total_pages=total_pages,
        notes=_catalog_reference("SSL Certificate Hostname Mismatch")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Cluster Inconsistent")["category"],
        check="Hreflang Cluster Inconsistent",
        severity=_catalog_reference("Hreflang Cluster Inconsistent")["severity"],
        affected_pages=len(hreflang_cluster_inconsistent),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Cluster Inconsistent")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Hreflang Sitemap Disagreement")["category"],
        check="Hreflang Sitemap Disagreement",
        severity=_catalog_reference("Hreflang Sitemap Disagreement")["severity"],
        affected_pages=len(hreflang_sitemap_disagreement),
        total_pages=total_pages,
        notes=_catalog_reference("Hreflang Sitemap Disagreement")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Content Language Mismatch")["category"],
        check="Content Language Mismatch",
        severity=_catalog_reference("Content Language Mismatch")["severity"],
        affected_pages=len(content_language_mismatch),
        total_pages=total_pages,
        notes=_catalog_reference("Content Language Mismatch")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Uncompressed HTML Response")["category"],
        check="Uncompressed HTML Response",
        severity=_catalog_reference("Uncompressed HTML Response")["severity"],
        affected_pages=len(uncompressed_html_response),
        total_pages=total_pages,
        notes=_catalog_reference("Uncompressed HTML Response")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Caching Headers")["category"],
        check="Missing Caching Headers",
        severity=_catalog_reference("Missing Caching Headers")["severity"],
        affected_pages=len(missing_caching_headers),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Caching Headers")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken External Link")["category"],
        check="Broken External Link",
        severity=_catalog_reference("Broken External Link")["severity"],
        affected_pages=len(broken_external_link),
        total_pages=total_pages,
        notes=_catalog_reference("Broken External Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("External Link Redirect Chain")["category"],
        check="External Link Redirect Chain",
        severity=_catalog_reference("External Link Redirect Chain")["severity"],
        affected_pages=len(external_link_redirect_chain),
        total_pages=total_pages,
        notes=_catalog_reference("External Link Redirect Chain")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("External Resource Blocked By Robots")["category"],
        check="External Resource Blocked By Robots",
        severity=_catalog_reference("External Resource Blocked By Robots")["severity"],
        affected_pages=len(external_resource_blocked_by_robots),
        total_pages=total_pages,
        notes=_catalog_reference("External Resource Blocked By Robots")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Image Source")["category"],
        check="Broken Image Source",
        severity=_catalog_reference("Broken Image Source")["severity"],
        affected_pages=len(broken_image_source),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Image Source")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Broken Favicon")["category"],
        check="Broken Favicon",
        severity=_catalog_reference("Broken Favicon")["severity"],
        affected_pages=len(broken_favicon),
        total_pages=total_pages,
        notes=_catalog_reference("Broken Favicon")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Repeated Dead Outbound Link")["category"],
        check="Repeated Dead Outbound Link",
        severity=_catalog_reference("Repeated Dead Outbound Link")["severity"],
        affected_pages=len(repeated_dead_outbound_link),
        total_pages=total_pages,
        notes=_catalog_reference("Repeated Dead Outbound Link")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Missing Viewport Meta")["category"],
        check="Missing Viewport Meta",
        severity=_catalog_reference("Missing Viewport Meta")["severity"],
        affected_pages=len(missing_viewport),
        total_pages=total_pages,
        notes=_catalog_reference("Missing Viewport Meta")["notes"],
    )
    _add_finding(
        findings,
        category=_catalog_reference("Images Missing Alt Text")["category"],
        check="Images Missing Alt Text",
        severity=_catalog_reference("Images Missing Alt Text")["severity"],
        affected_pages=len(pages_missing_alt),
        total_pages=total_pages,
        notes=_catalog_reference("Images Missing Alt Text")["notes"],
    )

    checks_df = pd.DataFrame(findings)
    if checks_df.empty:
        checks_df = pd.DataFrame(columns=["Category", "Check", "Severity", "Affected Pages", "Deduction", "Impact Score", "Notes"])

    category_scores = []
    for category, weight in CATEGORY_WEIGHTS.items():
        category_checks = checks_df[checks_df["Category"] == category]
        if category_checks.empty:
            score = 100
        else:
            average_deduction = category_checks["Deduction"].mean()
            score = int(max(0, min(100, round(100 - (average_deduction * 100), 1))))
        category_scores.append({"Category": category, "Weight": weight, "Score": score, "Label": CATEGORY_LABELS[category]})

    category_scores_df = pd.DataFrame(category_scores)
    weighted_total = sum((row["Score"] * row["Weight"]) for _, row in category_scores_df.iterrows())
    health_score = int(round(weighted_total / sum(CATEGORY_WEIGHTS.values())))
    grade = _grade_for_score(health_score)

    quick_wins = checks_df.sort_values(["Impact Score", "Affected Pages"], ascending=False).reset_index(drop=True)
    quick_wins = quick_wins[["Check", "Impact Score", "Affected Pages", "Category"]].rename(
        columns={"Check": "Issue", "Impact Score": "Impact", "Affected Pages": "Affected Pages", "Category": "Category"}
    )
    quick_wins.insert(len(quick_wins.columns), "Priority", range(1, len(quick_wins) + 1))

    if quick_wins.empty:
        quick_wins = pd.DataFrame(columns=["Issue", "Impact", "Affected Pages", "Category", "Priority"])

    findings_count = len(checks_df)

    return {
        "health_score": health_score,
        "grade": grade,
        "pages_crawled": total_pages,
        "issues_found": findings_count,
        "checks": checks_df,
        "quick_wins": quick_wins,
        "category_scores": category_scores_df,
        "duplicate_titles": dup_titles,
        "duplicate_descriptions": dup_desc,
        "duplicate_h1": dup_h1,
        "duplicate_body_content": dup_body,
        "orphan_pages": orphan_pages,
    }


def render_streamlit_health_score_ui(st, df: pd.DataFrame, site_ctx: Dict[str, Any] = None):
    st.subheader("🩺 Site Health")
    st.markdown("WEM-style site health scoring built from category deductions, quick wins, and site-wide crawl patterns.")

    report = build_site_health_report(df, site_ctx=site_ctx)
    health_score = report["health_score"]

    score_col, grade_col, pages_col, issues_col = st.columns(4)
    with score_col:
        st.metric("Health Score", health_score)
    with grade_col:
        st.metric("Grade", report["grade"])
    with pages_col:
        st.metric("Pages Crawled", report["pages_crawled"])
    with issues_col:
        st.metric("Issues Found", report["issues_found"])

    st.progress(min(1.0, max(0.0, health_score / 100)))

    st.markdown("---")
    health_tab1, health_tab2, health_tab3 = st.tabs(["Health Score", "Quick Wins", "Category Breakdown"])

    with health_tab1:
        st.markdown(
            f"The current site health score is {health_score}/100, which maps to a grade of **{report['grade']}**."
        )
        st.caption(
            "This score is derived from the WEM-style weighted model: category-level penalties are averaged and then combined into one overall health score."
        )
        st.dataframe(report["category_scores"], use_container_width=True)

    with health_tab2:
        if report["quick_wins"].empty:
            st.success("No quick wins detected in this crawl pass.")
        else:
            st.dataframe(report["quick_wins"], use_container_width=True)

    with health_tab3:
        st.dataframe(report["checks"], use_container_width=True)
