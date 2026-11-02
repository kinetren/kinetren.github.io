# Design

## Context

- **Where shots come from.** Screenshots reach the site only through
  `python3 upstream.py import`. It copies the images that `[shot.*]` slots declare, plus the
  images the guide shows, from the editor's `docs/images/` at the locked commit. A declared
  image that is missing upstream fails the import. On the editor side, every image is made
  by `src/scripts/live/readme_shots.py`:
  - real footage (`readme-shots.py --sources`), an English UI and a 1920×1080 window on its
    own Xvfb screen;
  - views reached through probe rectangles and real gestures;
  - images listed in the literal `SHOTS`;
  - WebP at quality 92;
  - `readme-check.py`, which requires the editor's docs to reference exactly that set.

  So a new shot is editor work, done by the editor's agent, and then a site slot.
- **The effects section.** It is drawn by `c_effects` in `build.py`: the name tiles, the
  video FX shot (`fx_video`), the audio list, and the Slowed+Reverb shot (`fx_audio`).
- **Client storage.** The page's script already uses `localStorage["lang"]` and
  `sessionStorage["kt-release"]`, and nothing else. The idle rule (`site-build`) forbids
  timers and animations outside the hero headline.
- **What a sync can change.** The site changes with every sync, but the roadmap shows only
  editor tags. The 26.11.02 sync (masks, Datamosh, Camera ISP, VHS Tape, sound generators)
  had no tag.

## Goals / Non-Goals

**Goals**
- Pictures of the three simulation effects and of masks, made by the editor's pipeline and
  imported like every other shot.
- A returning visitor learns, in one line above the hero, what was added since their last
  visit, in named features.
- Every future "обнови" produces both pieces: an update entry, and a shot request when a
  headline feature has no picture.

