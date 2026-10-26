# Proposal

## Why

The hero leaves the right side of the headline empty, and its "Download" button only scrolls
to the bottom section. That section's button opens the GitHub releases list, where the
visitor has to pick a file among four (`.tar.gz`, `.zip` and two `.sha256`) whose names
carry a version and a commit hash. The headline is a single fixed line. Hovering the
"video effects" number opens its 26-name list, which then slides under the heading of the
next section ("Rendering") and looks broken.

## What Changes

- A **download panel** sits to the right of the hero headline on wide screens and under the
  lede on narrow ones. The same panel replaces the "Download from GitHub" button of the
  "Download" section. The hero's own "Download" button (`#get`) is removed. "Features" stays.
- The panel's buttons download the build directly: the Windows `.zip` and the Linux
  `.tar.gz` of the latest GitHub release. The page asks the GitHub API for the latest
  release in the visitor's browser and shows its version and file size next to the button.
  Without JavaScript, or when GitHub does not answer, the buttons open the latest release page.
- The panel is **matched to the visitor's system**. A Windows visitor sees one "Download for
  Windows" button, and a Linux visitor sees one "Download for Linux" button. The other build
  remains as a small text link. A visitor on any other system (macOS, phones) sees both
  buttons and a line saying which systems kinetren runs on.
- The panel also links to **all releases** (the GitHub releases list, for older versions)
  and to **What's new** (the site's own version log, `#roadmap`, translated).
- The hero headline **rotates through several lines** with a short crossfade. The first line
  is the current headline ("A free video editor for Linux and Windows"). The others are
  slogans and calls to action picked by the owner ("Finally, proper editing on Linux",
  "Made for edits: Slowed+Reverb, VHS, Glow", "Edit. Export. Post.", "Download now, edit in
  a minute"). Internal facts retold as slogans are not allowed. Under `prefers-reduced-motion`, with the hero off screen or the tab hidden, the
  headline does not change. Screen readers and search engines get only the first line.
- The number popups (the stats strip) are drawn above the sections that follow the hero.
- Catalog keys change in all five languages: `[headline]` lines and `[dl]` panel labels are
  added (`hero.h1` moves to `headline.l1`), and `hero.cta_primary`, `hero.cta_note`,
  `get.cta` and `get.cta_note` are removed.
  `get.standfirst` drops its "builds are on the releases page" sentence.
  **BREAKING** for catalogs: other languages must follow the new English key set.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `site-content`: download requirement rewritten (direct, system-matched downloads in the
  hero and the Download section, release and what's-new links, runtime version label). The
  copy rule now allows the rotating hero headlines as slogans, as long as each promise holds. The stats
  popups must stay above the following sections. A new requirement covers the rotating
  headline.
- `site-build`: the "stays idle" requirement allows the headline rotation only while it is
  visible, and the page makes one request to `api.github.com`. Font subsets also cover the
  text the page script writes.

## Impact

- `build.py`: `c_hero` (two-column top, headline stack, panel), `c_install` (panel instead
  of the button), a shared download-panel helper, `PAGE_JS` (system detection, release
  lookup, headline rotation), a tiny head script that sets the system class before first
  paint, `collect_chars` (characters of the runtime label).
- `assets/kt.css`: hero grid, panel, headline stack and crossfade, `.hero` stacking above the
  next section.
- `content/structure.toml`: release URLs (`releases`, the latest-release page, the API
  endpoint) and the asset name suffixes (`[download]`).
- `content/{en,es,zh-Hans,ar,ru}.toml`: new and removed keys, rewritten `get.standfirst`.
- `.claude/skills/site-update/SKILL.md`: re-check the headline facts on every sync.
- `dist/` rebuilt. There is no change to the editor checkout and no new dependency.
