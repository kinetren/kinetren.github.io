# Kinetren landing page

The website of [Kinetren](https://github.com/kinetren/kinetren), a non-linear video
editor for Linux: a static site in five languages, built entirely from the sources in this
repository and served by GitHub Pages at **https://kinetren.github.io**.

Nothing in `dist/` is edited by hand — the next build overwrites it.

```bash
python3 build.py
```

```bash
python3 build.py --check
```

```bash
python3 build.py --serve
```

`build.py` writes the site to `dist/`; `--check` builds into a temporary directory and
fails if `dist/` differs from what the sources produce; `--serve` builds and serves
`dist/` at http://127.0.0.1:8000/ (pass a port to change it). View the site through
`--serve`, not by opening a file: a viewer that loads one HTML file without its
neighbours shows no images and no fonts.

Requirements: Python 3.11+, `fontTools` and `Pillow`
(`sudo apt install python3-fonttools python3-pil`), and the system fonts listed under
[Fonts](#fonts).

## What lives where

| | |
|---|---|
| `content/structure.toml` | the page's form: section order, components, image slots, key chords, effect names, numbers, the releases link |
| `content/en.toml` | **the reference catalog**: defines the set of keys |
| `content/<lang>.toml` | translations; the language codes are the editor's: `en`, `ru`, `es`, `zh-Hans`, `ar` |
| `assets/kt.css` | styles — a source, edited by hand |
| `assets/shots/*.webp` | screenshots, one set for every language, **imported** from Kinetren |
| `assets/shots/CREDITS.md` | authors and licenses of the footage in the screenshots, **imported** |
| `assets/kinetren.svg` | the icon, **imported** (favicon and the inline logo) |
| `assets/fonts/` | font subsets, **generated** by the build, plus `FONT-MANIFEST.txt` |
| `dist/` | the build output, committed; **the root that is published** |

The boundary is simple: `structure.toml` holds everything that is the same in every
language, the catalogs hold only prose. A translator cannot break the layout, and a layout
change does not touch five files.

## Translating

Take `content/<lang>.toml` and translate the values. The set of keys is fixed by
`en.toml`; the build fails if a key is missing or extra.

Values may contain only the inline markup `<em> <strong> <kbd> <code> <br>`; everything
else is escaped. Put emphasis where your language wants it, not where it is in English.

Not translated: `Kinetren`, `MP4`, `H.264`, `AAC`, `FFmpeg` and effect names (`Pan`,
`Blur`, `VHS`, `Slowed+Reverb`, `Morpher`) — rule 4 of the editor's
`src/apps/kt-app/i18n/README.md`. The `[lang]` section holds the languages' self-names and
is byte-identical in every catalog.

For Arabic, use the Arabic punctuation `،` `؛` `؟` instead of ASCII — the build fails
otherwise, as the editor's does. Write text in **logical** order; the browser does bidi.

### A language indexes itself

The build counts the share of values that differ from English. A catalog translated less
than `translated_min` (90 % by default, set in `structure.toml`) is still built, but gets
`noindex` and is left out of `sitemap.xml` and `hreflang`. Once it is translated, the
language is indexed from the next build — nothing is marked by hand.

Today `en` and `ru` are done; `es`, `zh-Hans` and `ar` are placeholders with English text.

## What the build checks

Errors (the build fails):

* a key is missing from some catalog, or present there but not in `en.toml`;
* a value is empty;
* the set of `{0}`/`{1}` placeholders differs from English;
* a value has a tag outside the allowed list, or an unpaired one;
* an Arabic value has an ASCII comma, semicolon or question mark;
* the text uses a character that no built font subset has;
* an image slot in `structure.toml` names a file that is not in `assets/shots/`;
* a row of `assets/shots/CREDITS.md` cannot be parsed.

Warning: a value is identical to English — that is what the readiness of a language is
computed from.

## Screenshots

The screenshots are not taken here. They are the editor's own showcase shots: Kinetren's
`src/scripts/readme-shots.py` drives the real editor with the English UI on free footage
and publishes them in its `docs/images/`. This site uses one English set for every
language. To refresh them from a Kinetren checkout:

```bash
python3 import-shots.py --from ../kinetren
```

```bash
python3 build.py
```

`import-shots.py` copies, byte for byte, every image that a `[shot.*]` slot in
`content/structure.toml` declares, plus the icon (`src/packaging/kinetren.svg`) and the
footage credits (`docs/images/CREDITS.md`), and deletes images no slot declares. It checks
every source first and changes nothing if one is missing. Image sizes are data: `build.py`
reads them from the files.

To show another screenshot, add a `[shot.<slot>]` entry naming a file from the editor's
`docs/images/`, reference the slot from a section, and re-import.

The footage is CC BY or public domain; `build.py` turns the imported `CREDITS.md` into
`dist/credits.html`, linked from the footer of every page.

## Fonts

`build.py` subsets the fonts itself, to exactly the characters used across all catalogs:
Latin and Cyrillic from the variable Ubuntu font, CJK from `NotoSansCJK-Regular.ttc`
(face 2), Arabic from `NotoSansArabic-Regular.ttf` with the joining features
`init/medi/fina/isol` — without them the letters fall apart into isolated forms.
On Ubuntu: `fonts-ubuntu`, `fonts-noto-cjk`, `fonts-noto-core`.

The format is **WOFF, not WOFF2**: `pyftsubset --flavor=woff2` needs the `brotli` module.
Install `python3-brotli` and change `--flavor=woff` to `woff2` in `subset()` if you want
WOFF2.

The build is reproducible: `SOURCE_DATE_EPOCH` is pinned, otherwise fontTools stamps the
build time into the font. It is reproducible **on one machine**: a host with different
versions of these font files produces different subsets, so `--check` is meaningful on the
host that built the committed `dist/`. CI therefore never rebuilds.

## SEO

The language is in the path (`/ru/`, not `?lang=ru`); every page has its own `canonical`,
`title`, `description`, Open Graph card and JSON-LD `SoftwareApplication`. `hreflang`
lists only the indexable languages plus `x-default` pointing at `/en/`.

The root `/` is a dispatcher: it reads `localStorage["lang"]` (the same key and values
the editor writes), then `navigator.languages`, and goes to the matching language. The tag
is parsed as in the editor's `src/apps/kt-app/src/i18n/detect.rs`: the region is cut off,
`zh-*` (including `zh-TW`/`zh-HK`) goes to Simplified, anything unknown to English.
Without JavaScript it shows links to all five languages, so neither a person nor a crawler
gets stuck.

The base URL is `https://kinetren.github.io`; it goes into canonical, hreflang, og:url,
og:image, the sitemap and robots.txt. All links between pages and to assets are relative.
For another host, build with `python3 build.py --base-url https://example.org`.

## Publishing

`.github/workflows/pages.yml` deploys the committed `dist/` to GitHub Pages on every push
to `main` (and on a manual run). It uploads `dist/` as it is and does not rebuild — so run
`python3 build.py` and `python3 build.py --check` before committing.

One-time setup on GitHub, by the owner of the `kinetren` organisation:

1. Create the repository `kinetren/kinetren.github.io` (the name must be exactly this for
   the site to live at the root of `kinetren.github.io`).
2. Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Add it as the remote of this repository and push `main`:

```bash
git remote add origin git@github.com:kinetren/kinetren.github.io.git
```

```bash
git push -u origin main
```

To roll back, revert the commit and push, or re-run the workflow on an earlier commit;
Pages keeps serving the last successful deployment meanwhile.
