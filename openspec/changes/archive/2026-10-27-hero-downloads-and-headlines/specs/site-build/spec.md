# Spec Delta

## MODIFIED Requirements

### Requirement: Font subsets are built from the characters actually used
The build SHALL subset Latin/Cyrillic, monospace, CJK and Arabic fonts to exactly the
characters used across all catalogs and structure, plus the characters the page script
can write at runtime (the release label: `v`, digits, `.`, `·`, `KMGB`, space). It SHALL
keep the Arabic joining features (`init/medi/fina/isol` and related), write the subsets to
`assets/fonts/` with a `FONT-MANIFEST.txt`, and reference them from the generated CSS.

#### Scenario: Arabic text keeps its joined forms
- **WHEN** `dist/ar/index.html` is viewed in a browser
- **THEN** Arabic words render as joined script, not isolated letter forms

#### Scenario: The release label renders in the site font
- **WHEN** `/zh-Hans/` shows the label `v26.10.25 · 48 MB` next to a download button
- **THEN** every character of it is drawn from a `KT` font subset, not a system fallback

### Requirement: The site is viewed through a local server and stays idle
`build.py --serve [PORT]` SHALL build and then serve `dist/` over HTTP on `127.0.0.1`
(port 8000 by default) until interrupted. The page MUST NOT run infinite animations over
`filter`, `mix-blend-mode` or `backdrop-filter`. An idle open page SHALL NOT keep the
compositor busy, with one exception: the hero headline crossfade, which animates only
`opacity` and `transform` and runs only while the hero is in the viewport and the tab is
visible. The only network request the page makes to another host SHALL be the one
latest-release request to `api.github.com`. Fonts, styles and images stay on the site.

#### Scenario: Serve mode shows images and fonts
- **WHEN** `python3 build.py --serve` runs and `http://127.0.0.1:8000/en/` is opened
- **THEN** the page loads with its screenshots, styles and fonts and no failed asset requests

#### Scenario: Scrolled past the hero, the page is idle
- **WHEN** `/en/` is scrolled to `#roadmap` and left open for 10 seconds
- **THEN** no headline line changes during that time and no animation is running

#### Scenario: One request leaves the site
- **WHEN** `/ru/` is loaded and its network log is read
- **THEN** every request other than one `GET https://api.github.com/repos/kinetren/kinetren/releases/latest` goes to the page's own origin
