# Request from the kinetren site: four screenshots

The site (github.com/kinetren/kinetren.github.io, checked out next to this repository as
`../kt.9.site`) shows only images this repository publishes in `docs/images/`; it imports
them byte for byte and never makes its own. It now needs pictures of the three simulation
effects and of masks. Please add four shots to the README screenshot pipeline and commit
the images.

## What to add

Extend `SHOTS` in `src/scripts/live/readme_shots.py` and the pipeline with four images,
taken on the README footage (`src/scripts/readme-shots.py --sources …`) like every other
shot: a fresh `kt-app` process, English UI, 1920×1080 window, views reached through probe
rectangles and real gestures, crops taken from those rectangles, WebP quality 92. Every
step checks its precondition and stops naming the step.

| name (`docs/images/<name>.webp`) | what it shows |
|---|---|
| `fx-datamosh` | the same frame without and with **Datamosh**, side by side |
| `fx-camera-isp` | the same frame without and with **Camera ISP**, side by side |
| `fx-vhs-tape` | the **VHS Tape** effects window with the deck face, and the frame it gives |
| `masks` | the preview with a **mask** drawn on the picture and an effect limited to it |

### fx-datamosh

- A video event of the showcase project that starts right after a cut between two
  different shots (motion in the second shot helps: a drone pan, a run).
- Datamosh with the **Cut mosh** preset (the "drop the keyframe" breakage), so the
  previous shot is dragged by the new shot's motion.
- Pick the frame a few frames after the cut, where the smear is clearly visible but both
  shots are still recognisable.
- Two preview-frame crops of the same moment, the effect switched off (a copy of the
  project, as `morpher-before-after` does) and on, placed side by side with a 12 px gap on
  the window's background colour.
- **No text baked into the image** (unlike `morpher-before-after`): the site captions it in
  five languages and says which half is which ("left: without, right: with").

### fx-camera-isp

- A dark or evening clip if the footage has one (the Charlotte night drone shot), otherwise
  any clip with a bright and a dark area.
- Camera ISP with the **Phone at night** look.
- The same two-halves layout as `fx-datamosh`, no baked text; choose a frame where the
  noise, the denoise smear and the tone curve are visible at the image's display size
  (about 900 px per half).

### fx-vhs-tape

- One event with **VHS Tape**, its effects window open (`win.fx`) with the **deck face**
  visible: the drum with the heads, the switches, tracking. Make one head **dirty** or
  **clogged** by the gesture a person uses (`pick_head`), so the picture shows the
  resulting dropouts or snow rather than the default clean look.
- The crop holds the effects window and the preview frame beside it, the way the
  `video-fx` shot holds its window; if they do not fit one crop, a composite of the window
  and the preview frame side by side, no baked text.

### masks

- One event on the preview with a **Pen** mask drawn around a subject (a face, a figure, a
  vehicle): a closed Bézier path with a few smooth points and visible feather.
- An effect limited to that mask so the mask is obvious in the picture: for example Blur
  limited to the mask (or the inverted mask), or Color Grade only inside it.
- The mask path and its points visible on the preview, and the Masks list visible in the
  Geometry node or the effect slot (wherever the effects window shows it).
- Crop: the preview with the drawn mask, plus the Masks list if it fits in one readable
  image; otherwise the preview alone.

## Conventions

- File names exactly as in the table; the site declares slots with these names. If a name
  must change, keep the four names stable afterwards and say which in the commit message.
- `readme-check.py` requires the docs to reference exactly the `SHOTS` set: reference the
  new images where they belong (the effects section of the README, the masks part of
  `docs/guide/effects-and-automation.md`, or `docs/guide/whats-new.md`), with alt text
  that says what is in the picture.
- Footage credits: if a shot uses a clip not yet in `docs/images/CREDITS.md`, add it there.
- Run the pipeline under `live-check.sh` too (the fixture-video mode) so the new steps
  cannot rot.
- Size: each image under about 400 KB, like the existing ones.

## Done when

`git ls-tree HEAD docs/images/` on `master` lists `fx-datamosh.webp`, `fx-camera-isp.webp`,
`fx-vhs-tape.webp` and `masks.webp`, `readme-check.py` passes, and the images were looked
at: each one shows what its row above says, sharp at its native size.
