# Tasks

## 1. Update strip: data and checks

- [ ] 1.1 Add `[updates] entries = ["26.11.02", "26.11.01"]` with its comment to `content/structure.toml`. Verify that `python3 build.py` reads it: printing the parsed list in a dry run shows both ids.
- [ ] 1.2 Add `[updates]` to `content/en.toml`. It holds the 26.11.02 and 26.11.01 entries (named features from the two syncs, design D3), plus `more`, `link` and `close`. Verify each entry is ≤ 160 characters and contains no `!`.
- [ ] 1.3 Add the same keys to `es`, `zh-Hans`, `ar` and `ru`, using the editor's terms (`src/apps/kt-app/i18n/<lang>.toml`) and Arabic `،` `؛` `؟`. Verify that `python3 build.py` reports no missing or extra key.
- [ ] 1.4 In `build.py`, fail the build when an `[updates] entries` id has no `updates.u<id>` key, when an English entry is over 160 characters, or when an entry has `!` or a banned word (design D3). Verify by temporarily adding "Big update!" to an entry: the build exits non-zero and names the language and key. Revert it afterwards.

## 2. Update strip: page

- [ ] 2.1 Render the strip in `build_page`, before the hero section (design D4): every entry hidden, the "more" line, the `../docs/whats-new/` link and the close button, with `data-newest` and `data-id` attributes. Verify that `dist/en/index.html` contains one `<aside class="upd" hidden` with two entry paragraphs.
- [ ] 2.2 Add the strip logic to `PAGE_JS`: read `kt-seen` once at load (try/catch), pick the entries to show, and on close or on link click store the newest id. No timer, no fetch. Verify in the browser pane at `python3 build.py --serve` that the three cases of the `site-content` scenarios (`261026`, newest, none) behave as written.
- [ ] 2.3 Style the strip in `assets/kt.css` (design D5): in the flow above the hero, mono timecode, 44 px close target, no animation. Verify with screenshots at 1440 px and 375 px, and on `/ar/` (RTL), that the strip wraps and covers neither the headline nor the download panel.
- [ ] 2.4 Check the storage and idle rules of the `site-build` delta: only `lang` and `kt-seen` in `localStorage`; with storage blocked (override `localStorage` to throw), the newest entry is shown with no console error; with the strip open and the page scrolled to `#roadmap` for 10 seconds, nothing is animated and there is no extra request. Record the results in this task.

## 3. Screenshots from the editor

- [x] 3.1 Hand `editor-prompt.md` of this change to the owner, who gives it to the editor's agent. Verify that the editor commit at the checkout's `HEAD` has `docs/images/fx-datamosh.webp`, `fx-camera-isp.webp`, `fx-vhs-tape.webp` and `masks.webp` (`git -C ../kinotrain.9 ls-tree HEAD docs/images/`). The next tasks wait for this.
- [x] 3.2 Declare the four `[shot.*]` slots and `gallery` in the effects section of `content/structure.toml` (design D1). Use the file names the editor actually committed. Verify that `python3 upstream.py import` copies the four files and updates `upstream.lock`.
- [x] 3.3 Render the gallery in `c_effects` (as built: the three simulations one per row at the column width, each with a short caption and a description; the masks shot beside its text — see design D1). Verify that `dist/en/index.html` has the four `<img>` with `width`/`height`, and that at 375 px `scrollWidth` equals the viewport width.
- [x] 3.4 Write `effects.g_<slot>_alt` and `effects.g_<slot>_cap` in all five catalogs, describing what each image shows (settings, clip, which half is which), and look at each image before writing its text. Verify that the build passes and the captions contain none of the banned words from the `site-content` scenario.

## 4. Future "обнови"

- [ ] 4.1 Add the update-entry step and the shot-request step to `.claude/skills/site-update/SKILL.md` (design D6), and the two outputs to the "обнови" paragraph of `CLAUDE.md`. Verify by reading that the steps sit between "Change the page" and "Import, build, check", and that the report list names the entry and the request path.
- [ ] 4.2 Create `editor-requests/` with a `README.md` of two sentences on what goes there and who reads it. Verify that `git status` shows it and that `.gitignore` does not exclude it.

## 5. Specs and finish

- [ ] 5.1 Run `python3 build.py`, `python3 build.py --check` and `python3 upstream.py facts`. Verify that all three pass.
- [ ] 5.2 Commit after each group (1–2, 3, 4) with English messages and no attribution lines. Verify with `git log -3`.
- [ ] 5.3 Archive the change (`/opsx:archive`) once groups 1–4 are done. Verify that `openspec/specs/site-content`, `site-build` and `upstream-sync` hold the new requirements and that `openspec validate --specs` passes.
