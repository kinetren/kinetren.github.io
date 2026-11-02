## ADDED Requirements

### Requirement: The effects section shows the effects it singles out
The effects section SHALL show a row of screenshots of the effects and features the editor
singled out with their own image. At first these are Datamosh, Camera ISP, VHS Tape and
masks, from the editor's images `fx-datamosh.webp`, `fx-camera-isp.webp`,
`fx-vhs-tape.webp` and `masks.webp`.
Each image SHALL be one of the editor's own screenshots imported from its `docs/images/`,
like every other shot. Each SHALL carry a translated caption and alt text that name the
effect and say what the picture shows: the settings visible, the clip, and before and
after when the image has two halves. A caption SHALL NOT praise the effect. The row SHALL
keep the image proportions, and SHALL fall to one image per line at 375 px width with no
horizontal scroll.

#### Scenario: Four shots in the effects section
- **WHEN** the site is built and `dist/en/index.html` is read
- **THEN** the effects section holds an image row with four `<img>` elements pointing at `../assets/shots/fx-datamosh.webp`, `fx-camera-isp.webp`, `fx-vhs-tape.webp` and `masks.webp`, each with non-empty `alt`, `width` and `height`, and each followed by its caption

#### Scenario: Captions are descriptions
- **WHEN** the `effects.g_*_cap` values of all five catalogs are read
- **THEN** none of them contains an exclamation mark or the words "stunning", "amazing", "powerful", "cool", "real", "finally" or their translations, and each names the effect it shows

#### Scenario: Phone width
- **WHEN** `/ru/` is opened at 375 px width and the effects section is scrolled into view
- **THEN** the four images stand one under another at the column width, and `document.documentElement.scrollWidth` equals the viewport width

### Requirement: A returning visitor sees what changed since the last visit
The page SHALL carry, above the hero, an update strip listing the site's update entries
(`[updates]`). Each entry SHALL be shown as its date in the section-timecode style
(`26:11:02`) followed by its text. The visitor's browser SHALL remember the newest entry it
has shown, under one `localStorage` key. On load:
- if the key holds the newest entry, the strip SHALL stay hidden;
- if it holds an older entry, the strip SHALL show every entry newer than that one, newest
  first, at most three, and say how many older ones it leaves out;
- if the key is absent or unreadable, the strip SHALL show the newest entry only.

The strip SHALL have a close button and a link to the guide's What's new page
(`/docs/whats-new/`). Closing the strip or following its link SHALL store the newest entry.
A strip that is ignored SHALL appear again on the next visit. Without JavaScript, or when
storage throws, the page SHALL render correctly: the strip is hidden without JavaScript and
shows the newest entry when storage throws. The strip SHALL have no heading, no animation
and no image, and SHALL NOT cover the hero's headline or download panel. It sits in the
flow above them.

#### Scenario: A visitor from two updates ago
- **WHEN** `/en/` is opened with `localStorage["kt-seen"] = "261026"` and the entries 261102 and 261101 exist
- **THEN** the strip is visible and reads the 26:11:02 entry and then the 26:11:01 entry, and after the close button is pressed `localStorage["kt-seen"]` is "261102" and a reload shows no strip

#### Scenario: Up to date
- **WHEN** `/es/` is opened with `localStorage["kt-seen"]` equal to the newest entry
- **THEN** the strip element is hidden and no part of it is in the layout

#### Scenario: No stored value
- **WHEN** `/zh-Hans/` is opened in a fresh profile
- **THEN** the strip shows only the newest entry, and `localStorage["kt-seen"]` is still absent until the strip is closed or its link followed

#### Scenario: Without JavaScript
- **WHEN** `/ar/` is loaded with JavaScript disabled
- **THEN** no strip is visible and the hero is laid out as without the strip

