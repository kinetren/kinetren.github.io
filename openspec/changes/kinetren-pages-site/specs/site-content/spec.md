# Spec Delta

## Purpose

What the landing page shows about the product: its name and icon, the screenshots and
where they come from, the attribution those screenshots require, and where the download
button leads.

## ADDED Requirements

### Requirement: The page names the product Kinetren
Every generated page, in every language, SHALL name the product **Kinetren**: header,
footer, `<title>`, Open Graph title, JSON-LD `name`, the root dispatcher, and all catalog
prose. The former name `Kinotrain` MUST NOT appear anywhere in `dist/`, `content/`,
`assets/kt.css` or `build.py`. The favicon and inline logo SHALL be the Kinetren icon
(`assets/kinetren.svg`, the same file as the editor's `src/packaging/kinetren.svg`),
published as `dist/assets/kinetren.svg`. Facts the rename changed SHALL be correct: the
installer registers the `.kt` project type.

#### Scenario: No former name in the output
- **WHEN** the site is built and `dist/`, `content/`, `assets/kt.css` and `build.py` are searched case-insensitively for `kinotrain`
- **THEN** there are no matches

#### Scenario: Favicon is the Kinetren icon
- **WHEN** `dist/en/index.html` is built
- **THEN** its icon link points at `../assets/kinetren.svg` and that file is byte-identical to `assets/kinetren.svg`

### Requirement: One English screenshot set serves every language
The page SHALL show the current Kinetren screenshots taken by the editor's own pipeline
(English UI, free footage), one set shared by all languages, stored in `assets/shots/`
with the file names the editor publishes in its `docs/images/`. Each image slot declared
in `content/structure.toml` SHALL name exactly one file there; the build MUST fail naming
the slot when its file is missing. Image width and height in the markup SHALL come from
the image file. The per-language Open Graph cards SHALL be built from the shared hero.
No image under `assets/shots/` SHALL be unreferenced by the structure.

#### Scenario: Every language page shows the same files
- **WHEN** the site is built
- **THEN** every `<img>` in `dist/<lang>/index.html` for all five languages points into `../assets/shots/` with the same file names, and `dist/assets/shots/` has no per-language subdirectories

#### Scenario: A missing screenshot fails the build
- **WHEN** a file named by a `[shot.*]` entry is removed from `assets/shots/` and `build.py` runs
- **THEN** it exits non-zero naming that slot and file

### Requirement: Screenshots are imported from a Kinetren checkout, never edited here
`import-shots.py --from <kinetren checkout>` SHALL copy the images declared in
`content/structure.toml` from `<checkout>/docs/images/`, the icon from
`<checkout>/src/packaging/kinetren.svg`, and the footage credits from
`<checkout>/docs/images/CREDITS.md` into this repository, and remove images from
`assets/shots/` that no slot declares. It MUST fail, changing nothing, if any declared
file is missing in the checkout. Without `--from` it SHALL exit with a usage message.

#### Scenario: Import from the monorepo
- **WHEN** `python3 import-shots.py --from /media/e/developer/kt.9/kinotrain.9` runs
- **THEN** `assets/shots/` holds exactly the declared images, byte-identical to their sources, and `assets/kinetren.svg` matches the checkout's icon

#### Scenario: A missing source image changes nothing
- **WHEN** the checkout lacks one declared image
- **THEN** the script exits non-zero naming it and `assets/` is unchanged

### Requirement: The page credits the footage in its screenshots
Because the screenshots show excerpts of CC BY works, every language page SHALL carry, in
the footer, a translated line saying the screenshots show free films, linking to the list
of works with their authors and licenses. That list SHALL be published with the site
(`dist/credits.html` or equivalent) and generated from the imported credits file, not
written by hand.

#### Scenario: Credits are reachable from every page
- **WHEN** any `dist/<lang>/index.html` is opened
- **THEN** its footer has a link that resolves to a page listing every work, author and license from the imported credits

### Requirement: The download button leads to the releases
The download button of the "Get it" section SHALL link to
`https://github.com/kinetren/kinetren/releases`; the hero's download button SHALL scroll
to that section (`#get`). The page MUST NOT show a hard-coded product version label.

#### Scenario: Download link target
- **WHEN** `dist/en/index.html` is built
- **THEN** the button inside `<section id="get">` has `href="https://github.com/kinetren/kinetren/releases"`, the hero button has `href="#get"`, and the text `kt26.08` does not occur in `dist/`
