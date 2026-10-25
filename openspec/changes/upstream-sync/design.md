# Design

## Context

- The editor is `kinetren/kinetren`, checked out next to this repository as
  `../kinotrain.9` (branch `master`, about 750 commits). Another agent works in that
  checkout all the time: right now it has uncommitted changes in `src/fixtures/`. Its
  docs are English (owner, 2026-10-21); the user guide is `docs/guide/` (7 pages,
  about 370 lines), the rest of `docs/` is for developers.
- The editor has had tags since 2026-10-25: `v26.10.25`, `v26.10.25.1` (lightweight).
  Their messages are internal round notes (CI runs, test numbers), not release notes.
- Only `import-shots.py --from <checkout>` links the two repositories today, and it copies
  from the working tree. Everything else on the page was written by hand from the editor's
  README, guide and history (archived change `kinetren-pages-site`, D9 and D11).
- `build.py` uses only the standard library, fontTools and Pillow. There is no Markdown
  package on the host (`markdown` and `mistune` are missing). CI never rebuilds, because
  font subsets depend on the host's fonts.
- The facts that can be read from the editor's source are already in machine-readable
  form there: `src/apps/kt-app/i18n/en.toml` `[lang]` (5 self-names) and `[trn.kind]`
  (33 transitions); `src/apps/kt-app/src/fx_registry.rs`, which has 26 video names as
  `"Name" => (k::fxreg::cat::…` match arms and 18 audio names as `name: "…"`.
- Drift we have already found (proposal, Why): the missing tag, the Space and A/D rows of
  the keyboard table compared with `docs/guide/shortcuts.md`, the Discord invite and the
  site URL in the editor's README. The guide also writes "Kinetren" in five places,
  quoting the editor's UI (D9).

## Goals / Non-Goals

**Goals:**
- One request ("обнови") gets an agent from "something changed in the editor" to a
  committed and checked site, touching only the sections the change concerns.
- Anything that can be compared mechanically is compared by a tool, not by an agent's
  reading.
- The guide on the site cannot differ from the guide in the editor at the locked commit.

**Non-Goals:**
- No automatic sync in CI and no scheduled job. The build is bound to one host, and prose
  and translations need judgement.
- No translation of the guide (owner, 2026-10-25: English only).
- No developer docs on the site (`architecture.md`, `file-format.md`, `media-index.md`,
  `features/`, `user-feedback.md`).
- No writes to the editor repository from this repository's tools or procedure.
- No change to how publishing works: a push to `main` deploys the committed `dist/`.

## Decisions

### D1. The sync point is a commit plus file digests, committed here

`upstream.lock` (TOML, at the repository root):

```toml
repository = "https://github.com/kinetren/kinetren"
commit = "3196cc51a9442240ec8518f4c44fef8d8ef7dc95"
tag = "v26.10.25.1"
date = "2026-10-25T15:42:58+03:00"

[[file]]
path = "assets/guide/export.md"
source = "docs/guide/export.md"
sha256 = "…"
```

The commit is the base for `status` ("what changed since") and for the GitHub links in the
guide. The digests let `build.py` refuse a hand-edited import without access to the
editor, so the build stays self-contained (`site-build`).
Rejected: the build reading the editor checkout to compare. That breaks "a fresh clone
builds", and CI has no checkout.
Rejected: a git submodule. It pins the whole editor (gigabytes of fixtures and history)
into the site's clone, and the owner would have to manage submodule updates by hand.

### D2. Read git objects, never the working tree; never fetch

`upstream.py` reads only through `git -C <checkout>`: `rev-parse`, `show <rev>:<path>`,
`ls-tree`, `diff --name-only <lock>..<rev>`, `log --format`, `tag --merged <rev> -l 'v*'`,
`status --porcelain -- <watched paths>`. It reads from committed revisions because the
editor's agent always has uncommitted work in progress, and a half-finished guide page
must not reach the site. It does not fetch, so it does not touch the refs that the other
agent and the owner work with. If `origin/master` is ahead of `HEAD` in the last fetched
refs, `status` says so and suggests pulling in the editor repository. It does not pull.
Checkout discovery (`--from`, `KINETREN_CHECKOUT`, siblings whose `origin` is
`kinetren/kinetren`) handles both the current folder name `kinotrain.9` and a future
`kinetren`.

### D3. Each section names its sources; `status` groups the diff by section

`[[section]]` gets `upstream = [...]`, a list of editor path prefixes. The guide and the
screenshots are mapped implicitly (`[docs]`, `[shot.*]`). The initial map:

