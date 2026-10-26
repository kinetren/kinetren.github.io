# Tasks

## 1. Data and catalogs

- [x] 1.1 In `content/structure.toml`, add `releases_latest = ".../releases/latest"` and `release_api = "https://api.github.com/repos/kinetren/kinetren/releases/latest"` to `[site]`, and a `[download]` table with the asset suffixes `win = "-windows-x86_64.zip"` and `linux = "-linux-x86_64.tar.gz"`. Update the `releases` comment. Verify `build.py` still loads the structure.
- [x] 1.2 In `content/en.toml`: add `[headline]` `l1`…`l5` (draft lines from design.md, where `l1` is the former `hero.h1`) and `[dl]` (`win`, `linux`, `other_win`, `other_linux`, `systems`, `all_releases`, `whats_new`). Remove `hero.h1`, `hero.cta_primary`, `hero.cta_note`, `get.cta` and `get.cta_note`. Drop the releases-page sentence from `get.standfirst`. Verify that no new value is filler, per the copy rule.
- [x] 1.3 Apply the same key changes to `es`, `zh-Hans`, `ar` and `ru`. Use the editor's terms from `../kinotrain.9/src/apps/kt-app/i18n/<lang>.toml` (reel, morpher, preview, automation) and keep the same headline count. Verify `python3 build.py` reports no missing or extra keys and every language stays above `translated_min`.

## 2. Markup

- [x] 2.1 Add a `download_panel` helper in `build.py` that emits the Windows and Linux primary buttons (static `href` = `releases_latest`, `data-dl`), the two "other build" text links, an empty label slot per button, the systems line, and the "All releases" (`releases`) and "What's new" (`#roadmap`) links. Verify the panel HTML in `dist/en/index.html`.
- [x] 2.2 Rework `c_hero`: make the top block a two-column grid of text (eyebrow, headline stack, lede, "Features" button) and the panel. The headline stack is an `<h1>` holding `headline.l1` plus `aria-hidden` `<p>` lines for `l2…`. Remove the `#get` button and the `cta_note`. Verify that `dist/ru/index.html` has exactly one `<h1>`, whose text equals `headline.l1`, and no `href="#get"` inside `.hero`.
- [x] 2.3 Rework `c_install` to use `download_panel` instead of the releases button. Verify that `<section id="get">` contains the panel and the requirements list still has its Windows row.
- [x] 2.4 Add the head script that sets `html.os-win` or `html.os-linux` (via `userAgentData.platform`, else the `userAgent`; Android, ChromeOS, iOS and macOS count as neither) to the language pages' `<head>`. Verify by evaluating it in the browser pane with a spoofed Windows and Linux UA.

## 3. Styles

- [x] 3.1 In `assets/kt.css`: add the hero grid (one column below 920 px, logical properties for RTL), the panel styles, which reuse `.btn`/`.btn-primary` and the mono `.cta-note` look, the label and links, and the CSS that hides the non-matching primary button and the irrelevant "other" link under `.os-win`/`.os-linux`. Verify at 1440 px and 375 px on `/en/` and `/ar/` that the panel sits beside the headline (left on Arabic) and below the lede on a phone, with no horizontal scroll.
- [x] 3.2 Add the headline stack: one grid cell, `.hl` at `opacity:0` and `.hl.on` at `opacity:1`, with an `opacity`/`transform` transition of at most 0.6 s. Under `prefers-reduced-motion`, show `l1` only. Verify the lede does not move while lines change, checked in `zh-Hans` and `ar` at 375 px.
- [x] 3.3 Give `.hero` `z-index:3`, so the stats popups are painted above the following sections. Verify with `document.elementFromPoint` inside the "26" list box at 1440 px and 375 px that the box, not the "Rendering" heading, is returned.

## 4. Page script

- [x] 4.1 In `PAGE_JS`, add the release lookup: one `fetch` of `release_api` with a 5 s abort, a `sessionStorage` cache of up to one hour (wrapped in try/catch), asset choice by suffix, `href` rewrite of the matching `data-dl` buttons and links, and the label `<tag> · <size>`. Missing assets or errors leave the static `href` and no label. Verify in the browser pane that the network log shows one request to `api.github.com`, the buttons link `kinetren-…-windows-x86_64.zip` and `…-linux-x86_64.tar.gz` of the latest release, and blocking the request leaves `releases/latest` with no console error.
- [x] 4.2 In `PAGE_JS`, add the headline rotation: a 5 s interval moving `.on`, started and stopped by an `IntersectionObserver` on `.hero` and by `visibilitychange`, and off under `matchMedia('(prefers-reduced-motion: reduce)')`. Verify that lines change on `/es/` within 12 s, stop after scrolling to `#roadmap`, and never start with reduced motion emulated.
- [x] 4.3 Add the runtime label alphabet (`v0123456789.· KMGB`) to `collect_chars`' extra string. Verify `assets/fonts/FONT-MANIFEST.txt` lists the characters after the build.

## 5. Process and docs

- [x] 5.1 In `.claude/skills/site-update/SKILL.md`, add a step: on every sync, check each `[headline]` line against the section it cites, rewrite a line in all five languages if its fact changed, and check the release asset suffixes when `src/scripts/release-build.sh` or `.github/workflows/release.yml` changed. Update the `README.md` lines about the download button if they describe it. Verify by reading the diff.

## 6. Build, check, commit

- [x] 6.1 Run `python3 build.py` and `python3 build.py --check`, and verify both exit 0 with no `kt26.08`, `Kinetren` or `Kinotrain` in `dist/` outside the allowed exceptions.
- [x] 6.2 Run `python3 build.py --serve` and check `/en/`, `/ru/`, `/ar/` and `/zh-Hans/` in the browser pane at 1440 px and 375 px against every scenario of the two delta specs, including the Windows, Linux and macOS UA cases. Take a screenshot of the hero with the panel.
- [x] 6.3 Commit with explicitly staged paths (`content/`, `assets/kt.css`, `assets/fonts/`, `build.py`, `dist/`, `.claude/skills/site-update/SKILL.md`, the change directory) and an English message without attribution lines. Do not push until the owner says so.
