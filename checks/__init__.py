"""Registry of stubbed checks_catalog.csv checks awaiting implementation.

health_score.py implements 121 checks directly (see CHECK_NAME_TO_CATALOG_ID
there for the full list — spread across every checks/*.py module).

The crawler has an opt-in "Check external links" checkbox (off by
default, since it makes requests to third-party domains discovered via
links/images and is noticeably slower). When enabled, crawl_site() calls
check_external_resources() once after the main crawl to probe external
links, images, and the favicon (capped at 50 links / 30 images, deduped),
populating site_ctx with external_link_status/_redirected/
_robots_blocked, image_status, and favicon_status/_url. That unlocked
C081/C083/C084/C085/C087/C091 in checks/links.py. When the checkbox is
off, those checks see empty site_ctx data and correctly find nothing.

The remaining 14 checks in checks_catalog.csv are the ones already ruled
out as redundant, ambiguous, architecturally impossible, needing an
external API, or (for TLS protocol version enumeration) too fragile
across OpenSSL/Python versions to trust. They have a placeholder function
here, grouped by category into one module per file.

Each stub has the signature (pages_df, site_ctx) -> None and raises
NotImplementedError. site_ctx carries the site-level data fetched once
per crawl (robots.txt text, sitemap URL list, sitemap hreflang, TLS info,
and — when external-link checking is on — the external link/image/
favicon probe results) — see fetch_site_context() and
check_external_resources() in main.py for what it contains.

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
