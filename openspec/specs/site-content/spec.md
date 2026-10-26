# site-content

## Purpose

What the landing page shows about the product: its name and icon, the facts and numbers,
the screenshots and where they come from, the attribution those screenshots require, the
version log and plan, the links, the page layout, and where the download button leads.

## Requirements

### Requirement: The page names the product kinetren, in lowercase
Every generated page, in every language, SHALL name the product **kinetren**, written in
lowercase everywhere — also at the start of a sentence and in titles: header, footer,
`<title>`, Open Graph title, JSON-LD `name`, the root dispatcher, `credits.html`, alt texts
and all catalog prose. No style SHALL transform the name to upper case. The former name
`Kinotrain` and the capitalised `Kinetren` MUST NOT appear in `dist/`, `content/`,
`assets/kt.css`, `build.py` or `README.md`. Two exceptions hold imported editor text as
written: the comment inside the byte-identical `assets/kinetren.svg`, and the guide pages
under `dist/docs/`, which quote the editor's own UI strings (for example the menu item
"Import older Kinetren project…") and change only when the editor changes them. The favicon and inline logo SHALL be the
kinetren icon (`assets/kinetren.svg`, the same file as the editor's
`src/packaging/kinetren.svg`), published as `dist/assets/kinetren.svg`. Facts the rename
changed SHALL be correct: the installer registers the `.kt` project type.

#### Scenario: No former or capitalised name in the output
- **WHEN** the site is built and `dist/` (except `assets/kinetren.svg` and `docs/`), `content/`, `assets/kt.css`, `build.py` and `README.md` are searched case-sensitively for `Kinotrain` and `Kinetren`
- **THEN** there are no matches

#### Scenario: The header shows the name in lowercase
- **WHEN** `dist/ru/index.html` is rendered in a browser
- **THEN** the header reads "kinetren", not "KINETREN"

#### Scenario: Favicon is the kinetren icon
- **WHEN** `dist/en/index.html` is built
- **THEN** its icon link points at `../assets/kinetren.svg` and that file is byte-identical to `assets/kinetren.svg`

### Requirement: One English screenshot set serves every language
The page SHALL show the current kinetren screenshots taken by the editor's own pipeline
(English UI, free footage), one set shared by all languages, stored in `assets/shots/`
with the file names the editor publishes in its `docs/images/`. Each image slot declared
in `content/structure.toml` SHALL name exactly one file there; the build MUST fail naming
the slot when its file is missing. Image width and height in the markup SHALL come from
the image file. The per-language Open Graph cards SHALL be built from the shared hero.
No image under `assets/shots/` SHALL be unreferenced by both the structure and the
imported guide pages.

#### Scenario: Every language page shows the same files
- **WHEN** the site is built
- **THEN** every `<img>` in `dist/<lang>/index.html` for all five languages points into `../assets/shots/` with the same file names, and `dist/assets/shots/` has no per-language subdirectories

#### Scenario: A missing screenshot fails the build
- **WHEN** a file named by a `[shot.*]` entry is removed from `assets/shots/` and `build.py` runs
- **THEN** it exits non-zero naming that slot and file

#### Scenario: An image used only by the guide is kept
- **WHEN** `docs/guide/timeline.md` shows `../images/transitions.webp` and no `[shot.*]` slot names it
- **THEN** after `upstream.py import` the file is in `assets/shots/` and the build accepts it

### Requirement: Screenshots are imported from a kinetren checkout, never edited here
`upstream.py import` SHALL copy the images declared in `content/structure.toml` and the
images shown by the guide from `docs/images/`, the icon from `src/packaging/kinetren.svg`,
and the footage credits from `docs/images/CREDITS.md` of a committed revision of a kinetren
checkout into this repository, and remove images from `assets/shots/` that nothing
declares. It MUST fail, changing nothing, if any declared file is missing at that revision.
The build MUST fail when an imported file differs from the SHA-256 recorded for it in
`upstream.lock`.

#### Scenario: Import from the monorepo
- **WHEN** `python3 upstream.py import --from /media/e/developer/kt.9/kinotrain.9` runs
- **THEN** `assets/shots/` holds exactly the declared images, byte-identical to their sources at the checkout's `HEAD` commit, and `assets/kinetren.svg` matches the checkout's icon

