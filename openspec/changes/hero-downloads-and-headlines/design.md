# Design

## Context

- The hero is built by `c_hero` in `build.py` as one column: eyebrow, `h1` (`max-width:15ch`),
  lede and a `.cta` row. The column is 1200 px wide (`--col`), so on wide screens roughly half
  of the space beside the headline is empty. The "Download" section is built by `c_install`
  and has one button that links to `[site] releases`.
- Release assets are created by the editor's `.github/workflows/release.yml` and named
  `kinetren-<YY.MM.DD>-<hash8>-linux-x86_64.tar.gz` and `…-windows-x86_64.zip`, each with a
  `.sha256`. The name holds a commit hash, so `releases/latest/download/<fixed-name>` URLs
  cannot exist. Also, a tag does not always get a release: `upstream.lock` is at `v26.10.26`,
  but the latest release on GitHub is `v26.10.25`.
- The page already runs one inline script (`PAGE_JS`: section reveal, hero tilt, clock,
  language memory) at the end of `<body>`, and sets the `.js` class on `<html>` there.
- Stats popup bug: `.hero` has `position:relative; isolation:isolate` with no `z-index`,
  and the next `<section>` is also `position:relative`. The hero forms its own stacking
  context at level 0, and the section comes later in the tree, so the section is painted
  on top. The `.pop` (`z-index:30`) can only rise within the hero, so the "Rendering"
  heading and slab cover the bottom of the 26-name list.

## Goals / Non-Goals

**Goals:**
- One panel component, used in the hero and in `#get`, that works fully without JavaScript
  and becomes direct, system-matched downloads with it.
- Headline rotation that keeps the SEO and accessibility of the current `h1`.

**Non-Goals:**
- No macOS, ARM, deb/rpm/AppImage or other builds. The panel shows only what the release
  workflow publishes.
- No checksum display or verification UI. The `.sha256` files stay on the release page.
- No change to the editor or its release naming.

## Decisions

### Release lookup in the browser, with static fallback
At page load, the script requests `GET https://api.github.com/repos/kinetren/kinetren/releases/latest`
once (`fetch`, 5 s timeout via `AbortController`). That endpoint excludes drafts and
prereleases. The script picks assets by suffix (`-windows-x86_64.zip`,
`-linux-x86_64.tar.gz`) and rewrites the `href` of matching buttons to `browser_download_url`.
It fills the label `<tag> · <size>` (size in MB with one decimal under 100 MB, else whole
MB). The parsed result `{tag, win:{url,size}, linux:{url,size}, at}` is cached in
`sessionStorage` for one hour. Unauthenticated API use allows 60 requests per hour per IP,
so a visitor clicking through languages does not use up the limit.

The static `href` is `releases/latest`, a GitHub redirect to the newest release page. It
is always valid and gives non-JS visitors a page with the files.

*Alternative considered:* record asset URLs at sync time (`upstream.py` → lock or
structure). That needs no third-party request and no JS. But it goes stale whenever a
release lands between syncs. It also would have recorded a missing release today (lock
tag `v26.10.26` has none). It also adds network access to the sync tooling. The runtime
lookup was chosen. Its only cost is one request to GitHub, which the visitor makes anyway
when downloading.

### System detection in `<head>`, before first paint
A small inline script in `<head>` sets `html.os-win`, `html.os-linux` or nothing. It uses
`navigator.userAgentData.platform` when present, otherwise `navigator.userAgent`, and
excludes Android, ChromeOS, iOS and macOS from "linux". CSS then hides the non-matching
primary button and shows the matching "other build" text link. Because the class is set
before layout, the panel does not flash two buttons. With no class (other OS, no JS), both
buttons and the "Linux and Windows" line are shown.

*Alternative considered:* doing it in `PAGE_JS` at the end of body. Rejected because both
buttons would flash on load.

