# Spec Delta

## MODIFIED Requirements

### Requirement: One request updates the whole site
When the owner asks an agent in this repository to update the site ("обнови", "update the
site", "sync with the editor"), the agent SHALL follow the procedure in
`.claude/skills/site-update/SKILL.md`, to which `CLAUDE.md` points: run `status`; for every
reported section read the editor diff of its `upstream` paths and bring that section's
facts in `content/en.toml` and `content/structure.toml` up to date, and change the same keys
in every other catalog with a translation that uses the editor's own terms; add a roadmap
entry for every new tag date and take shipped items off the plan; run `import`, `build.py`,
`build.py --check` and `facts` until all pass; commit; and report what changed per section
and what it could not decide. The agent MUST NOT push without the owner's go-ahead, MUST
NOT change a section the diff does not concern, and MUST follow the copy rules of
`site-content` (facts, never slogans). Commit messages SHALL be English and carry no AI or
agent attribution lines.

#### Scenario: Update after an editor round
- **WHEN** the owner says "обнови" after the editor gained a tag, changed `docs/guide/shortcuts.md` and changed `openspec/specs/export/spec.md`
- **THEN** the agent's commit adds the tag's version entry in all five catalogs, updates the export section from the changed spec, imports the guide so `/docs/shortcuts/` follows, passes `build.py --check` and `facts`, and the report lists the `roadmap`, `export` and docs changes

#### Scenario: Nothing to do
- **WHEN** the owner says "обнови" and `status` reports the site up to date
- **THEN** the agent says so and makes no commit