#### Scenario: A missing source image changes nothing
- **WHEN** the revision lacks one declared image
- **THEN** the script exits non-zero naming it and `assets/` is unchanged

#### Scenario: A hand-edited screenshot fails the build
- **WHEN** a file in `assets/shots/` is re-encoded after the import and `build.py` runs
- **THEN** it exits non-zero naming the file and saying it differs from `upstream.lock`

### Requirement: The page credits the footage in its screenshots
Because the screenshots show excerpts of CC BY works, every language page SHALL carry, in
the footer, a translated line saying the screenshots show free films, linking to the list
of works with their authors and licenses. That list SHALL be published with the site
(`dist/credits.html` or equivalent) and generated from the imported credits file, not
written by hand.

#### Scenario: Credits are reachable from every page
- **WHEN** any `dist/<lang>/index.html` is opened
- **THEN** its footer has a link that resolves to a page listing every work, author and license from the imported credits

### Requirement: Downloads for Linux and Windows lead to the releases
The page SHALL present kinetren as an editor for Linux and Windows (tagline, hero, footer,
JSON-LD `operatingSystem`). The download button of the "Download" section SHALL link to
`https://github.com/kinetren/kinetren/releases`; the hero's download button SHALL scroll to
that section (`#get`). The section SHALL list the requirements for Linux (x86_64, glibc
2.35+) and for Windows (10 or 11, x86_64, portable zip, FFmpeg found on the system or
downloaded on the first start), graphics and sound. The page MUST NOT show a hard-coded
product version label outside the version log.

#### Scenario: Download link target
- **WHEN** `dist/en/index.html` is built
- **THEN** the button inside `<section id="get">` has `href="https://github.com/kinetren/kinetren/releases"`, the hero button has `href="#get"`, the requirements list has a Windows row, and the text `kt26.08` does not occur in `dist/`

### Requirement: Copy states facts, never slogans
Every sentence of the catalogs SHALL state a fact about the editor (what it does, what it
needs, how it is used), taken from the editor's README, guide or code. Catalogs MUST NOT
contain slogans, "X, not Y" antitheses, rhetorical closing lines or self-evident remarks
(the owner's rule: such phrases make the site read as machine-written). Numbers on the page
SHALL match the editor: 26 video effects, 18 audio effects, 33 transitions, 4 track types,
5 interface languages. The effects section SHALL list the 26 video effects by name; a
"Transitions, titles, generators" section SHALL describe those three features.

#### Scenario: Former filler phrases are gone
- **WHEN** `content/en.toml` and `content/ru.toml` are searched for "file you ship", "Direction, not dates", "Undo means undo", "Sound looks like sound"
- **THEN** there are no matches

### Requirement: Every language is a real translation
Each language offered in the switcher SHALL have its own translated catalog that passes
`translated_min`, so every language page is indexed. Spanish, Simplified Chinese and Arabic
SHALL use the editor's own terms for the same things (transition names, region, reel,
playhead, presets); effect names stay untranslated.

#### Scenario: All five languages are indexed
- **WHEN** the site is built
- **THEN** no language page carries `noindex`, and `sitemap.xml` lists `/en/`, `/es/`, `/zh-Hans/`, `/ar/` and `/ru/`

### Requirement: Every number explains itself
The hero SHALL show five numbers — video effects, audio effects, transitions, track types,
interface languages — and each SHALL open, on mouse hover and on keyboard or touch focus,
the full list of what it counts, without JavaScript. The count SHALL equal the length of
its list. The track types are video, audio, morph and camera. On narrow screens the numbers
SHALL wrap into two columns with no empty cell.

#### Scenario: Hovering "4" lists the track types
- **WHEN** the number 4 on `/ru/` is hovered or focused
- **THEN** a box appears below it reading "Видео · Аудио · Морф · Камера"

#### Scenario: Counts match the lists
- **WHEN** each `stats.<id>_list` value in `content/en.toml` is split on " · "
- **THEN** the item counts are 26, 18, 33, 4 and 5, equal to the numbers in `structure.toml`

