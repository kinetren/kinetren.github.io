# Spec Delta

## MODIFIED Requirements

### Requirement: Code speaks English
Comments, docstrings, build messages and `--help` texts in `build.py`, `upstream.py`,
`assets/kt.css`, `content/structure.toml` and the catalog headers SHALL be English, and so
SHALL `CLAUDE.md` and `.claude/skills/site-update/SKILL.md`, except where they quote the
owner's trigger words ("обнови"). Russian and other languages appear only as translation
values, language self-names and those quoted trigger words.

#### Scenario: No Cyrillic outside translations
- **WHEN** `build.py`, `upstream.py`, `assets/kt.css`, `content/structure.toml` and the comment lines of every catalog are searched for Cyrillic
- **THEN** the only matches are the `ru = "Русский"` self-name lines

### Requirement: The README describes the standalone repository
`README.md` SHALL be in English and describe this repository on its own: how to build,
check and serve the site, how to translate, how to sync with the editor (`upstream.py
status`, `import` and `facts`, `upstream.lock`, and that asking an agent to "update" runs
the whole procedure), how the guide becomes `/docs/`, what the build checks, and how
publishing works (including the one-time owner setup on GitHub). It MUST NOT give commands
that assume a `site/` subdirectory or a monorepo beside it, except the explicit
`--from <kinetren checkout>` argument, and MUST NOT mention `import-shots.py`.

#### Scenario: Commands in the README run from the repository root
- **WHEN** each shell command in `README.md` is run from a fresh clone's root (with a kinetren checkout passed where `--from` asks for one)
- **THEN** none fails because of a missing `site/` or `rust/` path, and none names `import-shots.py`
