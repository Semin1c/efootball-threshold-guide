# Delivery verification

Reviewed 27 September 2026 (America/Los_Angeles).

## Passed

- Data validation: 11 positions, 26 trainable attributes and all 286 position/attribute combinations; unique keys, valid confidence/source references, explicit null targets and numeric range bounds.
- JavaScript syntax check.
- Offline source-monitor regression checks: initial baseline, unchanged source, changed source and failed fetch. Failed fetches retain previous accepted content. Neither checks nor candidate generation alter the chart or accepted baseline.
- Browser: source JSON loads, current-test confidence filter isolates Speed, row expansion exposes source and scope, GK / GK Reflexes displays 90–97, CB / Defensive Awareness displays 93–99.
- Combined filters produce a meaningful empty state; Clear filters restores results. Search for “stride” isolates the acceleration entry. Query filters survive reload.
- Role-priority ordering places core goalkeeper attributes first. Native phone position selector and wider-screen position buttons work.
- Memory aid expands and collapses. Enter expands a focused attribute row.
- Responsive verification: 390 × 844 phone, 820 × 1180 tablet and 1440 × 1000 laptop. No page horizontal overflow at those widths; an additional 320px width check also passed. Screenshots inspected at phone, tablet and laptop sizes. Phone’s first attribute begins within the initial 844px viewport.
- Browser error log was empty on the checked final page.

## Live source-monitor result

With the operating system’s trusted CA bundle, four KONAMI pages were fetched successfully and correctly reported BASELINE_NEEDED. Nine Reddit URLs returned fetch failures and were flagged rather than silently treated as unchanged. These direct-fetch restrictions are separate from the public pages reviewed through web search/open tools for the research.

The packaged monitor starts without an accepted baseline. Its README explains the first review and explicit acceptance step. The weekly workflow remains a file until installed and enabled in a GitHub repository. No remote scheduler has been started.

## Limits

This was browser viewport testing, not testing on physical iPhones/iPads or a complete cross-browser/accessibility audit. No gameplay experiments were performed. GitHub Pages and Netlify configuration is included but no live account deployment was performed. The app requires HTTP(S) to load its separate JSON; file-double-click and offline persistence are not supported. Some monitoring sources may require manual review because automated access is blocked.

## Automatic provisional-feed upgrade — 28 September 2026

Added an independently loaded provisional feed and source-health display. The existing chart remains usable if that feed fails. Extracted text is escaped before rendering and external links are restricted to vetted HTTPS hosts.

Regression checks cover candidate extraction, deduplication, source-revision links, retained findings when fetching fails, URL restrictions and preservation of the reviewed JSON. Initial discovery successfully reached the Amadeusz RSS feed; direct Reddit article access remains subject to blocking. The active workflow publishes candidates and source availability without a human baseline-acceptance step. Earlier baseline instructions apply only to the retained manual page-diff checker.