**Non-Goals**
- Changing the hero headlines (the owner's).
- Changing the roadmap: tags stay its unit.
- Pictures for the guide. The editor decides whether its README or guide shows the new
  images. Its `readme-check.py` requires a reference, which is the editor agent's concern.
- Any tracking. The visit is remembered only in the visitor's own browser.

## Decisions

### D1. Four slots with editor-chosen names, a gallery row in the effects section

The slots are named after the editor's files:

| slot | file |
|---|---|
| `fx_datamosh` | `fx-datamosh.webp` |
| `fx_camera_isp` | `fx-camera-isp.webp` |
| `fx_vhs_tape` | `fx-vhs-tape.webp` |
| `masks` | `masks.webp` |

The effects section gets `gallery = ["fx_datamosh", "fx_camera_isp", "fx_vhs_tape", "masks"]`
in `structure.toml`. `c_effects` renders it after the name tiles and the `fx_cap` line, as a
row of `shot()` figures. Each figure takes `effects.g_<slot>_alt` and `effects.g_<slot>_cap`.

The row is a CSS grid: two columns from 900 px up, one column below. Images keep their
ratio (`height:auto`, size from the file as today).

- *Why in the effects section:* the shots illustrate the effects named there, and the
  sentence about masks is the effects standfirst.
- *Why not a separate section:* the skill forbids inventing sections. A gallery is one more
  part of an existing one.

The names are proposed to the editor in the prompt. If the editor's agent picks different
names, only the `file` of each slot changes.

### D2. What each shot shows

Written in full in `editor-prompt.md`:

- **Datamosh:** the same frame without and with Datamosh ("Cut mosh" preset across a cut).
- **Camera ISP:** without and with the "Phone at night" look.
- **VHS Tape:** the effects window with the drawn deck face, plus the resulting frame.
- **Masks:** the preview with a pen mask drawn over the picture, and an effect limited to
  that mask.

Two-half images carry no baked-in text, unlike `morpher-before-after.webp`, which has
English labels. The site is in five languages, so the caption says which half is which.

### D3. The update strip: data

```toml
# structure.toml
[updates]
# Site syncs that changed what the page says about the editor, newest first.
# "26.11.02" reads the key updates.u261102 and is shown as 26:11:02.
entries = ["26.11.02", "26.11.01"]
```

Catalogs hold `[updates]` with:
- `u261102`, `u261101`: the entries;
- `more`: "and {0} earlier";
- `link`: reuses the wording of `dl.whats_new`, "What's new";
- `close`: the accessible name of the close button.

The key set is the usual one: English is the reference, and a missing key fails the build.
Entry text follows `site-content` "Update entries name what changed". Validation: the build
fails when an entry is longer than 160 characters in English, or contains `!` or one of the
banned words. The list of banned words lives in `build.py` next to the existing copy checks.

Seed entries:
- `26.11.01`: the v26.10.31 sync. Welcome window with templates, recent projects and a
  tour; Help → Guide; FFmpeg 9; a render window that names the encoder and keeps a log.
- `26.11.02`: masks on the preview; Datamosh, Camera ISP and VHS Tape; sound generators; a
  window after a crash.

### D4. The update strip: markup and behaviour

The strip is one `<aside class="upd" hidden data-newest="261102">`, placed before the hero
section inside `<main>`. It holds:
- one `<p data-id="…">` per entry, each `hidden`, with the timecode span and the text;
- a `<p class="upd-more" hidden>` for the "and N earlier" line;
- the link to `../docs/whats-new/`;
- a close `<button>`.

All entries are in the HTML, so the page needs no fetch. The script, run once at load:

```
seen = read("kt-seen")                 // try/catch: null on any error
if seen == newest: stop                // strip stays hidden
show = seen ? entries newer than seen : [newest]
unhide the first three of show; if more, unhide .upd-more with the count
unhide the strip
on close or link click: write("kt-seen", newest); hide the strip
```

Entry ids are `YYMMDD` strings, so "newer" is a plain string comparison.

- *Why only the newest entry when nothing is stored:* the site has never stored a visit, so
  on the first deploy every former visitor looks like a newcomer. Showing them nothing would
  defeat the change. One line naming the latest features is still true for a newcomer,
  because the strip says nothing about "your last visit". The alternative was to show the
  strip only to visitors with a stored `kt-seen`. It is cleaner for newcomers, but the
  former audience would see the strip only from their second visit after the deploy, which
  is exactly the audience the owner asked about.
- *Why store on close or click, not on display:* a strip seen for a second while scrolling
  would otherwise be lost. Ignoring it costs one line on the next visit.
- *No heading:* the strip is a date followed by facts. The owner asked for no headlines of
  the "big update" kind, and a heading word would be one.

### D5. Placement and style

- The strip is a full-width band above the hero, in the page's paper style: muted
  background and a small mono timecode, like the roadmap's. It is one line on wide screens
  and wraps on narrow ones.
- It is in the normal flow, never fixed or sticky, so it covers nothing.
- The close button has a 44 px hit area.
- It uses no animation and no `filter` or `backdrop-filter`.
- RTL works through the existing `dir` on `<html>`.

### D6. Future syncs (skill and CLAUDE.md)

`.claude/skills/site-update/SKILL.md` gains, in step 3:
- **Update entry:** after the sections change, write the day's entry in all five catalogs
  and add its date to `[updates] entries`. A second sync on the same day extends that day's
  entry instead of adding another. A sync that changed only wording, or a fix with no user
  meaning, gets no entry.
- **Shot request:** for each feature added to the page this sync, check the editor's
  `docs/images/` and the `SHOTS` list in `src/scripts/live/readme_shots.py` (read-only). If
  the editor's What's new or guide lists the feature as a headline item and there is no
  image of it, write `editor-requests/<YYYY-MM-DD>-shots.md`.
  - The request follows the shape of `editor-prompt.md`: the pipeline facts, one block per
    image (name, what is on screen, how it is reached, crop, no baked text), and the
    editor's own checks.
  - Its absolute path goes into the report.
  - Once the images exist upstream, a later sync adds the slots and the gallery entries.

`CLAUDE.md`'s "обнови" paragraph names the two outputs.

`editor-requests/` is committed. A request is a record of what the site asked for; it is
not a cache.

## Risks / Trade-offs

- **The editor never makes the shots.** The gallery tasks then stay open. The strip and the
  skill steps land independently, because tasks group them apart.
- **A newcomer sees a line about the latest sync.** This is accepted (D4). The text is still
  true and useful for them.
- **Entries drift into marketing.** The build check catches the obvious words, and the copy
  rule plus the owner's review catch the rest.
- **Same-day syncs.** Merging the text into one entry keeps one line per day, as the roadmap
  does for patch tags.

## Open Questions

- None blocking. If the editor's agent chooses other file names or a different shot list,
  D1's table and the gallery list follow its choice.
