# Design

## Context

See proposal.md — Why. Current state that shapes the approach:

- `build.py` (≈930 lines) is the only build step. It already writes relative asset paths
  (`../assets/…` from language pages, `assets/…` from the root), so the tree works at any
  host root; only absolute SEO URLs use `--base-url`.
- It reaches outside the repository in one place: `shutil.copy2(ROOT.parent /
  "rust/packaging/kinotrain.svg", …)`. The inline `LOGO` `<symbol>` is a hand-copied,
  older variant of that icon. `screenshots.py` depends on `REPO/rust/target/debug/kt-app`,
  `kt-cli` and `rust/scripts/live/` — none of which exist in this repository.
- `shot_src(lang, file)` looks in `assets/shots/<lang>/` and silently falls back to `en`.
  `make_og` builds one 1200×630 JPEG per language from that language's hero.
- Sections reference eight slots: `hero, timeline, fx_video, fx_audio, morpher, bin,
  render_settings, render_progress`. The kinetren monorepo's `docs/images/` (produced by
  its `readme-shots.py`, English UI, CC BY / public-domain footage, credits in
  `docs/images/CREDITS.md`) has: `hero` 1920×1080, `timeline` 1920×319, `video-fx`,
  `slowed-reverb-automation`, `morpher`, `morpher-before-after`, `media-bin`,
  `render-dialog`, `perf-panel`, `reel-parameters`, `search`, `titles`, `transitions`.
