# Spec Delta

## MODIFIED Requirements

### Requirement: Downloads for Linux and Windows lead to the releases
The page SHALL present kinetren as an editor for Linux and Windows (tagline, hero, footer,
JSON-LD `operatingSystem`). A download panel SHALL appear twice on every language page: in
the hero, beside the headline on wide screens (inline-end side; left on the Arabic page)
and below the lede on narrow screens, and in `<section id="get">` in place of a
releases-page button. The hero SHALL NOT keep a separate button that scrolls to `#get`.

Each panel SHALL hold:
- a Windows button and a Linux button. With JavaScript, each points at the latest
  non-prerelease GitHub release's file of that platform: the asset whose name ends in
  `-windows-x86_64.zip` or `-linux-x86_64.tar.gz`. A label beside the button gives the
  release's tag and the file's size, both read from that release. Without JavaScript, or
  when the release cannot be read or lacks the file, the button links to
  `https://github.com/kinetren/kinetren/releases/latest` and no version label is shown;
- a link "All releases" to `https://github.com/kinetren/kinetren/releases`;
- a link "What's new" to the page's own version log (`#roadmap`).

The panel SHALL match the visitor's system, detected in the browser before the panel is
first painted. On Windows only the Windows button is shown, and the Linux build is offered
as a small text link. On Linux (not Android) it is the other way round. On any other system,
or without JavaScript, both buttons are shown with a line naming the systems kinetren runs
on. The release SHALL be requested at most once per page view, from `api.github.com` only,
and an answer MAY be reused within the same browser session for up to one hour.

The "Download" section SHALL list the requirements for Linux (x86_64, glibc 2.35+) and for
Windows (10 or 11, x86_64, portable zip, FFmpeg found on the system or downloaded on the
first start), graphics and sound. The page source MUST NOT contain a hard-coded product
version label outside the version log. The release label exists only as text written by
the page script from the GitHub answer.

#### Scenario: Download link target
- **WHEN** `dist/en/index.html` is built
- **THEN** both the hero and `<section id="get">` contain a download panel whose Windows and Linux buttons have `href="https://github.com/kinetren/kinetren/releases/latest"`, a link to `https://github.com/kinetren/kinetren/releases` and a link to `#roadmap`; no element links `#get` from the hero; the requirements list has a Windows row; and the text `kt26.08` does not occur in `dist/`

#### Scenario: A Windows visitor gets the zip
- **WHEN** `/ru/` is opened in a browser reporting a Windows platform and the latest release has `kinetren-26.10.25-3196cc51-windows-x86_64.zip`
- **THEN** both panels show one primary button "Скачать для Windows" whose `href` is that asset's `browser_download_url`, a label with `v26.10.25` and the file size, a small "Linux" link to the `.tar.gz` asset, and no Linux primary button

#### Scenario: A Linux visitor gets the tarball
- **WHEN** `/en/` is opened on a Linux desktop browser
- **THEN** the primary button links the `-linux-x86_64.tar.gz` asset of the latest release, and the Windows build is a small text link

#### Scenario: A phone or a Mac sees both
- **WHEN** `/en/` is opened on macOS or Android
- **THEN** both buttons are shown with the line naming Linux and Windows

#### Scenario: GitHub does not answer
- **WHEN** the request to `api.github.com` fails, is rate-limited or returns a release without one of the two assets
- **THEN** the affected buttons keep `href="https://github.com/kinetren/kinetren/releases/latest"`, no version label is shown, and the console has no uncaught error

