# kinetren site

The landing page and user guide of the kinetren video editor, published by GitHub Pages
from the committed `dist/`. `README.md` describes the repository; `openspec/specs/` holds
the contracts (`site-content`, `site-build`, `site-publishing`, `site-docs`,
`upstream-sync`).

## "обнови" means: sync the site with the editor

When the owner asks to update the site ("обнови", "обнови сайт", "update", "sync with the
editor"), follow `.claude/skills/site-update/SKILL.md` from start to end. It finds what
changed in the editor (github.com/kinetren/kinetren, checked out as `../kinotrain.9`)
since `upstream.lock`, rewrites the affected sections in all five languages, adds roadmap
entries for new tags, re-imports screenshots and the guide, builds, checks and commits.

## House rules

- `dist/` is never edited by hand: `python3 build.py`, then `python3 build.py --check`.
- `assets/shots/`, `assets/guide/` and `assets/kinetren.svg` come only from
  `python3 upstream.py import`. Wrong text in the guide is fixed in the editor.
- The editor checkout is only read: no fetch, pull, checkout or edits there.
- Catalog copy states facts about the editor, never slogans. The name is lowercase
  **kinetren**. Translations use the editor's own terms
  (`src/apps/kt-app/i18n/<lang>.toml` in the editor).
- Code, comments and commit messages are in English. Commits carry **no**
  `Co-Authored-By` or other AI/agent attribution lines.
- A push to `main` publishes the site: push only when the owner says so.
- Work is planned as OpenSpec changes (`/opsx:propose` → `/opsx:apply` →
  `/opsx:archive`).
