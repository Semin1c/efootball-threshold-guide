# eFootball 2027 — Threshold Field Guide

Personal progression reference: 11 positions × 26 attributes, role targets, searchable evidence, confidence labels and automatic provisional findings.

## Live site

GitHub Pages: https://Semin1c.github.io/efootball-threshold-guide/
Repository: https://github.com/Semin1c/efootball-threshold-guide

Bookmark the same link on your phone, iPad or laptop. The hosted guide does not depend on your laptop staying on. This is a public site and repository, not a private/login-protected service.

## What updates automatically

The **Update provisional findings** GitHub workflow runs Mondays at 14:17 UTC and supports manual runs in the repository’s Actions tab. It checks vetted pages, the latest 50 entries of the Amadeusz public feed and up to eight official news links. The scheduler may run later than the requested time.

Detected mechanics discussions are added to `site/provisional.json` as **provisional** with a short source quotation, source URL, discovery time, source publication date when available, mentioned engine version and uncertainty notes. The job commits that feed to repository history and publishes the updated site in the same run.

This is deliberately simple text matching, not an AI fact checker. It cannot reliably tell a claim from a question, independently reproduce tests, infer mobile applicability, or read all information contained in images/videos. Candidate snippets are prompts to read the source. Source edits create a new entry linked to the prior entry when the extracted finding changes. Duplicates are skipped. Previously published findings remain when sources fail.

**Reviewed target ranges and thresholds are never overwritten.** Those live separately in `site/thresholds.json`. Human review is still required to promote a provisional finding into that chart. “Last updated” is the chart’s review date; “Last automatic check” is the source watcher’s timestamp. Reaching a source is not proof its claims are correct.

Direct Reddit post retrieval can be blocked even when its public feed works. The website displays successful/failed source counts and details. A partial-access run still publishes available discoveries and its honest health status. If GitHub disables a workflow or a run fails before publishing, the last check timestamp remains old; inspect Actions and re-enable/rerun it.

## Local preview

```sh
python3 -m http.server 8000 --directory site
```

Open http://localhost:8000. Double-clicking the HTML file normally cannot fetch its separate JSON. Offline persistence is not implemented.

## Manual checks and updates

```sh
python3 scripts/validate_data.py
python3 scripts/test_monitor.py
python3 scripts/test_claims.py
node --check site/app.js
python3 scripts/update_claims.py
```

The final command fetches public sources and writes only the provisional feed. It requires no AI API key or paid service. For Python certificate errors, repair the trusted certificate installation or set `SSL_CERT_FILE` to an operating-system trusted CA bundle. Never disable TLS verification.

The original `scripts/check_sources.py` remains available as a separate manual page-diff tool. Its baseline-acceptance flow does not control the active provisional workflow. No initial manual baseline is required for the active workflow.

For edits to reviewed values, record the exact game version/platform, source, controls, player model, manager/boosters, form/stamina, trial counts and uncertainty. Update affected `lastReviewed` dates and the chart’s `lastUpdated`/`lastSourceReview` fields honestly. Every position range is an editorial heuristic, not an official or measured minimum.

## Hosting a copy

Put the full project at the root of a GitHub repository, including `.github`. Use branch `main`. Under Settings → Pages, choose GitHub Actions and run **Publish guide to GitHub Pages**. Enable Actions and workflow write permissions for the updater if your repository/organization defaults restrict them. The update job’s write permission is for the provisional JSON commit; it does not promote claims.

Alternatively, drag just the `site` folder into [Netlify Drop](https://app.netlify.com/drop). This publishes a static snapshot. The included GitHub updater deploys to GitHub Pages; a Netlify snapshot does not receive updates unless you connect and configure Git-based deployment separately. `netlify.toml` supplies the correct publish folder.

All assets use relative paths, so repository subpaths work. No fonts, analytics or third-party scripts load in the browser.

## Data files

- `site/thresholds.json`: reviewed source notes, editorial ranges, mechanics, confidence definitions and memory aid.
- `site/provisional.json`: automatic source findings and availability; separate from reviewed values.
- `sources-watch.json`: vetted static sources; discovery endpoints are fixed in `scripts/update_claims.py`.
- `.github/workflows/pages.yml`: publish on manual dispatch or main-branch site edits.
- `.github/workflows/review-sources.yml`: weekly discovery, history preservation and publication.

Independent fan reference. Not affiliated with KONAMI.