### Panel markup is static and identical on both places
`build.py` gets a `download_panel(struct, t, where)` helper that emits both buttons, both
"other build" links, the meta label slots, the systems line, and the two text links. All
of this is driven by `data-dl="win|linux"` attributes, so the script needs no knowledge of
which instance it is updating. URLs live in `structure.toml [site]`: `releases`
(existing), `releases_latest`, `release_api`, plus asset suffixes in a new `[download]`
table. Catalog text lives in a new `[dl]` table: `win`, `win_note`, `linux`, `linux_note`
(the platform line under each button, which also serves visitors without JavaScript),
`other_win`, `other_linux`, `systems`, `all_releases` and `whats_new`. The number of
headline lines is the number of `headline.l*` keys in the English catalog. The validator
already requires every other catalog to have the same keys.

### Hero layout: grid, not absolute positioning
The top `.wrap` of the hero becomes a two-column grid: `minmax(0,1fr) auto` with the panel
in the inline-end column, aligned to the headline's top. Below `920px` (the existing
`.split` breakpoint) it collapses to one column with the panel after the lede. The
"Features" button and the eyebrow stay in the left column. Logical properties keep it
right for RTL.

### Headline stack
The markup is `<div class="headline">` with `<h1 class="hl on">l1</h1>` and
`<p class="hl" aria-hidden="true">l2..ln</p>` stacked in one grid cell
(`grid-area:1/1`). The cell takes the height of its tallest line, so the lede never
jumps. Only `.on` has `opacity:1`. The script moves `.on` every 5 s, and the transition is
`opacity .5s, transform .5s` (a small `translateY`). An `IntersectionObserver` on the hero
and `visibilitychange` start and stop the timer. `matchMedia('(prefers-reduced-motion:
reduce)')` disables it. The `<h1>` keeps the existing `h1` styles, including the `<em>`
gradient.

Draft headlines (English; the owner approves the wording during review, and each line is
backed by the named section):

1. `A free video editor <em>for Linux and Windows</em>`: tagline, `get`
2. `The preview <em>is the export</em>`: `why.ship_*` (one code path)
3. `Every parameter <em>on a curve</em>`: `effects.note` (automation)
4. `Edit a reel once, <em>every copy follows</em>`: `edit.reels_*`
5. `Swap the source, <em>keep the cut</em>`: `morpher.swap_*`

The translations use the catalog's existing terms for reel, morpher, preview and automation
in each language.

### Stats popup above the next section
`.hero` gets `z-index:3` (it is already positioned), so its stacking context is painted
above the following sections (`z-index:auto`). The sticky header is `z-index:20` and stays
above it. The popup on narrow screens keeps `max-width:min(440px,90vw)`. The fix is
verified with `elementFromPoint` (spec scenario).

### Font coverage
`collect_chars` gets the runtime label alphabet in its `extra` string, so the label never
falls back to a system font.

## Risks / Trade-offs

- [GitHub API rate limit or outage] → The buttons keep the `releases/latest` href, which still works. The answer is cached per session.
- [The asset naming changes in the editor's release workflow] → The suffix match fails, the buttons fall back to the release page, and the change is visible but harmless. The suffixes are in `structure.toml` for a one-line fix. `upstream.py status` already flags `src/scripts/release-build.sh` under section `get`.
- [UA spoofing or no detection] → The visitor gets both buttons, which is the safe default.
- [Headline wording drifts into slogans over time] → The copy requirement now names the exception and its fact-backing rule. The site-update skill re-checks each headline against the sections it cites.
- [The crossfade conflicts with "stays idle"] → It is opacity and transform only, every 5 s, paused off screen, in a hidden tab and under reduced motion. The spec is amended to say so explicitly.
- [Mid-length translations wrap to more lines than English] → The stack's height is the tallest line, so the layout is stable. Check at 375 px in `zh-Hans` and `ar`.

## Migration Plan

This is a content-only site. The work is built, checked with `build.py --check`, committed,
and published by a push to `main` when the owner says so. Rollback is a revert of the commit.
