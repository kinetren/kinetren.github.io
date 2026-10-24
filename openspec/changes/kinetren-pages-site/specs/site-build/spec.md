# Spec Delta

## Purpose

Generating the multilingual kinetren landing page from formal sources (`content/`,
`assets/`) into a static `dist/` tree, with the checks that keep translations, fonts and
the committed output honest. Bootstrapped from the behaviour the site already had in the
monorepo (owner rounds R.19–R.22).

## ADDED Requirements

### Requirement: The site is generated from structure and per-language catalogs
`build.py` SHALL produce `dist/` from `content/structure.toml` (page form: section order,
components, image names, key chords, effect names, numbers — everything identical across
languages), `content/<lang>.toml` (prose only) and `assets/`. `dist/` SHALL contain one page
per language at `dist/<lang>/index.html` for every code in `[site] langs`, a root
dispatcher `dist/index.html`, shared assets under `dist/assets/` (one content-hashed CSS
file, font subsets, images), `sitemap.xml` and `robots.txt`. Nothing in `dist/` is edited by
hand.

#### Scenario: A full build writes every language and the shared assets
- **WHEN** `python3 build.py` runs on the committed sources
- **THEN** it exits 0 and `dist/` contains `index.html`, `en/ ru/ es/ zh-Hans/ ar/` each with `index.html`, `assets/kt.<hash>.css`, `assets/fonts/*.woff`, `sitemap.xml` and `robots.txt`

### Requirement: Catalogs are validated against the English reference
`content/en.toml` SHALL define the set and order of keys. The build MUST fail, naming the
catalog and key, when a key is missing from a catalog or present only there; when a value
is empty; when the `{0}`/`{1}` placeholder set differs from English; when a value contains
a tag outside `<em> <strong> <kbd> <code> <br>` or an unpaired tag; when an Arabic value
contains an ASCII comma, semicolon or question mark; or when any text uses a character
absent from every built font subset. A value identical to English SHALL be a warning only.

#### Scenario: A missing key fails the build
- **WHEN** a key present in `en.toml` is deleted from `ru.toml` and `build.py` runs
- **THEN** it exits non-zero and the report names `ru` and that key

#### Scenario: An ASCII comma in Arabic fails the build
- **WHEN** an `ar.toml` value contains `,` and `build.py` runs
- **THEN** it exits non-zero naming the key

### Requirement: Translation coverage decides indexing
The build SHALL compute, per language, the share of values that differ from English. A
language below `[site] translated_min` SHALL still be built but its page MUST carry
`<meta name="robots" content="noindex, follow">` and it MUST be left out of `sitemap.xml`
and of every `hreflang` list. Every page SHALL list `x-default` pointing at `/en/`.

#### Scenario: An untranslated catalog is noindex
- **WHEN** the site is built with a copy of `es.toml` whose values are mostly identical to English
- **THEN** `dist/es/index.html` has the noindex meta, and neither `sitemap.xml` nor `dist/en/index.html` mentions `/es/`

### Requirement: The visitor gets their system language
Languages SHALL be listed in the order `en`, `es`, `zh-Hans`, `ar`, `ru` (switcher, root
page, hreflang, sitemap). The root page `dist/index.html` SHALL redirect to a language
chosen in this order: the `localStorage["lang"]` value if it is a known language code (not
`auto`) — it is written when the visitor picks a language in the switcher — then the first
of `navigator.languages` whose base subtag matches a known language (`zh-*`, including
`zh-TW`/`zh-HK`, maps to `zh-Hans`), else `[site] default`. The default-language page
(`/en/`) SHALL apply the same choice and go to the chosen language when it differs, keeping
the URL fragment, so English is shown only to those who picked it or whose system language
is English or unsupported. The other language pages MUST NOT redirect. Without JavaScript
the root page SHALL show links to all languages.

#### Scenario: A Taiwanese browser lands on simplified Chinese
- **WHEN** the root page is opened with no saved language and `navigator.languages = ["zh-TW"]`
- **THEN** it navigates to `zh-Hans/`

#### Scenario: Unknown language falls back to English
- **WHEN** `navigator.languages = ["de-DE"]` and nothing is saved
- **THEN** the root page navigates to `en/` and `/en/` stays where it is

#### Scenario: A Russian system leaves the English page
- **WHEN** `/en/#get` is opened with `navigator.languages = ["ru-RU"]` and nothing saved
- **THEN** it navigates to `../ru/#get`

#### Scenario: English chosen in the switcher stays English
- **WHEN** `/en/` is opened with `navigator.languages = ["ru-RU"]` and `localStorage["lang"] = "en"`
- **THEN** it does not navigate

#### Scenario: Explicit language URLs do not move
- **WHEN** `/ru/` is opened with `navigator.languages = ["en-US"]`
- **THEN** it does not navigate

### Requirement: Font subsets are built from the characters actually used
The build SHALL subset Latin/Cyrillic, monospace, CJK and Arabic fonts to exactly the
characters used across all catalogs and structure, keeping the Arabic joining features
(`init/medi/fina/isol` and related), write them to `assets/fonts/` with a
`FONT-MANIFEST.txt`, and reference them from the generated CSS.

#### Scenario: Arabic text keeps its joined forms
- **WHEN** `dist/ar/index.html` is viewed in a browser
- **THEN** Arabic words render as joined script, not isolated letter forms

### Requirement: The build is reproducible and checkable
Two builds from the same sources SHALL produce byte-identical `dist/` trees.
`build.py --check` SHALL build into a temporary directory, compare it file by file with
`dist/`, list every missing, extra and differing file, and exit non-zero on any difference.

#### Scenario: Check passes right after a build
- **WHEN** `python3 build.py` runs and then `python3 build.py --check`
- **THEN** the check exits 0

#### Scenario: Check catches a stale dist
- **WHEN** a catalog value is edited and `build.py --check` runs without rebuilding
- **THEN** it exits non-zero and lists the affected pages as differing

### Requirement: The build is self-contained in this repository
`build.py` MUST NOT read any file outside this repository's directory other than the
system fonts it subsets. The icon, screenshots, styles and content SHALL all come from
this repository.

#### Scenario: Build in a fresh clone
- **WHEN** the repository is cloned alone into an empty directory (no monorepo beside it) and `python3 build.py --check` runs on a host with the required fonts and Python packages
- **THEN** it exits 0

### Requirement: The site is viewed through a local server and stays idle
`build.py --serve [PORT]` SHALL build and then serve `dist/` over HTTP on `127.0.0.1`
(port 8000 by default) until interrupted. The page MUST NOT run infinite animations over
`filter`, `mix-blend-mode` or `backdrop-filter`; an idle open page SHALL NOT keep the
compositor busy.

#### Scenario: Serve mode shows images and fonts
- **WHEN** `python3 build.py --serve` runs and `http://127.0.0.1:8000/en/` is opened
- **THEN** the page loads with its screenshots, styles and fonts and no failed asset requests