- Catalog `shot_alt`/`shot_cap` texts describe the old Kinotrain shots (e.g. "a purple
  morpher block" on the timeline); with new images they become wrong.
- The repo has no commit; the branch is `master`, files are staged including
  `__pycache__/*.pyc`.

## Goals / Non-Goals

**Goals:**
- A fresh clone of this repository alone can run `build.py`, `build.py --check` and
  `import-shots.py --from <kinetren>`.
- One source for every external asset (icon, shots, credits): the kinetren checkout,
  pulled by one script.
- Deploy is a copy of committed bytes: what `--check` verified locally is what is served.

**Non-Goals:**
- New sections for the screenshots the site does not use yet (`perf-panel`, `search`,
  `titles`, `transitions`, `reel-parameters`, `morpher-before-after`).
- Translating the Russian comments/docstrings inside `build.py`, `structure.toml`,
  `kt.css` (follow-up; the README, as the public face, is done now).
- Rebuilding the site in CI, custom domain, WOFF2.

## Decisions

### D1. Slot → image mapping

| slot | new file | note |
|---|---|---|
| `hero` (+ OG cards) | `hero.webp` | full window during playback |
| hero inset `timeline`, section `edit` | `timeline.webp` | reel instance expanded mid-edit |
| `fx_video` | `video-fx.webp` | |
| `fx_audio` | `slowed-reverb-automation.webp` | the existing caption "rate and mix, keyframed" fits as is |
| `morpher` | `morpher.webp` | the editor; before/after is left for a later section |
| `bin` | `media-bin.webp` | |
| `render_settings` | `render-dialog.webp` | |
| `render_progress` | — removed | kinetren publishes no progress shot |

The `export` section switches from `list_and_shots` to the existing `list_and_shot`
component. Its catalog keys change accordingly in all five catalogs: `export.shot2_alt`
and `export.cap` are removed, `export.shot_cap` is added. Alt and caption texts of every
slot whose image changed are rewritten in `en.toml` from the actual images, translated in
`ru.toml`; `es`/`zh-Hans`/`ar` got the English text at first and were translated in the
second round (D16).

Alternative rejected: using `perf-panel.webp` as the second export image — it is the
diagnostics panel, not a render, and its caption would be untrue.

### D2. Revision: one shared screenshot set instead of per-language sets — owner's choice on 2026-10-24

R.22 ("make it so that everywhere it is in the needed language") produced
`assets/shots/<lang>/`. The kinetren pipeline shoots English only, and the owner chose the
current English set for all languages over keeping stale per-language Kinotrain shots.
Layout becomes flat: `assets/shots/<file>.webp` → `dist/assets/shots/<file>.webp`.
`shot_src` loses its `lang` parameter and its silent fallback; a missing file is a build
error naming the slot (spec site-content). `make_og` still writes `og-<lang>.jpg` per
language (the `og:image` URL scheme stays), all from the shared hero.

If localized shots return later, the per-language directory can come back as an optional
override without changing the slot model.

### D3. `import-shots.py` replaces `screenshots.py`

A ~60-line stdlib script: reads `[shot.*].file` from `content/structure.toml`, verifies
every declared file plus `src/packaging/kinetren.svg` and `docs/images/CREDITS.md` exist
in `--from`, then (only after all checks pass) copies them to `assets/shots/`,
`assets/kinetren.svg` and `assets/shots/CREDITS.md`, and deletes `*.webp` in
`assets/shots/` that no slot declares. Copy, not re-encode: the images are already the
editor pipeline's output and must stay byte-identical so their provenance is checkable.

Alternative rejected: keeping `screenshots.py` with a `--repo` argument. It would duplicate
the editor's `readme-shots.py`, shoot the synthetic demo project rather than real footage,
and drift from the editor's own showcase.

### D4. The logo symbol is generated from `assets/kinetren.svg`

`build.py` reads the vendored SVG, strips comments and the XML wrapper, and emits it as
`<symbol id="kt" viewBox=…>` — so the favicon, the header mark and the editor's icon are
one file. The hand-written `LOGO` constant goes away.

### D5. Credits page generated from the imported `CREDITS.md`

`build.py` parses the Markdown table rows of `assets/shots/CREDITS.md` (`[title](url)
(year)`, author, license with optional link) and the trailing notes, and writes
`dist/credits.html` — English, same CSS, linked from each language footer through a new
catalog key `site.credits` (the link text, e.g. "Footage credits"). The link markup is
produced by the build; catalogs still allow no `<a>`. A row the parser cannot read fails
the build, so a format change upstream is noticed rather than silently dropping an
author.

Alternative rejected: credits text inside the catalogs — five copies of license data a
translator could break, and it would drift from the editor's file.

### D6. Download and version

The "Get it" section's button links to `https://github.com/kinetren/kinetren/releases`
(new `[site] releases` value in `structure.toml`, not in catalogs). The hero CTA keeps
`#get`, which scrolls to the install steps. The `kt26.08` label in the header and footer
and JSON-LD `softwareVersion` are removed; the `.mast-ver` style goes with them.

Revision (second round): the section is called "Download", its button reads "Download from
GitHub", and the releases page serves both the Linux tarball and the Windows zip. Versions
appear only in the roadmap's version log (D11).

### D7. Pages deploy: Actions artifact of the committed `dist/`

`.github/workflows/pages.yml`: on `push` to `main` and `workflow_dispatch`; permissions
`contents: read, pages: write, id-token: write`; `concurrency: {group: pages,
cancel-in-progress: false}`; steps `actions/checkout`, `actions/configure-pages`,
`actions/upload-pages-artifact` with `path: dist`, then `actions/deploy-pages` in a job
bound to the `github-pages` environment.

Why not build in CI: subsets depend on the exact font files (`Ubuntu[wdth,wght].ttf`,
Noto CJK/Arabic) of the build host; a runner with other font versions would produce
different bytes and either break `--check` or deploy something nobody checked locally.
Why not "deploy from branch": Pages can only serve `/` or `/docs` of a branch, not
`/dist`. No `.nojekyll` or `CNAME` is needed: an Actions artifact bypasses Jekyll, and
`kinetren.github.io` is the org's default host.

`DEFAULT_BASE` becomes `https://kinetren.github.io`; the committed `dist/` is built with it.

### D8. Repository hygiene

`.gitignore` modelled on the monorepo's: `__pycache__/`, `*.pyc`, `*~`, `*.swp`,
`.DS_Store`, `.directory`, `Thumbs.db`, `/node_modules/`, `.claude/settings.local.json`,
`assets/fonts/*.tmp.ttf` (the subset scratch name in `subset()`), and `/ktprompts*` — the owner keeps private notes in the repo root. `git rm -r --cached
__pycache__`. The branch is renamed `master` → `main` before the first commit, since the
workflow and Pages use `main`.

### D9. Facts come from the editor, not from the old landing copy

The old copy was written for the Kinotrain of August and was both stale ("ten video
effects", "three kinds of track", "X11") and full of slogans. The new copy is taken from the
editor's README (owner-reviewed) and checked against the code: effect and transition names
from the app's catalog (`src/apps/kt-app/i18n/en.toml`, `[trn.kind]`), track kinds from
`LaneKind` (Video, Audio, Morph, Camera). Russian transition names are the app's own Russian
names. A rule in the header of `content/en.toml` forbids filler for future editors.

### D10. Lists behind the numbers: CSS only

Each stat is `tabindex="0"` with a hidden `.pop` shown on `:hover` and `:focus`; focus covers
keyboard and touch (a tap focuses). No script, nothing animates. The lists live in the
catalogs (`stats.<id>_list`) so transition names can be translated; effect names are not
translated (rule 4). The `.hero` clips only horizontally (`overflow-x:clip`), so the box can
extend below it.

### D11. Version log from history, plan from the claims index

There are no GitHub releases or tags yet, and versions are build dates (`kt26.10.24-<hash>`
in `release-build.sh`). The log therefore lists milestone dates from the editor's history —
commit dates and the dated rounds of `docs/user-feedback.md` — each shown once as
`26:10:24`, the same shape as the section timecodes (rejected: printing `v26.10.24` next to
it, which duplicated the same number). Versions are on the left, the plan on the right. The
plan is summarised from `openspec/changes/r71-ktprompts-index/design.md` (its "no",
"partial" and "future" rows, in the order of rounds R.72–R.76 and later); the owner's
private `ktprompts*` files are read but never copied, quoted or committed.

### D12. Live clock

`[data-clock]` on the Download section's timecode; the page script writes `HH:MM:SS` once a
second with `setInterval`. One text node per second costs nothing measurable — the idle-CPU
rule (no infinite compositor work) is about filters and blending, not text.

### D13. Journal-page layout and the rail

`.wrap` uses `margin-inline:0 auto`, so the column sits at the start edge and RTL mirrors it
for free. The menu gets a fixed start margin after the name instead of `margin-inline-start:
auto`. The rail was `position:fixed` (it stood still while the page moved, and was absent on
`credits.html`); it is now `position:absolute` with `top:0; bottom:0` against `body`
(`position:relative`), so it spans and scrolls with the document. It stays hidden below
1000 px, where the column needs the width.

### D14. System language on the English page

The root dispatcher already chose by saved choice → `navigator.languages` → default. The
owner wants English only for those who choose it, so `/en/` runs the same `ktLang()` (shared
code, `lang_detect_js`) and redirects when it differs. Only the default page does this:
redirecting `/ru/` for an English browser would bounce crawlers off every indexable
translation. Picking a language in the switcher writes `localStorage["lang"]`, which wins.
Order `en, es, zh-Hans, ar, ru` is the owner's.

### D15. Lowercase name

The owner's brand rule: "kinetren" in lowercase everywhere. Catalogs, generated strings and
docs are lowercased, and `.mast-name` / `.pick h1` lose `text-transform:uppercase`. Section
headings stay uppercase (they never contain the name). The imported icon keeps its comment
byte-identical.

### D16. Spanish, Chinese and Arabic translated with the editor's terms

The three catalogs were English copies (so the switcher offered five languages but showed
two). They are translated in full. Terms come from the editor's own catalogs
(`src/apps/kt-app/i18n/{es,zh-Hans,ar}.toml`): transition names verbatim, región/区间/منطقة,
bobina/片段/بكرة, cursor/播放头/المؤشر, preajustes/预设/الإعدادات المسبقة. Effect names stay
English (rule 4). Arabic uses ، ؛ ؟ (the build enforces it) and logical order. All five pass
`translated_min` and are indexed.

## Risks / Trade-offs

- [Font versions differ between machines → `--check` fails on another host although
  nothing changed] → documented in README: `--check` is meaningful on the host that
  built `dist/`; CI never rebuilds.
- [Org repo name must be exactly `kinetren.github.io` and Pages source set to "GitHub
  Actions", or the deploy job fails / serves nothing] → README lists the one-time owner
  setup; the workflow fails visibly rather than silently.
- [Alt texts describe images the writer has not looked at] → task to view each new image
  before writing its alt/caption.
- [CC BY attribution missing or stale → license breach on a public page] → credits are
  generated from the editor's file and a parse failure fails the build.
- [Pages on other languages show an English UI] → accepted by the owner (D2).
- [The version log is curated from history, not from published releases] → once GitHub
  releases exist, the log should list them; until then the dates are build dates (D11).
- [A redirect from `/en/` could surprise a visitor who followed an English link] → the
  switcher choice is remembered and wins; only `/en/` redirects (D14).

## Migration Plan

1. Implement and build locally; `build.py --check` green; review via `--serve`.
2. Commit on `main`.
3. Owner: create `kinetren/kinetren.github.io`, set Settings → Pages → Source "GitHub
   Actions", add the remote, push.
4. Rollback: re-run the workflow on an earlier commit (`workflow_dispatch` on that ref)
   or revert and push; Pages keeps serving the last successful deployment meanwhile.