### Requirement: Update entries name what changed
Every update entry SHALL be one line in each of the five catalogs, `updates.u<YYMMDD>`,
with the same key set in every catalog. It SHALL list named features and facts of that sync:
effect names, menu paths and what a user can now do. It is the same kind of text as a
roadmap summary, but it is written for every site sync that changed what the page says
about the editor, whether or not the editor tagged a release. An entry MUST NOT contain a
heading word ("Update", "News", "What's new"), an exclamation mark, an adjective of praise,
a version-count boast or a call to action. It MUST NOT name test numbers, CI runs, rounds or
internal stage names. An entry SHALL be at most 160 characters in English. Entries are
never rewritten after they are published, except to correct a fact.

#### Scenario: Entries are lists of features
- **WHEN** the `[updates]` values of `content/en.toml` are read
- **THEN** each is at most 160 characters, contains no "!", and none contains "update", "news", "new version", "huge", "big", "exciting", "finally", "cool" (case-insensitive)

#### Scenario: Every catalog has every entry
- **WHEN** the site is built
- **THEN** each id in `structure.toml [updates] entries` has its `updates.u<id>` key in all five catalogs, and a missing one fails the build naming the language and the key

## MODIFIED Requirements

### Requirement: Copy states facts, never slogans
Every sentence of the catalogs SHALL state a fact about the editor (what it does, what it
needs, how it is used), taken from the editor's README, guide or code. Catalogs MUST NOT
contain slogans, "X, not Y" antitheses, rhetorical closing lines or self-evident remarks
(the owner's rule: such phrases make the site read as machine-written). The single
exception is the hero's rotating headlines (`[headline]`): they ARE slogans and calls to
action, chosen by the owner, about what a visitor gets (price, freedom, audience, how fast
they start). They MUST NOT be internal facts retold as slogans ("The preview is the
export", "Every parameter on a curve"), which read as truisms. Every promise they make
SHALL be true of kinetren. Numbers on the page SHALL match the editor: the counts of video
effects, audio effects, transitions, track types and interface languages that
`upstream.py facts` reads from the editor's registry and catalog at the lock. The effects
section SHALL list every video effect by name; a "Transitions, titles, generators" section
SHALL describe those three features.

#### Scenario: Former filler phrases are gone
- **WHEN** `content/en.toml` and `content/ru.toml` are searched for "file you ship", "Direction, not dates", "Undo means undo", "Sound looks like sound"
- **THEN** there are no matches

#### Scenario: Headlines are slogans, not retold internals
- **WHEN** the `headline.*` values of `content/en.toml` are read
- **THEN** none of them is "The preview is the export", "Every parameter on a curve", "Edit a reel once, every copy follows" or "Swap the source, keep the cut", and every promise in them (free, Linux and Windows, Slowed+Reverb, VHS and Glow included, ready within a minute of the download) holds for the current release

#### Scenario: The counts are the editor's
- **WHEN** `python3 upstream.py facts` runs against the locked commit
- **THEN** it reports no mismatch for the video effects, audio effects, transitions, interface languages and hero numbers

### Requirement: Every number explains itself
The hero SHALL show five numbers: video effects, audio effects, transitions, track types and
interface languages. Each SHALL open, on mouse hover and on keyboard or touch focus, the
full list of what it counts, without JavaScript. The list box SHALL be drawn above
everything that follows the hero: no heading, slab or card of the next section may cover
any part of it. The count SHALL equal the length of its list. The track types are video,
audio, morph and camera. On narrow screens the numbers SHALL wrap into two columns with no
empty cell.

#### Scenario: Hovering "4" lists the track types
- **WHEN** the number 4 on `/ru/` is hovered or focused
- **THEN** a box appears below it reading "Видео · Аудио · Морф · Камера"

#### Scenario: The longest list is not covered by the next section
- **WHEN** the video-effects number on `/en/` is hovered at 1440 px and at 375 px width
- **THEN** the whole list box is visible and `document.elementFromPoint` at any point inside it returns the box or its text, not the "Rendering" heading or its section

#### Scenario: Counts match the lists
- **WHEN** each `stats.<id>_list` value in `content/en.toml` is split on " · "
- **THEN** each item count equals its number in `structure.toml`, and `upstream.py facts` reports those numbers as the editor's
