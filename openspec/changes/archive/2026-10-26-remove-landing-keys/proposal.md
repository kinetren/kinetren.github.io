# Proposal

## Why

The landing page carries a full "Keyboard" section: 30 rows in four groups, with key
chords in `structure.toml` and 35 catalog keys in each of five languages. The owner's
verdict (2026-10-26) is that a reference table does not belong on a landing page. It also
duplicates `docs/guide/shortcuts.md`, which drifted from it twice already (the last sync
rewrote six rows). The table should live in the user guide, now published at
`/docs/shortcuts/`. But the guide's version looks worse than the landing's: keys are bold
text, not key caps, and there are no groups for region and view. The owner wants the
editor's agent to rewrite that page properly, so the site's renderer has to accept the key
caps the rewrite will use.

## What Changes

- **Remove the keyboard section from the landing page.** That covers the `[[section]]
  id = "keys"`, the `[keys.*]` chord tables in `content/structure.toml`, the `[keys]` table
  in all five catalogs, the `keys` component in `build.py` and the `.keys` styles. The
  sections after it shift up: roadmap `00:01:58`, download `00:02:12`, and their slabs
  keep alternating. The roadmap plan item `n_keys` (automation keys) is unrelated and
  stays.
- **The guide may use `<kbd>`.** The `/docs/` renderer accepts paired `<kbd>…</kbd>` as
  the only inline HTML, rendered as the same key caps as the landing page. Any other HTML
  still fails the build with `file:line`.
- **A prompt for the editor's agent** (`editor-prompt.md` in this change). It asks the
  agent to rewrite `docs/guide/shortcuts.md` in the editor repository: groups, `<kbd>`
  caps, every shortcut the program actually has, each checked against the code and not
  copied from the landing page, and only Markdown the site renders. The owner pastes it in
  the editor repository. This repository does not write there.
- The upstream map, the update skill and the specs stop mentioning a keyboard section.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `site-content`: a new requirement that the landing page carries no keyboard reference
  and that shortcuts are documented in the guide.
- `site-build`: the page form no longer lists key chords.
- `site-docs`: guide text may contain `<kbd>` as its only inline HTML.
- `upstream-sync`: the example update no longer touches a keyboard section.

## Impact

- `content/structure.toml`, `content/{en,es,zh-Hans,ar,ru}.toml`, `build.py`
  (`c_keys`, `collect_chars`, guide inline renderer), `assets/kt.css`, `README.md`,
  `.claude/skills/site-update/SKILL.md`, `dist/` (rebuilt).
- `/docs/shortcuts/` changes only after the editor's rewrite lands and the next "обнови"
  imports it.
- Nothing links to `#keys` (the header menu never had it). Bookmarks of `/<lang>/#keys`
  fall back to the top of the page.