### Requirement: Copy states facts, never slogans
Every sentence of the catalogs SHALL state a fact about the editor (what it does, what it
needs, how it is used), taken from the editor's README, guide or code. Catalogs MUST NOT
contain slogans, "X, not Y" antitheses, rhetorical closing lines or self-evident remarks
(the owner's rule: such phrases make the site read as machine-written). The single
exception is the hero's rotating headlines (`[headline]`): they ARE slogans and calls to
action, chosen by the owner, about what a visitor gets (price, freedom, audience, how fast
they start). They MUST NOT be internal facts retold as slogans ("The preview is the
export", "Every parameter on a curve"), which read as truisms. Every promise they make
SHALL be true of kinetren. Numbers on the page SHALL match the
editor: 26 video effects, 18 audio effects, 33 transitions, 4 track types, 5 interface
languages. The effects section SHALL list the 26 video effects by name; a "Transitions,
titles, generators" section SHALL describe those three features.

#### Scenario: Former filler phrases are gone
- **WHEN** `content/en.toml` and `content/ru.toml` are searched for "file you ship", "Direction, not dates", "Undo means undo", "Sound looks like sound"
- **THEN** there are no matches

#### Scenario: Headlines are slogans, not retold internals
- **WHEN** the `headline.*` values of `content/en.toml` are read
- **THEN** none of them is "The preview is the export", "Every parameter on a curve", "Edit a reel once, every copy follows" or "Swap the source, keep the cut", and every promise in them (free, Linux and Windows, Slowed+Reverb, VHS and Glow included, ready within a minute of the download) holds for the current release

### Requirement: Every number explains itself
The hero SHALL show five numbers: video effects, audio effects, transitions, track types and
interface languages. Each SHALL open, on mouse hover and on keyboard or touch focus, the
full list of what it counts, without JavaScript. The list box SHALL be drawn above
everything that follows the hero: no heading, slab or card of the next section may cover
any part of it. The count SHALL equal the length of its list. The track types are video,
audio, morph and camera. On narrow screens the numbers SHALL wrap into two columns with no
empty cell.

#### Scenario: Hovering "4" lists the track types
- **WHEN** the number 4 on `/ru/` is hovered or focused
- **THEN** a box appears below it reading "Видео · Аудио · Морф · Камера"

#### Scenario: The longest list is not covered by the next section
- **WHEN** the number 26 on `/en/` is hovered at 1440 px and at 375 px width
- **THEN** the whole list box is visible and `document.elementFromPoint` at any point inside it returns the box or its text, not the "Rendering" heading or its section

#### Scenario: Counts match the lists
- **WHEN** each `stats.<id>_list` value in `content/en.toml` is split on " · "
- **THEN** the item counts are 26, 18, 33, 4 and 5, equal to the numbers in `structure.toml`

## ADDED Requirements

### Requirement: The hero headline rotates through slogans
The hero `<h1>` SHALL hold, in every language, the first line of `[headline]`: the product
line naming kinetren's platforms ("A free video editor for Linux and Windows"). It is the
only headline text in the accessible name and in what crawlers index. The other
`[headline]` lines (at least three more, the same count in every catalog) SHALL be shown in
the same place, one at a time, in a loop that changes line every 4–6 seconds with a
crossfade of at most 0.6 s and does not move the content below it: the headline box keeps
the height of its tallest line. The extra lines SHALL be hidden from assistive technology.
The rotation SHALL NOT run, and the first line SHALL stay, when the visitor prefers reduced
motion or JavaScript is off. It SHALL pause while the hero is out of the viewport or the
tab is hidden.

#### Scenario: Lines change on an open page
- **WHEN** `/es/` is open at the top for 12 seconds with motion allowed
- **THEN** at least two different `[headline]` lines of `content/es.toml` have been visible in the hero, and the `.lede` paragraph has not moved

#### Scenario: Reduced motion keeps the first line
- **WHEN** `/en/` is opened with `prefers-reduced-motion: reduce`
- **THEN** only "A free video editor for Linux and Windows" is visible and it does not change

#### Scenario: The h1 is the product line
- **WHEN** `dist/ru/index.html` is built
- **THEN** its `<h1>` text equals `headline.l1` of `content/ru.toml` without markup, and the other lines are in elements with `aria-hidden="true"`
