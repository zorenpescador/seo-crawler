"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 105 checks directly (see CHECK_NAME_TO_CATALOG_ID
there for the full list — spread across every checks/*.py module). The
crawler now fetches robots.txt/sitemap.xml once per crawl (cached in
st.session_state.crawl_metadata as site_ctx, not re-fetched on Streamlit
reruns), captures response headers, and records real 3XX status codes
plus a Redirect Target — which unlocked the C001-C010 robots/sitemap
checks, the header-based security checks, and the redirect-chain checks.
What's left mostly needs capability the crawler still doesn't have: SSL/
TLS inspection (a live handshake per domain) and external HTTP requests
(checking whether external links/images/favicons actually resolve). The
remaining 30 checks in checks_catalog.csv have a placeholder function
here, grouped by category into one module per file.

Each stub has the signature (pages_df, site_ctx) -> None and raises
NotImplementedError. site_ctx carries the site-level data fetched once
per crawl (robots.txt text, sitemap URL list) — see fetch_site_context()
in main.py for what it contains.

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
