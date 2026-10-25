# Spec Delta

## Purpose

Keeping the site in step with the kinetren editor: a recorded sync point, a read-only tool
that reports and imports what changed in the editor since then, mechanical fact checks, and
the agent procedure that one request ("обнови" / "update") runs end to end.

## ADDED Requirements

### Requirement: The sync point is recorded in upstream.lock
The repository SHALL commit `upstream.lock`, a TOML file naming the editor repository
(`https://github.com/kinetren/kinetren`), the full commit hash the site was last synced to,
the newest `v*` tag reachable from that commit (empty if none), the commit date, and, for
every file imported from the editor, its path here, its source path there and its SHA-256.
Only `upstream.py import` SHALL write it.

#### Scenario: Lock after an import
- **WHEN** `python3 upstream.py import` runs against an editor checkout at commit `C`
- **THEN** `upstream.lock` names `C`, the newest `v*` tag reachable from `C`, and one entry per file under `assets/shots/`, `assets/guide/` and `assets/kinetren.svg`, each with a SHA-256 equal to that file's

### Requirement: The editor checkout is found and only read
`upstream.py` SHALL take the checkout from `--from <path>`, else from the environment
variable `KINETREN_CHECKOUT`, else from the first sibling directory of this repository
(`../kinetren`, `../kinotrain.9`) whose `origin` remote is `kinetren/kinetren`. If none is
found it SHALL exit non-zero saying how to pass the path. It SHALL read files from a
committed revision (`--rev`, default `HEAD`) and never from the working tree, and it MUST
NOT run any command that changes the checkout (fetch, pull, checkout, reset, commit,
writing files). If the checkout has uncommitted changes under a watched path, `status`
SHALL say that they are ignored.

#### Scenario: Uncommitted edits in the editor do not leak
- **WHEN** a file under the editor's `docs/guide/` has an uncommitted edit and `upstream.py import` runs
- **THEN** `assets/guide/` receives the committed content of that file, and the editor checkout's `git status` output is the same before and after

#### Scenario: No checkout found
- **WHEN** neither `--from` nor `KINETREN_CHECKOUT` is given and no sibling directory has the kinetren origin
- **THEN** `upstream.py status` exits non-zero and names `--from` and `KINETREN_CHECKOUT`

### Requirement: Sections declare the editor paths they are written from
Every `[[section]]` in `content/structure.toml` SHALL have an `upstream` list of editor
paths (files or directories, e.g. `openspec/specs/export`, `docs/guide/export.md`,
`src/apps/kt-app/i18n/en.toml`) that its facts come from. A section whose facts come from
nowhere in the editor SHALL say so with an empty list. Paths SHALL exist at the locked
commit; `upstream.py status` SHALL report a path that does not.

#### Scenario: A renamed editor path is reported
- **WHEN** a section's `upstream` names a path that does not exist at the editor's `HEAD`
- **THEN** `status` lists that section and path as missing upstream

### Requirement: status reports what changed since the lock
`python3 upstream.py status` SHALL print, for the range from the locked commit to the
target revision: the number of commits and their subject lines, every new `v*` tag with
its date, and the changed editor files grouped by the site section(s) whose `upstream`
covers them, plus the guide pages and screenshots that changed. Files not covered by any
section SHALL be listed under "not mapped". With `--json` it SHALL print the same as one
JSON object. When the target revision equals the lock it SHALL say the site is up to date
and exit 0.

#### Scenario: A change in export reaches the export section
- **WHEN** the editor has a commit after the lock that changes `docs/guide/export.md`
- **THEN** `status` lists that file under the `export` section and under the guide pages

#### Scenario: Nothing new
- **WHEN** the editor's `HEAD` is the locked commit
- **THEN** `status` reports the site as up to date and exits 0

### Requirement: import copies everything the site takes from the editor
`python3 upstream.py import` SHALL copy, byte for byte from the target revision: every
image named by a `[shot.*]` slot or by a guide page from `docs/images/`, the footage
credits `docs/images/CREDITS.md`, the icon `src/packaging/kinetren.svg`, and every
`docs/guide/*.md`; it SHALL remove from `assets/shots/` and `assets/guide/` the files no
longer named, and then rewrite `upstream.lock`. It MUST check every source first and
change nothing if one is missing.

#### Scenario: A missing source changes nothing
- **WHEN** a `[shot.*]` slot names a file that the target revision lacks
- **THEN** `import` exits non-zero naming it, and `assets/` and `upstream.lock` are unchanged

### Requirement: facts compares what can be checked mechanically
`python3 upstream.py facts` SHALL compare the site with the target revision and print
every mismatch, exiting non-zero if there is one: the `[lang]` self-names against the
editor catalog's `[lang]`; the transition list and count against the editor catalog's
`[trn.kind]`; the video and audio effect lists and counts against the editor's effect
registry; the five hero numbers against the lengths of their lists; and the roadmap
versions against the editor's `v*` tags. A fact it cannot extract from the editor SHALL be
reported as "cannot verify", not as a match.

#### Scenario: A new transition is caught
- **WHEN** the editor's `[trn.kind]` gains a 34th entry and the site still says 33
- **THEN** `facts` exits non-zero naming the transitions count and the missing name

#### Scenario: An untagged roadmap is caught
- **WHEN** the editor has tag `v26.10.25` and `structure.toml` lists no `26.10.25` version
- **THEN** `facts` exits non-zero naming `v26.10.25`

### Requirement: One request updates the whole site
When the owner asks an agent in this repository to update the site ("обнови", "update the
site", "sync with the editor"), the agent SHALL follow the procedure in
`.claude/skills/site-update/SKILL.md`, to which `CLAUDE.md` points: run `status`; for every
reported section read the editor diff of its `upstream` paths and bring that section's
facts in `content/en.toml` and `content/structure.toml` up to date, and change the same keys
in every other catalog with a translation that uses the editor's own terms; add a roadmap
entry for every new tag date and take shipped items off the plan; run `import`, `build.py`,
`build.py --check` and `facts` until all pass; commit; and report what changed per section
and what it could not decide. The agent MUST NOT push without the owner's go-ahead, MUST
NOT change a section the diff does not concern, and MUST follow the copy rules of
`site-content` (facts, never slogans). Commit messages SHALL be English and carry no AI or
agent attribution lines.

#### Scenario: Update after an editor round
- **WHEN** the owner says "обнови" after the editor gained a tag and changed `docs/guide/shortcuts.md`
- **THEN** the agent's commit adds the tag's version entry in all five catalogs, updates the keyboard section from the new guide, imports the guide, passes `build.py --check` and `facts`, and the report lists the `roadmap`, `keys` and docs changes

#### Scenario: Nothing to do
- **WHEN** the owner says "обнови" and `status` reports the site up to date
- **THEN** the agent says so and makes no commit
