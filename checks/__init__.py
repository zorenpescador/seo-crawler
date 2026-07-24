"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 36 checks directly (see CHECK_NAME_TO_CATALOG_ID
there, including the title/description length, multiple-H1, missing
html-lang, H1-duplicates-title, URL-too-long, URL-contains-uppercase,
URL-contains-underscores, URL-excessive-parameters, and low-text-to-html-
ratio checks in checks/on_page.py; the missing-favicon-link,
missing-twitter-card, and invalid-structured-data checks in
checks/markup.py; and the images-missing-dimensions, excessive-dom-size,
and legacy-image-formats checks in checks/performance.py) plus the
aggregate score/category-scores/quick-wins rows (C136, C137, C139). The
remaining 99 checks in checks_catalog.csv have a placeholder function
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
