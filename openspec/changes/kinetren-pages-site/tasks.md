# Tasks

## 1. Repository hygiene

- [x] 1.1 Add `.gitignore` per design D8 and unstage bytecode (`git rm -r --cached __pycache__`); verify `git ls-files | grep -c pyc` prints 0 and `git status --porcelain` shows no `__pycache__`
- [x] 1.2 Rename the branch `master` → `main` (`git branch -m main`); verify `git branch --show-current` prints `main`

## 2. Import assets from kinetren

- [x] 2.1 Write `import-shots.py --from <checkout>` per design D3 (reads `[shot.*]`, checks every source first, copies shots, icon to `assets/kinetren.svg`, `CREDITS.md` to `assets/shots/`, deletes undeclared `*.webp`, usage message without `--from`); verify: without `--from` it exits non-zero with usage; against a temp copy of the checkout with one image removed it exits non-zero naming it and `git status assets/` is unchanged
- [x] 2.2 Update `content/structure.toml` slots to the D1 mapping (drop `render_progress`, `export` → `component = "list_and_shot"`, add `[site] releases`); verify `python3 -c "import tomllib;tomllib.load(open('content/structure.toml','rb'))"` succeeds
- [x] 2.3 Run `python3 import-shots.py --from /media/e/developer/kt.9/kinotrain.9`, remove `assets/shots/{en,ru,es,zh-Hans,ar}/`; verify `assets/shots/` holds exactly the 7 declared `.webp` + `CREDITS.md`, each `cmp`-identical to the checkout, and `cmp assets/kinetren.svg <checkout>/src/packaging/kinetren.svg` succeeds
- [x] 2.4 Delete `screenshots.py`; verify `grep -rn screenshots.py --exclude-dir=openspec --exclude-dir=dist .` finds only README lines that task 5.1 rewrites

## 3. Build changes in `build.py`

- [x] 3.1 Make the build self-contained: copy the icon from `assets/kinetren.svg` to `dist/assets/kinetren.svg`, generate the `<symbol id="kt">` from it (D4) instead of the `LOGO` constant, print paths relative to the repo root; verify `grep -n "ROOT.parent\|rust/" build.py` finds nothing
- [x] 3.2 Flatten shot resolution (D2): `shot_src` reads `assets/shots/<file>`, a missing file fails the build naming slot and file, assets copy to `dist/assets/shots/<file>`, OG cards from the shared hero; verify by temporarily renaming `assets/shots/morpher.webp`: `build.py` exits non-zero naming `morpher`; restore it
- [x] 3.3 Rename the product in generated markup (`<title>`, header, footer, JSON-LD, root dispatcher, icon links → `kinetren.svg`), drop the `kt26.08` label and `softwareVersion`, remove `.mast-ver` from `assets/kt.css` and rename its header comment; set `DEFAULT_BASE = "https://kinetren.github.io"`; verify `grep -ri "kinotrain\|kt26.08" build.py assets/kt.css` finds nothing
- [x] 3.4 Link the "Get it" button to `[site] releases`, keep the hero CTA on `#get` (D6); verify in the built `dist/en/index.html` that the button inside `id="get"` has the releases URL and the hero button `#get`
- [x] 3.5 Generate `dist/credits.html` from `assets/shots/CREDITS.md` and add the footer link with catalog key `site.credits` (D5); an unparseable row fails the build; verify the page lists all 9 works with author and license and that a deliberately broken row in a temp copy makes the build exit non-zero

## 4. Catalogs

- [x] 4.1 View each new image (`hero`, `timeline`, `video-fx`, `slowed-reverb-automation`, `morpher`, `media-bin`, `render-dialog`) and rewrite the matching `shot_alt`/`shot_cap`/`shot2_*` texts in `en.toml` to describe what each actually shows; apply the export key change (remove `export.shot2_alt`, `export.cap`; add `export.shot_cap`) and add `site.credits`; verify `build.py` reports no key errors for `en`
- [x] 4.2 Replace Kinotrain → kinetren and `.otio` project type → `.kt` in all five catalogs (and the `en.toml` header comment); translate the changed/new keys in `ru.toml`; copy the English values into `es`, `zh-Hans`, `ar`; verify `grep -ric kinotrain content/` prints 0 for every file and `build.py` passes catalog validation with `en` and `ru` still indexable and `es`/`zh-Hans`/`ar` still `noindex`

