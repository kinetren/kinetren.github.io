# Spec Delta

## MODIFIED Requirements

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
