# Spec Delta

## MODIFIED Requirements

### Requirement: Guide text is rendered, never rewritten
The rendered page SHALL contain the guide's text as written: headings, paragraphs,
emphasis, inline code, ordered and unordered lists (including lists nested in list items),
tables (with `\|` inside cells), fenced code blocks, links, images and key caps written as
`<kbd>…</kbd>`. `<kbd>` SHALL be the only inline HTML: it is rendered as the same key cap
as on the landing page, its content is escaped, and an unpaired or nested `<kbd>` fails the
build. The build MUST fail, naming the file and line, on a construct it does not render
(any other raw HTML, block quotes, setext headings, reference-style links, footnotes)
instead of passing it through or dropping it. Headings SHALL get the same anchor ids
GitHub gives them.

#### Scenario: An unsupported construct fails loudly
- **WHEN** an imported guide page contains a line starting with `>`
- **THEN** `build.py` exits non-zero naming that file and line

#### Scenario: Anchors match GitHub
- **WHEN** `export.md` has the heading `## kt-cli`
- **THEN** the rendered heading has `id="kt-cli"`

#### Scenario: Key caps render
- **WHEN** a guide table cell reads `<kbd>Ctrl</kbd>+<kbd>S</kbd>`
- **THEN** the rendered cell contains `<kbd>Ctrl</kbd>+<kbd>S</kbd>`, styled as on the landing page

#### Scenario: Other HTML still fails
- **WHEN** a guide page contains `<span>x</span>` or an unclosed `<kbd>`
- **THEN** `build.py` exits non-zero naming that file and line
