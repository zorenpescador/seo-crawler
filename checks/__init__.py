"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 18 checks directly (see CHECK_NAME_TO_CATALOG_ID
there) plus the aggregate score/category-scores/quick-wins rows (C136, C137,
C139). Everything else in checks_catalog.csv (117 checks) has a placeholder
function here, grouped by category into one module per file.

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