### Requirement: The roadmap is a version log and a plan
The roadmap section SHALL show, in the left column, the versions newest first, each labelled
once by its date in the section-timecode style (`26:10:24` for version v26.10.24, with
`v26.10.24` only as the hover title) and followed by a one- or two-sentence summary; and in
the right column the planned features in the order of the coming rounds. From the first
editor tag on, the versions SHALL be the editor's `v*` tags, one entry per tag date: patch
tags of the same day (`v26.10.25.1`) belong to that day's entry. Entries older than the
first tag stay build dates from the editor's history. A summary SHALL state what changed
for a user, taken from the commits between that tag and the previous one; it MUST NOT name
internal test numbers, CI runs or round numbers. Planned items SHALL come from the
editor's claims index and leave the plan once shipped; the owner's private claims files
MUST NOT be copied, quoted or published.

#### Scenario: One label per version
- **WHEN** `dist/en/index.html` is built
- **THEN** each version entry contains `26:10:24`-style text once and no visible `v26.10.24` text, and the version list precedes the plan in the markup

#### Scenario: Two tags on one day make one entry
- **WHEN** the editor has tags `v26.10.25` and `v26.10.25.1`
- **THEN** the roadmap has exactly one `26:10:25` entry, and `upstream.py facts` reports no missing version

### Requirement: The download section shows the current time
The timecode of the "Download" section SHALL show the visitor's current local time as
`HH:MM:SS`, updated once a second; the other sections keep their fixed timecodes. The update
SHALL touch only that text.

#### Scenario: The clock ticks
- **WHEN** `/ru/` is open for two seconds
- **THEN** the `[data-clock]` text has changed and equals the local time within a second

### Requirement: Source and community links
The header of every language page and guide page SHALL link to the source repository
`https://github.com/kinetren/kinetren`, the Discord server `https://discord.gg/gXdzZQYY4e`
and the YouTube channel `https://www.youtube.com/@kinetren` as a separate group after the
page menu: monochrome inline SVG icons in the text colour, with the full names as their
tooltip and accessible name, visible on narrow screens too (owner, 2026-10-26). The footer of every
language page SHALL link the same three by their full names.

#### Scenario: Links present
- **WHEN** `dist/es/index.html` is built
- **THEN** all three URLs occur in the header's `mast-social` group and in the footer

#### Scenario: Short labels set apart from the menu
- **WHEN** `/ru/` is open at 1440 px and at 375 px
- **THEN** the header shows the GitHub, Discord and YouTube icons after the page menu, separated from it, and hovering the YouTube icon shows "YouTube"

### Requirement: The page is laid out like a printed page
The content column SHALL hug the start edge of the window (left; right on the Arabic page)
with the free space on the other side; the menu SHALL sit a step after the name, not at the
far edge. On wide screens a film-strip rail SHALL run along the start edge for the whole
height of the document and scroll with it, on the language pages and on `credits.html`.
On narrow screens the layout SHALL stay single-column without horizontal scrolling.

#### Scenario: The rail covers the document
- **WHEN** `/ru/` is open at 1440 px width
- **THEN** the rail's height equals the document's scroll height and it is positioned with the document, not the viewport

#### Scenario: No horizontal scroll on a phone
- **WHEN** `/ru/` is open at 375 px width
- **THEN** the document's scroll width equals the viewport width

### Requirement: Shortcuts live in the guide, not on the landing page
The language pages SHALL NOT carry a keyboard reference: no section of shortcut tables, no
key-chord data in `content/structure.toml` and no `[keys]` table in the catalogs. Keyboard
and mouse shortcuts SHALL be documented only in the imported guide (`/docs/shortcuts/`),
which the header's "Docs" link reaches. The sections keep consecutive timecodes and
alternating slabs without the removed section.

#### Scenario: No keyboard section on any language page
- **WHEN** the site is built
- **THEN** no `dist/<lang>/index.html` contains `id="keys"` or an element with class `keys`, and no catalog has a `[keys]` table

#### Scenario: Shortcuts reachable through the guide
- **WHEN** `dist/en/index.html` is built
- **THEN** its header links `../docs/`, and `dist/docs/shortcuts/index.html` exists
