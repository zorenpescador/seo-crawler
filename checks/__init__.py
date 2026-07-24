"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 115 checks directly (see CHECK_NAME_TO_CATALOG_ID
there for the full list — spread across every checks/*.py module).
site_ctx now also carries a one-time TLS handshake result (ssl_info:
cert expiry, hostname match) and per-URL sitemap hreflang annotations,
alongside robots.txt text and the sitemap URL list — see
fetch_site_context() and fetch_ssl_info() in main.py. What's left is
almost entirely checks needing external HTTP requests to third-party
domains discovered via links/images (broken external links, external
redirect chains, blocked-by-robots external resources, broken images,
broken favicons) — the catalog itself flags these as an opt-in, slower
mode (a --check-external-links style flag), which the crawler doesn't
have a UI toggle for yet. The remaining 20 checks in checks_catalog.csv
have a placeholder function here, grouped by category into one module
per file.

Each stub has the signature (pages_df, site_ctx) -> None and raises
NotImplementedError. site_ctx carries the site-level data fetched once
per crawl (robots.txt text, sitemap URL list, sitemap hreflang, TLS
info) — see fetch_site_context() in main.py for what it contains.

To implement a check: write the real function body in the relevant category
module, then wire its check_id into health_score.CHECK_NAME_TO_CATALOG_ID (or
extend the registry runner, once one exists) so it feeds the health score.
"""
from . import (
    architecture,
    crawlability,
    international,
    links,
    markup,
    mobile,
    on_page,
    performance,
    redirects,
    security,
)

PENDING_CHECKS = {
    **crawlability.CHECKS,
    **security.CHECKS,
    **redirects.CHECKS,
    **on_page.CHECKS,
    **architecture.CHECKS,
    **links.CHECKS,
    **international.CHECKS,
    **markup.CHECKS,
    **performance.CHECKS,
    **mobile.CHECKS,
}
