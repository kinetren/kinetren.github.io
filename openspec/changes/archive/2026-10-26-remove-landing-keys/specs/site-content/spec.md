# Spec Delta

## ADDED Requirements

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
