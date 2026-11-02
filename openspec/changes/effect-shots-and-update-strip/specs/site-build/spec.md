## ADDED Requirements

### Requirement: The page keeps only named values in the visitor's browser
The page's script SHALL store nothing in the visitor's browser except these keys:
- `localStorage["lang"]`: the language chosen in the switcher;
- `localStorage["kt-seen"]`: the id of the newest update entry the strip has shown and the
  visitor has closed or followed;
- `sessionStorage["kt-release"]`: the cached latest-release answer.

It SHALL set no cookies. The update strip SHALL make no network request. Every read and
write SHALL be wrapped so that a browser that blocks storage still renders the page and its
download panel. The strip's logic SHALL run once at load and SHALL NOT start a timer or an
animation, so the idle-page rule of this capability holds with the strip visible.

#### Scenario: Only the named keys
- **WHEN** `/en/` is opened in a fresh profile, the language switcher is used once, the update strip is closed, and storage is listed
- **THEN** `localStorage` holds only `lang` and `kt-seen`, `sessionStorage` holds at most `kt-release`, and `document.cookie` is empty

#### Scenario: Storage blocked
- **WHEN** `/ru/` is opened with site data blocked, so every `localStorage` access throws
- **THEN** the page renders with no console error, the download panel works, and the strip shows the newest entry

#### Scenario: Idle with the strip open
- **WHEN** `/en/` is opened with the strip visible, scrolled to `#roadmap` and left for 10 seconds
- **THEN** no animation is running and the network log has no request after load besides the one to `api.github.com`
