# site-publishing

## Purpose

How this repository is kept and published as the GitHub Pages site
`https://kinetren.github.io`: what is committed, what is ignored, which URL the pages
claim, and how a push to `main` reaches the live site.

## Requirements

### Requirement: Generated caches and local files stay out of git
The repository SHALL have a `.gitignore` that excludes Python bytecode (`__pycache__/`,
`*.pyc`), editor and OS files (`*~`, `*.swp`, `.DS_Store`, `.directory`, `Thumbs.db`),
local Claude settings (`.claude/settings.local.json`), `node_modules/`, and build scratch
(temporary font files), and the owner's private notes kept in the repository root
(`/ktprompts*`), which MUST never be committed or published. `dist/`, `assets/fonts/`,
`openspec/` and the shared `.claude/` commands and skills SHALL remain tracked. No ignored
path SHALL be in the index or in any commit of the branch.

#### Scenario: Bytecode is not tracked
- **WHEN** `python3 build.py` runs and then `git status --porcelain` is read
- **THEN** no `__pycache__` or `.pyc` path appears, and `git ls-files` lists none

#### Scenario: Private notes never enter history
- **WHEN** `git log --all --oneline -- 'ktprompts*'` runs
- **THEN** it prints nothing

### Requirement: Code speaks English
Comments, docstrings, build messages and `--help` texts in `build.py`, `import-shots.py`,
`assets/kt.css`, `content/structure.toml` and the catalog headers SHALL be English. Russian
and other languages appear only as translation values and language self-names.

#### Scenario: No Cyrillic outside translations
- **WHEN** `build.py`, `import-shots.py`, `assets/kt.css`, `content/structure.toml` and the comment lines of every catalog are searched for Cyrillic
- **THEN** the only matches are the `ru = "Русский"` self-name lines

### Requirement: The committed dist is the Pages root and claims the Pages URL
`dist/` SHALL be committed and SHALL be the exact tree served at the site root. The default
base URL SHALL be `https://kinetren.github.io`; every `canonical`, `hreflang`, `og:url`,
`og:image`, `sitemap.xml` and `robots.txt` URL in the committed `dist/` SHALL start with it.
All links between pages and to assets SHALL be relative, so the same tree also works from
`--serve`.

#### Scenario: URLs in the committed output
- **WHEN** the committed `dist/` is searched for absolute `http(s)://` URLs of the site itself
- **THEN** all of them start with `https://kinetren.github.io/`, and none contains `kinotrain.app`

### Requirement: A push to main publishes dist
A GitHub Actions workflow SHALL, on every push to `main` and on manual dispatch, upload the
committed `dist/` unchanged as the Pages artifact and deploy it to GitHub Pages, with only
the permissions Pages deployment needs (`contents: read`, `pages: write`,
`id-token: write`) and one deployment at a time. The workflow MUST NOT rebuild the site.

#### Scenario: Deploy after a push
- **WHEN** a commit that changes `dist/` is pushed to `main` of `kinetren/kinetren.github.io` with Pages source set to "GitHub Actions"
- **THEN** the workflow succeeds and `https://kinetren.github.io/en/` serves the new `dist/en/index.html`

### Requirement: The README describes the standalone repository
`README.md` SHALL be in English and describe this repository on its own: how to build,
check and serve the site, how to translate, how to refresh screenshots from a kinetren
checkout, what the build checks, and how publishing works (including the one-time owner
setup on GitHub). It MUST NOT give commands that assume a `site/` subdirectory or a
monorepo beside it, except the explicit `--from <kinetren checkout>` argument.

#### Scenario: Commands in the README run from the repository root
- **WHEN** each shell command in `README.md` is run from a fresh clone's root (with a kinetren checkout passed where `--from` asks for one)
- **THEN** none fails because of a missing `site/` or `rust/` path
