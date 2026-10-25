---
name: site-update
description: Bring the kinetren site up to date with the kinetren editor (the main repository). Use when the owner says "обнови", "обнови сайт", "update", "update the site", "sync with the editor" or "pull changes from the main repo" in this repository. Finds what changed in the editor since upstream.lock, rewrites the affected sections in all five languages (not only the version log), re-imports screenshots and the user guide, builds, checks and commits.
---

# Update the site from the editor

The site describes the kinetren editor (github.com/kinetren/kinetren, checked out next to
this repository, usually as `../kinotrain.9`). `upstream.lock` records the editor commit
the site was last synced to. This procedure brings every part of the page that depends on
the editor up to that editor's current committed state.

Work only in this repository. The editor checkout is only read. Do not fetch, pull, check
out or edit anything there. If `status` says `origin/master` is ahead, tell the owner to
pull in the editor repository. Do not do it yourself.

## 1. What changed

```bash
python3 upstream.py status
```

- "up to date": say so in one line and stop. No commit.
- Otherwise read the whole report: the commit subjects of the range, new `v*` tags,
  sections whose sources changed, guide pages, images, "not mapped" and "missing
  upstream".
- A "missing upstream" path means the editor moved or renamed something a section was
  written from. Find the new path (`git -C <checkout> log --stat --follow`) and fix that
  section's `upstream` list in `content/structure.toml`.

## 2. Read the editor, not the code

For every section in the report:

```bash
git -C <checkout> diff <locked commit>..HEAD -- <the section's upstream paths>
```

Specs (`openspec/specs/<cap>/spec.md`) say what the editor does. The guide
(`docs/guide/*.md`) says it in user words. The UI catalog
(`src/apps/kt-app/i18n/en.toml`) has the exact names of menus and controls. Read those,
not the Rust code. Then list the facts on the page that are now wrong or missing.

Also skim the subjects of all commits in the range, including the "not mapped" ones. A
user-visible change sometimes lands without touching a mapped path. If so, add that path
to the section's `upstream` list.

## 3. Change the page

- Change only the values those facts live in: `content/en.toml` first, then
  `content/structure.toml` for anything language-independent (numbers, effect names, key
  chords, the `next` plan, versions).
- Then change the **same keys** in `es`, `zh-Hans`, `ar`, `ru`. Take terms from the
  editor's own catalogs (`src/apps/kt-app/i18n/<lang>.toml`), so the site and the program
  use the same words. Effect names and product names are not translated. Arabic uses
  `،` `؛` `؟`.
- Do not touch a section the diff does not concern. Do not polish wording that is still
  correct.
- Copy rules (`site-content`): every sentence states a fact about the editor. No slogans,
  no "X, not Y", no closing punchlines. The name is always lowercase **kinetren**.
- A new user-facing feature with nothing on the page: add it to the section it belongs to
  if it fits in a sentence. Otherwise list it in the report as undecided. Do not invent a
  section.

### Roadmap

- One entry per new tag **date**: `v26.10.25` and `v26.10.25.1` are one entry, `26.10.25`.
  Add the date to the front of `versions` in the roadmap section of `structure.toml`, and
  add the key `roadmap.v261025` to all five catalogs.
- The summary is one or two sentences on what changed **for a user** between the previous
  tag and this one. Take it from commit subjects and changed specs. Never name test
  numbers (`t804`), CI runs, rounds (`R.71`) or internal stage names. Tag messages are
  internal notes: do not copy them.
- Take items that shipped off `next` (and their `roadmap.n_*` keys in all catalogs). The
  plan comes from the editor's claims index (`openspec/changes/r71-ktprompts-index`).
  The owner's private `ktprompts*` files are never read into the site.

## 4. Import, build, check

```bash
python3 upstream.py import
```

```bash
python3 build.py
```

```bash
python3 build.py --check
```

```bash
python3 upstream.py facts
```

Repeat until all four pass. Typical failures:

- A guide page added or removed upstream: place it in or take it out of `[docs] pages`.
- The guide uses Markdown the build does not render: report it. It is fixed in the editor,
  not here.
- `facts` mismatch: the page lags the editor. Fix the page. Notes are not failures, but
  mention them in the report.

Imported files (`assets/shots/`, `assets/guide/`, `assets/kinetren.svg`) are never edited
here. The build refuses them if they differ from `upstream.lock`.

## 5. Commit and report

- One commit. English. First line: `Sync with kinetren <newest tag or short hash>`. The
  body lists the sections changed. Commit as the repository's configured identity. **No
  `Co-Authored-By` or any other AI/agent attribution lines** (owner's rule).
- Report to the owner, in Russian if they wrote in Russian:
  - per section, what changed on the page (one line each);
  - new versions added;
  - guide pages that changed;
  - `facts` notes;
  - anything left undecided and why.
- **Do not push.** A push to `main` publishes the site. Ask first.
