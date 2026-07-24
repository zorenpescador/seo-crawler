"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 85 checks directly (see CHECK_NAME_TO_CATALOG_ID
there for the full list — spread across every checks/*.py module). What's
left mostly needs capability the crawler doesn't have yet: robots.txt/
sitemap fetches, SSL/TLS inspection, HTTP response headers, external link
requests, or a real redirect-status pipeline (the crawler currently
follows redirects transparently via requests' default allow_redirects,
so 3XX-dependent checks can't see intermediate hop statuses). The
remaining 50 checks in checks_catalog.csv have a placeholder function
here, grouped by category into one module per file.

Each stub has the signature (pages_df, site_ctx) -> None and raises
NotImplementedError. site_ctx is a placeholder for site-level data the
crawler doesn't collect yet (robots.txt text, sitemap tree, TLS info, etc.).

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