| section | upstream |
|---|---|
| hero | `README.md`, `src/apps/kt-app/i18n/en.toml`, `src/apps/kt-app/src/fx_registry.rs` |
| why | `openspec/specs/video-plan`, `openspec/specs/export`, `openspec/specs/media-index` |
| edit | `docs/guide/timeline.md`, `openspec/specs/ui-timeline`, `openspec/specs/compositions` |
| playback | `openspec/specs/transport`, `docs/guide/shortcuts.md` |
| effects | `docs/guide/effects-and-automation.md`, `openspec/specs/video-fx`, `openspec/specs/audio-fx`, `openspec/specs/automation`, `src/apps/kt-app/src/fx_registry.rs` |
| more | `docs/guide/compositions-and-generators.md`, `openspec/specs/transitions`, `openspec/specs/generators` |
| morpher | `docs/guide/morpher.md`, `openspec/specs/morpher` |
| bin | `docs/guide/getting-started.md`, `openspec/specs/ui-reach`, `openspec/specs/media-index` |
| export | `docs/guide/export.md`, `openspec/specs/export` |
| care | `openspec/specs/durability`, `openspec/specs/project-format` |
| keys | `docs/guide/shortcuts.md` |
| roadmap | `openspec/changes/r71-ktprompts-index` (the plan); versions come from tags |
| get | `README.md`, `src/packaging`, `src/scripts/release-build.sh` |

Specs (`openspec/specs/<cap>/spec.md`) are the editor's contracts, so they are the most
reliable trigger for a change of behaviour. The guide is the most reliable source of user
wording. Most editor commits touch only tests and CI. `status` shows those as a count per
top directory under "not mapped", so a round of 30 internal commits does not bury the one
spec change. The map lives in `structure.toml` next to the sections, so adding a section
without saying where its facts come from is visible in review.
Rejected: one global list of watched paths. It says that something changed, not which
part of the page to reread.

### D4. `facts`: what a tool can compare

| fact | site | editor |
|---|---|---|
| language self-names | `[lang]` in every catalog | `i18n/en.toml` `[lang]` |
| transitions | `stats.transitions_list`, the number in `structure.toml` | `i18n/en.toml` `[trn.kind]` values |
| video effects | `[fx] names`, `stats.vfx_list`, number | `fx_registry.rs` category match arms |
| audio effects | `stats.afx_list`, `effects.list_body`, number | `fx_registry.rs` `name: "…"` |
| list lengths | hero numbers | lengths of the `stats.*_list` values |
| versions | `[[section]] roadmap versions` | `git tag --merged <rev> -l 'v*'`, grouped by date |

Names are compared as sets and counts; order is the site's choice. The `fx_registry.rs`
extraction is a regex over Rust source, so it is a heuristic. When it finds no names or a
name repeats, the fact is reported "cannot verify" instead of "ok", which turns a silent
false match into a visible gap. Notes that do not fail the run: the Discord invite and the
site URL in the editor's README compared with `structure.toml`. They are not site facts,
but the owner should see them.
Not compared mechanically: key chords. The guide's shortcut table is prose
("**A** / **Home**"), and parsing it would give the guide a format it never promised. The
`keys` section is mapped to `shortcuts.md`, and the agent rereads it.

### D5. The procedure is a project skill; the trigger is in `CLAUDE.md`

`.claude/skills/site-update/SKILL.md` holds the procedure from `upstream-sync`
("One request updates the whole site"). Its description names the trigger phrases
("обнови", "update the site", "sync with the editor"), so the skill is picked
automatically and can also be run as `/site-update`. `CLAUDE.md` (new) says the same in
one paragraph and lists the house rules an agent here must keep: copy rules, editor terms
for translations, English commits as the configured identity without attribution lines,
no push without a go-ahead. The skill's steps:

1. `upstream.py status --json`. If up to date, say so and stop.
2. For every reported section, read `git -C <checkout> diff <lock>..<rev> -- <upstream>`
   and the guide and spec text, and list the facts on the page that changed. Change only
   those values: `en.toml` first, then the same keys in `es`, `zh-Hans`, `ar`, `ru`, with
   terms taken from the editor's `i18n/<lang>.toml`.
3. Roadmap: one `roadmap.vYYMMDD` key per new tag date, summarised from the commit
   subjects and changed specs between that tag and the previous one, without test or CI
   numbers. Take shipped items off `next`.
4. `upstream.py import`, `build.py`, `build.py --check`, `upstream.py facts`. Repeat until
   all pass. A guide page that is new or removed is placed in or taken out of
   `[docs] pages`.
5. Commit (one commit, English, first line "Sync with kinetren <tag or short hash>").
   Report per section what changed, plus anything left undecided (for example a feature
   with no wording in the guide yet).
6. Ask before pushing.

Rejected: a script that rewrites prose from the diff. The catalogs are hand-written
facts in five languages, and only a reader can tell that "Space twice stops" became "a
second tap returns to the start".
Rejected: doing it from the editor repository. Its agent cannot write here without the
owner's permission, and its rules (OpenSpec rounds, `finish.sh`) are unrelated to the
site. From the editor side, one line in its `CLAUDE.md` is enough: after a round that
changes user-visible behaviour, `docs/guide/` or tags, the report could end with "site:
say 'обнови' in kt.9.site". The owner declined it on 2026-10-26: they decide when to
update the site.

### D6. The guide: byte-identical import, Markdown subset rendered by `build.py`

