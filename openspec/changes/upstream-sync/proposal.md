# Proposal

## Why

The site describes an editor that changes every day, and today nothing connects the two
repositories except a manual `import-shots.py --from ../kinotrain.9`. The facts on the page
are written by hand from the editor's README, guide and history, so they already drift:
the editor has tags `v26.10.25` and `v26.10.25.1` that the roadmap does not list; its
`docs/guide/shortcuts.md` describes Space and A/D differently from the site's keyboard
table; its README links another Discord invite and `kinetren.com`. The owner wants one
request — "обнови" / "update" — to make an agent find what changed in the editor since the
last sync and update every affected section of the page, not only the version log. The
user guide in the editor's `docs/guide/` must also appear on the site without becoming a
second copy that someone edits and forgets.

## What Changes

- **A sync point.** A committed `upstream.lock` records the editor commit and tag the site
  was last synced to, and the SHA-256 of every file imported from it.
- **One upstream tool.** `upstream.py` replaces `import-shots.py`
  (**BREAKING** for anyone running the old script name):
  - `status` lists the commits and new `v*` tags since the lock, and groups the files
    changed in the editor by the site section that depends on them;
  - `import` copies screenshots, icon, credits and the guide from a committed editor
    revision (never from its working tree) and rewrites the lock;
  - `facts` compares the facts that can be checked mechanically (language self-names,
    transition names and count, effect names and counts, versions against tags) and
    prints every mismatch.
  The tool only reads the editor checkout: no fetch, pull, checkout or write there.
- **Sections declare their upstream sources.** Each `[[section]]` in
  `content/structure.toml` names the editor paths it is written from (specs, guide pages,
  the UI catalog), so `status` can say "export: `openspec/specs/export/spec.md`,
  `docs/guide/export.md` changed".
- **An agent procedure for "обнови".** A project skill and a `CLAUDE.md` in this
  repository: run `status`; for each affected section read the editor diff and update
  `en.toml`, `structure.toml` and the same keys in the other four catalogs; add a version
  entry for each new tag date; import; build; `--check`; `facts`; commit; report per
  section. Pushing (= publishing) stays the owner's decision.
- **The user guide on the site.** The guide is imported byte for byte into
  `assets/guide/`, its images into `assets/shots/`, and rendered in English to
  `/docs/` and `/docs/<page>/`. Every language page gets a "Docs" link in the header. Links
  between guide pages become site links; other repository links point at GitHub at the
  locked commit. The build fails on Markdown it does not render, on a broken anchor and on
  a guide page not listed in `structure.toml`.
- **Imported files cannot be edited here.** The build fails when an imported file's digest
  differs from `upstream.lock`.
- **The version log follows tags.** One roadmap entry per tag date (`v26.10.25` and
  `v26.10.25.1` are one entry); entries before the first tag stay as they are.

## Capabilities

### New Capabilities
- `upstream-sync`: the sync point, the read-only upstream tool (`status`, `import`,
  `facts`), section-to-source mapping, finding the checkout, and the agent procedure that
  "обнови" triggers.
- `site-docs`: the editor's user guide imported and rendered as English pages of the site,
  with link rewriting, anchors, images and the checks that keep it identical to the source.

### Modified Capabilities
- `site-content`: the roadmap's versions come from the editor's `v*` tags; screenshots are
  imported by `upstream.py` from a committed revision and checked against the lock; images
  used by the guide count as referenced.
- `site-build`: the site is also generated from the imported guide; imported files are
  verified against `upstream.lock`.
- `site-publishing`: the English-only rule and the README cover `upstream.py`, the lock
  and the update procedure instead of `import-shots.py`.

## Impact

- New: `upstream.py`, `upstream.lock`, `assets/guide/`, `CLAUDE.md`,
  `.claude/skills/site-update/SKILL.md`, `dist/docs/`.
- Changed: `build.py` (Markdown renderer, docs pages, lock verification, sitemap, font
  characters), `content/structure.toml` (`upstream` per section, `[docs]`, roadmap
  versions), all five catalogs (`site.nav_docs`, new version summaries), `README.md`,
  `assets/kt.css` (guide typography).
- Removed: `import-shots.py`.
- No new dependency: the Markdown subset is rendered by `build.py` itself.
- The editor repository is only read. The guide quotes the editor's UI as written,
  including its capitalised "Kinetren", so `dist/docs/` is exempt from the site's
  lowercase rule (owner, 2026-10-26).
