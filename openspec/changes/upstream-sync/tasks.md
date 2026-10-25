# Tasks

## 1. Upstream decisions (owner, 2026-10-26)

- [x] 1.1 Decide how the guide's capitalised "Kinetren" (a quote of the editor's menu item, about 47 occurrences in the editor's catalogs) meets the lowercase rule: the owner chose to exempt `dist/docs/` (design D9, `site-content` delta); verify the delta passes `openspec validate upstream-sync --strict`
- [x] 1.2 Ask whether the editor's `CLAUDE.md` gets a pointer to the site's update procedure: the owner declined (design D5); nothing is written in the editor repository

## 2. `upstream.py`: discovery, lock and import

- [x] 2.1 Create `upstream.py` with subcommands `status`, `import`, `facts`, options `--from`, `--rev` (default `HEAD`), `--json`, and checkout discovery `--from` → `KINETREN_CHECKOUT` → siblings `../kinetren`, `../kinotrain.9` whose `origin` is `kinetren/kinetren` (D2); verify `python3 upstream.py status` finds `../kinotrain.9` with no arguments, and with `KINETREN_CHECKOUT=/nonexistent` and `--from` unset in a temp copy of the repo with no siblings it exits non-zero naming `--from` and `KINETREN_CHECKOUT`
- [x] 2.2 Implement `import`: read every source with `git show <rev>:<path>` (shots from `[shot.*]`, images referenced by `docs/guide/*.md`, `CREDITS.md`, the icon, every `docs/guide/*.md`), check all first, then write `assets/shots/`, `assets/guide/`, `assets/kinetren.svg`, remove files no longer named, and write `upstream.lock` per D1; verify: `git -C ../kinotrain.9 status --porcelain` is identical before and after; every `assets/guide/*.md` is `cmp`-identical to `git show HEAD:docs/guide/<f>`; a `[shot.*]` pointing at a missing file makes it exit non-zero with `git status assets upstream.lock` unchanged
- [x] 2.3 Delete `import-shots.py`; verify `grep -rn import-shots --exclude-dir=openspec --exclude-dir=dist --exclude-dir=.git .` finds only `README.md` lines that task 7.1 rewrites

## 3. Section map and `status`

- [x] 3.1 Add `upstream = [...]` to every `[[section]]` in `content/structure.toml` with the D3 map, and a `[docs] pages` list in the guide order `getting-started, timeline, effects-and-automation, compositions-and-generators, morpher, export, shortcuts`; verify `python3 -c "import tomllib;s=tomllib.load(open('content/structure.toml','rb'));assert all('upstream' in x for x in s['section'])"` succeeds
- [x] 3.2 Implement `status`: commits `<lock>..<rev>` with subjects, new `v*` tags with dates, changed files grouped by section (prefix match on `upstream`), guide pages and screenshots changed, "not mapped" as counts per top directory, upstream paths missing at `<rev>`, a note when watched paths have uncommitted edits, a note when `origin/master` is ahead of `HEAD` (no fetch), and "up to date" with exit 0 when `<rev>` equals the lock; same data with `--json`; verify with `--rev` set to the lock commit (prints up to date), and with the lock temporarily pointing at `HEAD~20` (lists sections whose sources changed in those commits, and `--json` parses with `json.loads`)

## 4. `facts`

- [x] 4.1 Implement the D4 comparisons: `[lang]` vs editor `i18n/en.toml [lang]`; transitions vs `[trn.kind]`; video names vs `fx_registry.rs` category arms; audio names vs `name: "…"`; hero numbers vs list lengths; roadmap versions vs `v*` tags grouped by date; "cannot verify" when extraction yields nothing or duplicates; README Discord/site URL as non-failing notes; verify on the current sources it reports exactly the missing `26.10.25` version (plus the notes) and exits non-zero, and that a temp edit removing one name from `stats.transitions_list` is reported

## 5. Guide rendering in `build.py`

- [x] 5.1 Write the Markdown subset renderer of D6 (headings with GitHub anchor ids, paragraphs, lists with continuation and one nested level, pipe tables with `\|`, fenced code, strong/em/code, links, images) that fails with `file:line` on any other block construct; verify all seven imported pages render without error, and a temp guide copy with a `>` line, a setext heading and a raw `<div>` each fail naming the line
- [x] 5.2 Generate `dist/docs/index.html` and `dist/docs/<stem>/index.html` (D7 chrome: name → root dispatcher, index and GitHub links, no switcher, `lang="en"`, canonical, title, description), rewrite guide-to-guide links and check their anchors, send other relative links to `blob/<locked commit>/…`, images from `assets/shots/` with their sizes; fail on a page missing from or extra to `[docs] pages`; verify `dist/docs/export/index.html` has `id="kt-cli"`, `getting-started` links `https://github.com/kinetren/kinetren/blob/<commit>/README.md#install`, and a temp link to `export.md#nope` fails the build
- [x] 5.3 Add the guide URLs to `sitemap.xml` (no `hreflang`), include guide characters in the font subsets, and add guide typography (tables, code blocks, lists) to `assets/kt.css`; verify `sitemap.xml` lists 8 `/docs/` URLs and `python3 build.py --serve` shows `/docs/shortcuts/` with styled tables and no failed requests at 1440 px and 375 px (no horizontal scroll)
- [x] 5.4 Add `site.nav_docs` to all five catalogs (Docs, Documentación, 文档, التوثيق, Документация) and the header link `../docs/` before "Download" on every language page; verify `dist/ru/index.html` has `href="../docs/"` with the Russian label and the catalog validation passes

## 6. Lock verification in `build.py`

- [x] 6.1 Before building, compare every `upstream.lock` entry with its file's SHA-256 and fail naming each file that differs or is missing, and each file in `assets/shots/` or `assets/guide/` not in the lock; extend the "unreferenced image" check to accept images used by the guide; verify a one-byte edit to `assets/guide/export.md` and a stray `.webp` in `assets/shots/` each make `build.py` exit non-zero naming the file, and restoring them makes it pass

## 7. The "обнови" procedure and docs

- [x] 7.1 Rewrite `README.md`: replace the screenshot section with "Syncing with the editor" (`upstream.py status/import/facts`, `upstream.lock`, asking an agent to "update"), add "The user guide" (`/docs/`, import, checks), and list the new build checks; verify no command names `import-shots.py`, `site/` or `rust/`
- [x] 7.2 Write `.claude/skills/site-update/SKILL.md` with the D5 steps and trigger phrases in its description, and `CLAUDE.md` pointing to it with the house rules (copy rules, editor terms, English commits without attribution lines, no push without a go-ahead); verify both are English apart from the quoted trigger word and the skill appears in the session's skill list as `site-update`

## 8. First sync (acceptance run of the procedure)

- [x] 8.1 Run `python3 upstream.py import` at the editor's `HEAD` then follow the skill by hand: add the `26.10.25` roadmap entry in all five catalogs from the commits since the last version entry, bring the `keys` rows in line with `docs/guide/shortcuts.md` (Space double-tap, A/D and Home/End), and fix anything else `status` reports; verify `python3 upstream.py facts` exits 0, `python3 upstream.py status` reports up to date, and every catalog still passes `translated_min`
- [x] 8.2 Run `python3 build.py` and `python3 build.py --check`, and grep `dist/` for `Kinetren`/`Kinotrain`; verify both commands exit 0 and the grep finds matches only in `assets/kinetren.svg` and `docs/`
- [x] 8.3 Commit as the configured identity with an English message and no attribution lines, and report to the owner per section; do not push; verify `git log -1 --format=%B` has no `Co-Authored-By` and `git status --porcelain` is empty
