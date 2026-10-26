# Design

## Context

- The landing page's `keys` section is drawn by `c_keys` in `build.py` from
  `[keys.transport|editing|region|view]` in `content/structure.toml` (30 rows of chords)
  and the `[keys]` table of each catalog (title, standfirst, 4 group names, 30 action
  texts). `.keys` styles in `assets/kt.css`, lines 381–396 and the `min-width:0` list on
  line 42. `collect_chars` adds the chords to the font subsets.
- The global `kbd` style (`assets/kt.css`, line 337) is already shared by every page,
  including `/docs/`.
- The `/docs/` renderer (`GuidePage.inline`) fails on any `<` followed by a letter. The
  catalogs already allow `<kbd>` through `INLINE_TAGS`.
- `docs/guide/shortcuts.md` in the editor has three tables (Transport, Editing, Mouse on
  the timeline) with keys in bold. It lacks things the landing page had: double-click on
  the preview to detach it, double-click on the timecode to type a position, double-click
  on the speed bar, volume rail or fader to reset them, and paste that chains. It also
  has things the landing page lacked: `Alt+M`/`Alt+S`, `Enter` on a reel, the mouse
  gestures.
- Section order and look today: … export `00:01:30` warm, care `00:01:44` none, keys
  `00:01:58` plain, roadmap `00:02:12` none, get `00:02:26` plain (clock).

## Goals / Non-Goals

**Goals:**
- No shortcut reference on the landing page, in any language, and no data left behind for
  it.
- `/docs/shortcuts/` can show key caps as soon as the editor writes them.
- The editor's agent gets a self-contained brief that produces a complete, verified
  shortcuts page.

**Non-Goals:**
- Writing the editor's guide from here. The site never edits imported text (`site-docs`,
  `upstream-sync`).
- Translating the guide.
- A link from a landing section to `/docs/shortcuts/`. The header already has "Docs", and
  a "see all shortcuts" line would be a section of its own again.

## Decisions

### D1. Remove the section and its data together

The `[[section]]`, the `[keys.*]` tables, the catalogs' `[keys]` tables, `c_keys`, its
`COMPONENTS` entry, the chords in `collect_chars` and the `.keys` CSS go in one change.
Leaving the component or the catalog keys "for later" would leave 175 translated strings
with nothing to show them, and the build's key-set check would keep them alive in five
files. `roadmap.n_keys` ("selecting and moving several automation keys") is a plan item,
not part of the section, and stays.

### D2. Timecodes and slabs close the gap

Roadmap moves to `00:01:58` and download to `00:02:12`, so the timecodes keep their 14 s
step. Slabs keep alternating after `care` (none): roadmap becomes `plain` and download
`none`. Rejected: keeping the old timecodes. A 28 s jump reads as a missing section,
because the timecodes imitate one continuous timeline.

### D3. `<kbd>` is the one inline HTML the guide may use

In `GuidePage.inline`, before the raw-HTML check, each `<kbd>…</kbd>` pair in a non-code
part is cut out. Its content must contain no `<`, `` ` `` or `*`. It is HTML-escaped and
put back after the Markdown pass as `<kbd>…</kbd>`. Any `<` left after the cut, including
an unpaired `<kbd>` or `</kbd>`, still fails with `file:line`. `md_plain` (titles,
descriptions, anchors) drops the tags and keeps the text, which is what GitHub does for
anchors. Inside backticks `<kbd>` stays literal code, as on GitHub.
Rejected: an allow-list of several tags. `<kbd>` is the only one the shortcut page needs,
and every extra tag is a way for the guide to look different on GitHub and on the site.
Rejected: turning `**Ctrl+S**` into caps on the site. The same text would then render
differently on GitHub and here.

### D4. The prompt is an artifact of this change, handed over by the owner

`editor-prompt.md` lives in the change directory, so it is archived with the decision that
produced it, and the owner pastes it into a session in the editor repository. It is
written in Russian, the owner's language with that agent. The editor's agent records the
owner's words in its `docs/user-feedback.md` and writes the guide in English. The prompt
tells it to verify every shortcut against the code (key handling in
`src/apps/kt-app/src/`), because the landing rows were themselves out of date twice. It
also names the Markdown subset the site renders, and the `<kbd>` convention.
Rejected: writing into the editor checkout from here. `upstream-sync` makes the checkout
read-only for this repository's tools and agents.

## Risks / Trade-offs

- [Between this change and the editor's rewrite, shortcuts exist only in the plainer
  guide page] → it already lists more shortcuts than the landing page did. The rewrite
  lands with the next "обнови".
- [The editor's agent writes HTML the site does not render] → the build fails with
  `file:line` on import. The prompt lists the subset, so this should not happen.
- [Visitors with `/#keys` bookmarks] → the fragment no longer resolves, and the page
  opens at the top.

## Migration Plan

1. Land the removal and the `<kbd>` support, rebuild, commit.
2. The owner gives `editor-prompt.md` to the editor's agent.
3. After the editor commits the new page, "обнови" imports it and `/docs/shortcuts/` shows
   key caps.

Rollback: revert the commit.
