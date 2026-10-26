# Tasks

## 1. Remove the keyboard section

- [x] 1.1 In `content/structure.toml` delete the `[[section]] id = "keys"` block and the `[keys.*]` tables with their header comment; move roadmap to `timecode = "00:01:58"`, `slab = "plain"` and download to `timecode = "00:02:12"`, `slab = "none"` (D2); verify `python3 -c "import tomllib;s=tomllib.load(open('content/structure.toml','rb'));assert 'keys' not in s and all(x['id']!='keys' for x in s['section'])"` succeeds and the section timecodes printed in order step by 14 s up to `00:02:12`
- [x] 1.2 Delete the `[keys]` table from all five catalogs, keeping `roadmap.n_keys`; verify `grep -n '^\[keys\]' content/*.toml` prints nothing and `grep -c '^n_keys' content/*.toml` prints 1 for each file
- [x] 1.3 Remove `c_keys`, its `COMPONENTS` entry and the chord loop in `collect_chars` from `build.py`, and the `.keys` rules (the "keyboard" block and `.keys>*` in the `min-width:0` list) from `assets/kt.css`; verify `grep -n 'c_keys\|struct\["keys"\]' build.py` and `grep -n '\.keys' assets/kt.css` print nothing

## 2. `<kbd>` in the guide

- [x] 2.1 In `GuidePage.inline` cut out `<kbd>…</kbd>` pairs before the raw-HTML check and restore them escaped after the Markdown pass; drop the tags in `md_plain` (D3); verify with a temp guide copy (lock re-hashed) that a cell `<kbd>Ctrl</kbd>+<kbd>S</kbd>` renders as `<kbd>Ctrl</kbd>+<kbd>S</kbd>`, that `` `<kbd>x</kbd>` `` stays literal code, and that `<span>x</span>`, an unclosed `<kbd>` and a nested `<kbd><kbd>` each fail naming the line
- [x] 2.2 Check the key cap look inside guide tables (`.doc-table`, `.doc-body`) and add a rule only if the global `kbd` style breaks there (line height, wrapping in the first column); verify in a temp build of a `shortcuts.md` copy using `<kbd>` at 1440 px and 375 px: caps match the landing page, no horizontal page scroll

## 3. References and docs

- [x] 3.1 Update `README.md` (the `structure.toml` row no longer lists key chords; "The user guide" names `<kbd>` as the one HTML tag the guide may use) and `.claude/skills/site-update/SKILL.md` (no "key chords" in the list of language-independent values); verify `grep -n -i 'key chord' README.md .claude/skills/site-update/SKILL.md build.py content/structure.toml` prints nothing
- [x] 3.2 Hand the owner `editor-prompt.md` (this change directory) in the final report, quoted in full so it can be pasted into the editor session; verify the report contains it

## 4. Build and commit

- [x] 4.1 Run `python3 build.py`, `python3 build.py --check` and `python3 upstream.py facts`; verify the two builds exit 0 and `facts` fails on nothing but the missing roadmap entry for v26.10.26 (the editor tagged the locked commit after this change was planned; adding it is a separate "обнови", owner 2026-10-26), `grep -l 'id="keys"\|class="keys"' dist -r` prints nothing, and `dist/docs/shortcuts/index.html` exists
- [x] 4.2 View `/ru/` and `/ar/` around the care → roadmap → download sections at 1440 px and 375 px; verify the slabs alternate, the timecodes read 00:01:44, 00:01:58 and the live clock, and there is no horizontal scroll
- [x] 4.3 Commit as the configured identity with an English message and no attribution lines; do not push; verify `git log -1 --format=%B | grep -ci co-authored` prints 0 and `git status --porcelain` is empty
