# site-docs

## Purpose

Publishing the editor's user guide (`docs/guide/` in kinetren) as English pages of the
site, generated from a byte-identical import so the site and the editor never hold two
different texts.

## Requirements

### Requirement: The guide is published under /docs/
The build SHALL render every page in `assets/guide/` to `dist/docs/<stem>/index.html` and
an index `dist/docs/index.html` that lists the pages in the order of `[docs] pages` in
`content/structure.toml`, each with its first heading and first paragraph. The pages SHALL
be in English (`<html lang="en">`), with their own `canonical`, `title` (the page's first
heading) and `description` (its first paragraph, without markup), listed in `sitemap.xml`
and without `hreflang`. The build MUST fail when a file in `assets/guide/` is not listed
in `[docs] pages` or a listed page has no file.

#### Scenario: Every guide page is built
- **WHEN** the site is built with the seven guide pages imported
- **THEN** `dist/docs/index.html` and `dist/docs/<stem>/index.html` exist for each of them, and `sitemap.xml` lists all eight URLs

#### Scenario: A new upstream page must be placed
- **WHEN** an import adds `assets/guide/titles.md` that `[docs] pages` does not list
- **THEN** `build.py` exits non-zero naming `titles.md`

### Requirement: Every language page links to the guide
The header menu of every language page SHALL have a "Docs" item (catalog key
`site.nav_docs`, translated) linking to `../docs/`. A guide page's header SHALL link the
product name to the root dispatcher, so a visitor returns to their own language.

#### Scenario: Docs link from the Russian page
- **WHEN** `dist/ru/index.html` is built
- **THEN** its header has a link with `href="../docs/"` whose text is the `site.nav_docs` value from `ru.toml`

### Requirement: Guide text is rendered, never rewritten
The rendered page SHALL contain the guide's text as written: headings, paragraphs,
emphasis, inline code, ordered and unordered lists (including lists nested in list items),
tables (with `\|` inside cells), fenced code blocks, links and images. The build MUST fail,
naming the file and line, on a construct it does not render (raw HTML, block quotes,
setext headings, reference-style links, footnotes) instead of passing it through or
dropping it. Headings SHALL get the same anchor ids GitHub gives them.

#### Scenario: An unsupported construct fails loudly
- **WHEN** an imported guide page contains a line starting with `>`
- **THEN** `build.py` exits non-zero naming that file and line

#### Scenario: Anchors match GitHub
- **WHEN** `export.md` has the heading `## kt-cli`
- **THEN** the rendered heading has `id="kt-cli"`

### Requirement: Guide links and images resolve on the site
A link from one guide page to another (`morpher.md`, `export.md#kt-cli`) SHALL point at the
site page (`../morpher/`, `../export/#kt-cli`), and the build MUST fail when the target page
or anchor does not exist. Any other relative link SHALL point at
`https://github.com/kinetren/kinetren/blob/<locked commit>/<resolved path>`. An image
`../images/<file>` SHALL be served from `assets/shots/<file>` with the file's width and
height and the Markdown alt text.

#### Scenario: README link goes to GitHub at the locked commit
- **WHEN** `getting-started.md` links `../../README.md#install` and the lock names commit `C`
- **THEN** the rendered link is `https://github.com/kinetren/kinetren/blob/C/README.md#install`

#### Scenario: A broken anchor fails the build
- **WHEN** a guide page links `export.md#no-such-heading`
- **THEN** `build.py` exits non-zero naming the source file and the anchor