## 5. Docs and publishing

- [x] 5.1 Rewrite `README.md` in English for the standalone repo (build/check/serve, translating, `import-shots.py`, what the build checks, fonts and the host-specific `--check` caveat, SEO, publishing and the one-time owner setup); verify no command in it contains `site/` or `rust/`
- [x] 5.2 Add `.github/workflows/pages.yml` per D7; verify it parses (`python3 -c "import yaml;yaml.safe_load(open('.github/workflows/pages.yml'))"`), triggers on `push: main` and `workflow_dispatch`, uploads `path: dist`, and contains no build step

## 6. Build and verify end to end

- [x] 6.1 Run `python3 build.py` then `python3 build.py --check`; verify both exit 0 and fonts in `assets/fonts/` were regenerated with an updated `FONT-MANIFEST.txt`
- [x] 6.2 Run the spec greps on the result: `grep -ri kinotrain dist content assets/kt.css build.py` and `grep -r "kinotrain.app\|kt26.08" dist` find nothing; every absolute self-URL in `dist/` starts with `https://kinetren.github.io/`; `dist/assets/shots/` has no subdirectories
- [x] 6.3 `python3 build.py --serve` and open `/`, `/en/`, `/ru/`, `/ar/` and `/credits.html` in the browser pane; verify all images, fonts and styles load with no failed requests, Arabic renders joined, the root redirects by browser language, and the footer credits link works
- [x] 6.4 Stage everything and create the first commit on `main`; verify `git log --oneline` shows it and `git status` is clean. Pushing and creating `kinetren/kinetren.github.io` stay with the owner (README, design Migration Plan)
- [x] 6.5 `git clone` the local repo into a temp directory (no monorepo beside it) and run `python3 build.py --check` there; verify exit 0

## 7. Second round (owner, 2026-10-25)

- [x] 7.1 Translate comments, docstrings, build messages and `--help` in `build.py`, `assets/kt.css`, `content/structure.toml` and catalog headers to English; verify no Cyrillic outside translation values and `ru = "Русский"`
- [x] 7.2 Rewrite the en/ru copy as facts from the editor's README and code (D9); verify the former filler phrases are absent and `build.py` passes catalog validation
- [x] 7.3 Five stats with hover/focus lists (D10); verify the list counts are 26/18/33/4/5 and the box shows on focus in the browser
- [x] 7.4 Version log on the left with one `26:10:24` label each, plan on the right from the r71 claims index (D11); verify in the browser and that no `ktprompts` file is tracked or in history
- [x] 7.5 Live clock in the Download section (D12); verify the `[data-clock]` text changes over two seconds and matches local time
- [x] 7.6 GitHub and Discord links in the header and footer; Linux and Windows in copy, requirements and JSON-LD; verify the URLs and the Windows row in `dist/es/index.html`
- [x] 7.7 Start-aligned column, menu next to the name, rail spanning and scrolling with the document, also on `credits.html` (D13); verify rail height equals document height at 1440 px and no horizontal scroll at 375 px
- [x] 7.8 Lowercase "kinetren" everywhere, no CSS uppercase on the name (D15); verify the case-sensitive grep finds `Kinetren` only in the imported icon comment
- [x] 7.9 Language order `en, es, zh-Hans, ar, ru`; `/en/` follows the system language unless English was chosen (D14); verify the dispatcher cases ru→ru, zh-TW→zh-Hans, de→en, saved en→stay, hash kept
- [x] 7.10 `.gitignore` excludes `/ktprompts*`; verify `git log --all -- 'ktprompts*'` prints nothing
- [x] 7.11 Rebuild; verify `python3 build.py --check` is green and each batch is committed without a co-author trailer
- [x] 7.12 Translate `es`, `zh-Hans` and `ar` in full with the editor's terms (D16); verify the build reports all five languages indexed, the stat lists still count 26/18/33/4/5, and the Arabic and Chinese pages render with their fonts
