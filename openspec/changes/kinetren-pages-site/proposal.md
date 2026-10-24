# Proposal

## Why

This repository is the `site/` landing page lifted out of the editor's monorepo
(`/media/e/developer/kt.9/kinotrain.9`) as it stood on 2026-10-21 — one day before the
product was renamed to **Kinetren** (archived change `2026-10-22-kinetren-rename` there).
So it still says Kinotrain everywhere, shows screenshots of the old UI, depends on files
that only exist in the monorepo (`../rust/packaging/kinotrain.svg`, `../rust/target/…`,
`../rust/scripts/live/`), has no `.gitignore` (compiled `__pycache__/*.pyc` is already
staged), no commit yet, and nothing that publishes it. It is to become its own GitHub
repository served by GitHub Pages at `https://kinetren.github.io`.

There are also no specs here: the site's behaviour is only described in `README.md` and in
the owner's rounds R.19–R.22 of the monorepo's `docs/user-feedback.md`. Before changing it,
the existing contract is written down, so the change does not silently drop any of it.

## What Changes

- **Specs bootstrapped from what exists.** The current, working behaviour of `build.py`
  (catalog validation, translation coverage → `noindex`, language dispatcher, font
  subsets, reproducible `--check`, `--serve`, no idle CPU load) becomes the baseline spec.
- **Standalone build.** `build.py` no longer reads anything outside this repository: the
  app icon is vendored as `assets/kinetren.svg`. Paths in docs and messages lose the
  `site/` prefix.
- **Rename to Kinetren.** Every visible name, the page `<title>`, Open Graph, JSON-LD,
  the inline logo, the icon file, and the five catalogs say Kinetren; facts the rename
  changed are corrected (project type `.kt` instead of `.otio`).
- **BREAKING (content) — one English screenshot set for every language.** The eight
  per-language Kinotrain shots (`assets/shots/<lang>/`) are replaced by the current
  Kinetren screenshots from the monorepo's `docs/images/` (English UI, free footage).
  This revises the owner's R.22 decision "the window in the page's language" — chosen by
  the owner on 2026-10-24. `screenshots.py` (which needs the monorepo's `rust/` tree and
  produced per-language shots) is removed; a small `import-shots.py --from <kinetren
  checkout>` copies the declared images and the icon instead.
- **Footage attribution on the page.** The new screenshots show CC BY films, so the page
  footer credits them, linking to a credits list.
- **Download goes somewhere.** The "Download for Linux" button points to
  `https://github.com/kinetren/kinetren/releases` instead of `#get`; the hard-coded
  version label `kt26.08` is dropped (the releases page is the version of record).
- **GitHub Pages.** Default base URL becomes `https://kinetren.github.io`; a GitHub
  Actions workflow deploys the committed `dist/` as is on push to `main` (it does not
  rebuild: font subsets depend on the host's font versions). `build.py --check` stays the
  local gate before pushing.
- **Repository hygiene.** A `.gitignore` (Python caches, editor/OS files, local Claude
  settings, build scratch); the staged `__pycache__/` is unstaged; `README.md` rewritten
  for the standalone repository, in English (the project's document language).

Non-goals: rewriting the feature prose or the roadmap to match today's Kinetren (owner's
rule: the site roadmap is not touched without a separate request); translating
`es`/`zh-Hans`/`ar`; a custom domain; WOFF2.

## Capabilities

### New Capabilities
- `site-build`: generating the multilingual static site from `content/` and `assets/` —
  catalog validation, translation coverage and indexing, the language dispatcher, font
  subsets, reproducibility and the `--check`/`--serve` modes, all self-contained in this
  repository.
- `site-content`: what the page shows — the Kinetren name and icon, the screenshot set and
  where it comes from, footage attribution, and the download target.
- `site-publishing`: how the repository is kept and published — `.gitignore`, the
  committed `dist/` as the Pages root, the base URL and the deploy workflow.

### Modified Capabilities
<!-- none: openspec/specs/ is empty in this repository -->

## Impact

- `build.py` (icon path, names, base URL, shot resolution, footer, download link, version
  label), `content/structure.toml`, all five `content/*.toml`, `assets/kt.css` (header
  comment), `assets/shots/` (replaced), `assets/kinetren.svg` (new), `assets/fonts/`
  (regenerated), `dist/` (rebuilt).
- Removed: `screenshots.py`, `assets/shots/<lang>/` for `ru es zh-Hans ar`,
  `__pycache__/`.
- New: `.gitignore`, `import-shots.py`, `.github/workflows/pages.yml`.
- Build host needs the same tools as before (Python 3.11+, fontTools, Pillow, Ubuntu and
  Noto fonts); the CI runner needs none of them.
- Owner-side, outside the repo: create `github.com/kinetren/kinetren.github.io`, set
  Pages source to "GitHub Actions".