`upstream.py import` copies `docs/guide/*.md` to `assets/guide/` and every
`../images/<file>` they show into `assets/shots/` (adds `titles.webp`,
`transitions.webp`). `build.py` renders a strict subset of CommonMark/GFM: ATX headings,
paragraphs, `-`/`*` and `1.` lists with continuation lines and one nested level (as in
`effects-and-automation.md`), pipe tables with `\|`, fenced code, `**strong**`, `*em*`,
`` `code` ``, inline links and images. Anything else fails with `file:line`. Inline text is
HTML-escaped, so raw HTML can never pass through.
Rejected: the `markdown` package. It is not installed on the host and would be the only
non-font dependency, and a version change would alter output bytes, which `--check`
relies on not happening.
Rejected: rendering through the GitHub API. Network access during the build, and the
build would depend on GitHub's output.
Anchor ids follow GitHub's rule (lowercase; drop everything except letters, digits,
spaces, `-` and `_`; spaces → `-`; repeats get `-1`, `-2`), so `export.md#kt-cli` works on
GitHub and on the site alike.

### D7. URLs and page chrome of the guide

`/docs/` and `/docs/<stem>/`, not `/en/docs/`. The guide exists in one language, and a
path under `/en/` would suggest translated siblings and a switcher that would lead
nowhere. Guide pages use the site's CSS, fonts and rail. Their header has the product
name, which links to the root dispatcher `../../` (or `../` from the index), so a
Russian visitor returns to `/ru/`. The header also links the guide index and GitHub. No
language switcher. The landing header gets `site.nav_docs` before "Download". The five
translations: Docs, Documentación, 文档, التوثيق, Документация.
Links to repository files outside `docs/guide/` go to GitHub at the locked commit, not
`blob/master`, so the link shows the text the site was built from.

### D8. Revision: versions from tags instead of build dates — owner's choice on 2026-10-25

The archived D11 said: "versions are build dates while no GitHub release exists". Tags
now exist, and the owner chose them over GitHub releases (no `gh` on the host, and the
tags are the editor's own record) and over hand-picked dates. One entry per tag date:
the `.N` suffix is a same-day rebuild. The first tag-based entry is `26.10.25`. Older
entries (`26.10.24` … `26.08.22`) stay as they are, because no tags exist before
2026-10-25. Tag messages are internal and are not copied. The summary is the agent's,
written under the copy rules.

### D9. Revision: imported guide text keeps its spelling, `dist/docs/` is exempt from the lowercase rule — owner's choice on 2026-10-26

The plan was to fix the capitalised "Kinetren" in `docs/guide/export.md` upstream. When
the change was applied, it turned out that the word is not a typo in the guide. The guide
quotes the editor's UI ("File → Import older Kinetren project…",
`menu.file.import_older` in `i18n/en.toml`), and the capitalised form occurs about 47
times across the editor's five catalogs. A fix in the guide alone would make the guide
misquote the program. The owner chose to let the site show the guide exactly as written:
the "no `Kinetren`" rule of `site-content` covers the site's own text and exempts
`dist/docs/`, the same way it already exempts the imported icon. When the editor
lowercases its UI, the next "обнови" carries the change over.
Rejected: lowercasing at render time. The site would show text that exists nowhere in the
editor.
Rejected: blocking the guide until the editor renames its UI strings. That is a separate
change in the editor, and the owner did not ask for it.

## Risks / Trade-offs

- [The section map misses a source, and a change slips past] → "not mapped" lists every
  changed top directory with a count, and the skill tells the agent to read the commit
  subjects of the whole range, not only the mapped diffs.
- [An editor round is large (dozens of commits)] → the agent works from specs and the
  guide (contracts and user wording), not from code. Undecided items go into the report
  instead of the page.
- [The `fx_registry.rs` layout changes, and the regex finds nothing] → reported as
  "cannot verify". The agent then checks by reading, and the extraction is updated in a
  later change.
- [Translations of changed keys drift in quality] → terms come from the editor's own
  catalogs. The build still enforces key sets, markup and Arabic punctuation.
- [The guide shows "Kinetren" where the site writes "kinetren"] → the guide quotes the
  editor's UI, and the site follows when the editor changes it (D9).
- [The checkout is behind GitHub] → `status` reports it from the last fetched refs. The
  owner pulls in the editor repository.
- [Guide pages are English on every language's menu] → the "Docs" label is translated.
  The guide's `<html lang="en">` tells browsers to offer translation.

## Migration Plan

1. Land `upstream.py`, `upstream.lock`, the section map, the guide renderer and the lock
   check. Remove `import-shots.py`, then run the first `import` at the editor's `HEAD`.
2. Run the procedure once by hand as its acceptance test. It adds the `26:10:25` entry and
   fixes the keyboard rows that differ from `shortcuts.md`.
3. Update `README.md`, then build, check and commit. Publishing is the owner's push.

Rollback: revert the commit. `dist/` returns to the previous build, and nothing outside
this repository changed.
