# Proposal

## Why

The editor has gained three video effects that each simulate a real process: Datamosh runs a
codec, Camera ISP simulates a sensor and its processor, and VHS Tape records onto a modelled
tape. It has also gained masks on the preview. On the page these are only three names in a
29-name list and one sentence. None of them has a screenshot, because the editor's
screenshot pipeline (`src/scripts/live/readme_shots.py`, `docs/images/`) has no shot of
them, and the site may only show what that pipeline publishes.

A visitor who saw the site before has no way to tell that it changed. The page looks the
same on every visit. The new things are below the fold, and the roadmap lists only editor
tags. The last sync added masks and three effects without a new tag.

## What Changes

- **Screenshots of the new effects and masks.** The site declares four new image slots:
  `fx-datamosh`, `fx-camera-isp`, `fx-vhs-tape` and `masks`. They are files the editor's
  pipeline publishes in its `docs/images/`. A prompt for the editor's agent describes what
  each shot shows. It is written to this change's `editor-prompt.md`, and the owner takes it
  to the editor repository; the site does not take screenshots itself. The effects section
  shows the four shots in a row, with a translated caption and alt text that state what is
  in the picture.
- **The update strip.** A one-line strip above the hero lists what changed on the page
  since the visitor's last visit: the date of each site update in the timecode style and a
  list of named features. There is no heading word and no adjective, only dates and
  features. The strip links to the editor's What's new page (`/docs/whats-new/`) and can be
  closed. The visitor's browser stores which update was last seen (`localStorage`, key
  `kt-seen`). A visitor whose last seen update is the newest one sees nothing. A visitor
  with no stored value sees only the newest entry. That covers a first visit, and also every
  visitor from before this change, since the site has never stored a visit until now.
  Without JavaScript the strip stays hidden.
- **Update entries.** Each site sync that changes what a user can read about the editor
  adds one entry, under its date, to `[updates]` in `structure.toml` and to `updates.u<date>`
  in all five catalogs. The first entries describe the two syncs already made (26.11.01 and
  26.11.02).
- **Future "обнови".** The site-update procedure gains two steps:
  - write the update entry;
  - when a feature the page now describes has no screenshot in the editor, write a shot
    request for the editor's agent (`editor-requests/<date>-shots.md`) and give the owner
    its absolute path in the report.
- **The numbers in `site-content` follow the editor.** The requirements still say "26 video
  effects". They now refer to the counts that `upstream.py facts` checks, instead of fixed
  numbers that go stale with every new effect.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `site-content`:
  - effect and mask screenshots in the effects section;
  - the update strip and the rules for its entries;
  - the counts no longer fixed in the text.
- `site-build`: the page's script may read and write one `localStorage` key for the update
  strip, and the strip adds no animation and no request to another host.
- `upstream-sync`: the site-update procedure writes an update entry and a shot request for
  the editor.

## Impact

- `content/structure.toml`:
  - four `[shot.*]` slots;
  - the effects section's `gallery`;
  - `[updates]`.
- `content/<lang>.toml` × 5:
  - `effects.g_*_alt` and `effects.g_*_cap`;
  - `[updates]` entries;
  - the strip's link and close labels.
- `build.py`: the effects component renders the gallery row, a new strip component sits
  above the hero, and `page_js` gains the strip logic.
- `assets/kt.css`: the strip and the gallery row.
- `.claude/skills/site-update/SKILL.md`, `CLAUDE.md`: the two new steps.
- New folder `editor-requests/` for shot requests to the editor's agent.
- Depends on the editor. The slots cannot land until the editor's `docs/images/` has the
  four files, because `upstream.py import` fails on a missing declared image. The strip
  does not depend on the editor and can land first.
