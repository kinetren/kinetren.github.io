## MODIFIED Requirements

### Requirement: One request updates the whole site
When the owner asks an agent in this repository to update the site ("обнови", "update the
site", "sync with the editor"), the agent SHALL follow the procedure in
`.claude/skills/site-update/SKILL.md`, to which `CLAUDE.md` points:
- run `status`;
- for every reported section, read the editor diff of its `upstream` paths and bring that
  section's facts in `content/en.toml` and `content/structure.toml` up to date;
- change the same keys in every other catalog, with a translation that uses the editor's
  own terms;
- add a roadmap entry for every new tag date and take shipped items off the plan;
- when the sync changes what the page says about the editor, add one update entry under
  the sync's date (`structure.toml [updates]` and `updates.u<YYMMDD>` in all five catalogs).
  It follows the rules of `site-content`: named features and facts, no heading word, no
  praise. A second sync on the same day extends that day's entry instead of adding another;
- when a feature the page now describes has no screenshot among the editor's
  `docs/images/`, and is one the editor's own What's new or guide presents as a headline
  item, write a shot request for the editor's agent to `editor-requests/<YYYY-MM-DD>-shots.md`.
  The request names each wanted image (`docs/images/<name>.webp`), what it shows and the
  conventions of the editor's screenshot pipeline;
- run `import`, `build.py`, `build.py --check` and `facts` until all pass;
- commit;
- report what changed per section, the update entry, the absolute path of any shot request,
  and what it could not decide.

The agent MUST NOT push without the owner's go-ahead, MUST NOT change a section the diff
does not concern, MUST NOT take screenshots or produce images itself, and MUST follow the
copy rules of `site-content` (facts, never slogans). Commit messages SHALL be English and
carry no AI or agent attribution lines.

#### Scenario: Update after an editor round
- **WHEN** the owner says "обнови" after the editor gained a tag, changed `docs/guide/shortcuts.md` and changed `openspec/specs/export/spec.md`
- **THEN** the agent's commit adds the tag's version entry in all five catalogs, updates the export section from the changed spec, imports the guide so `/docs/shortcuts/` follows, adds the day's update entry in all five catalogs, passes `build.py --check` and `facts`, and the report lists the `roadmap`, `export`, update-entry and docs changes

#### Scenario: A new effect without a screenshot
- **WHEN** the editor's What's new announces a new video effect, `facts` reports it missing on the site, and `docs/images/` has no image of it
- **THEN** the agent adds the effect to the page and to the day's update entry, writes `editor-requests/<date>-shots.md` describing the wanted image, and the report gives that file's absolute path; no image is added to `assets/shots/` by hand

#### Scenario: Nothing to do
- **WHEN** the owner says "обнови" and `status` reports the site up to date
- **THEN** the agent says so and makes no commit and no update entry
