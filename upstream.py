#!/usr/bin/env python3
"""Keep the site in step with the kinetren editor (github.com/kinetren/kinetren).

The site is written from the editor: its specs, its user guide, its UI catalog, its
screenshots and its tags. upstream.lock records the editor commit the site was last
synced to and the SHA-256 of every file imported from it; this tool reports what changed
since then, imports the files the site takes verbatim, and compares the facts that a
program can compare.

    python3 upstream.py status [--json]   what changed in the editor since the lock,
                                          grouped by the site section it concerns
    python3 upstream.py import            copy screenshots, icon, credits and the user
                                          guide, then rewrite upstream.lock
    python3 upstream.py facts             names, counts and versions: site vs editor

The checkout is --from <path>, else $KINETREN_CHECKOUT, else a sibling directory
(../kinetren, ../kinotrain.9) whose origin is kinetren/kinetren. Files are read from a
committed revision (--rev, default HEAD), never from the working tree: the editor's own
agent always has unfinished work there. The checkout is only read — no fetch, pull,
checkout or write; pulling is done in the editor repository.

Asking an agent here to update the site runs the whole procedure:
.claude/skills/site-update/SKILL.md.
"""

import argparse
import collections
import hashlib
import json
import os
import pathlib
import posixpath
import re
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
SHOTS = ASSETS / "shots"
GUIDE = ASSETS / "guide"
ICON = ASSETS / "kinetren.svg"
LOCK = ROOT / "upstream.lock"

REPOSITORY = "https://github.com/kinetren/kinetren"
ORIGIN_RE = re.compile(r"github\.com[:/]kinetren/kinetren(?:\.git)?/?$")
SIBLINGS = ("kinetren", "kinotrain.9")

# Editor paths of what the site imports verbatim.
UP_IMAGES = "docs/images"
UP_GUIDE = "docs/guide"
UP_CREDITS = "docs/images/CREDITS.md"
UP_ICON = "src/packaging/kinetren.svg"
# Editor paths the mechanical fact checks read.
UP_CATALOG = "src/apps/kt-app/i18n/en.toml"
UP_FX = "src/apps/kt-app/src/fx_registry.rs"
UP_README = "README.md"

GUIDE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
VIDEO_FX_RE = re.compile(r'^\s*"([^"]+)"\s*=>\s*\{?\s*\(k::fxreg::cat::', re.M)
AUDIO_FX_RE = re.compile(r'^\s*name:\s*"([^"]+)"', re.M)
VERSION_TAG_RE = re.compile(r"^v(\d\d\.\d\d\.\d\d)(?:\.\d+)?$")


class Fatal(Exception):
    pass


# ----------------------------------------------------------------------- git --

class Checkout:
    """Read-only access to an editor checkout through git objects."""

    def __init__(self, path):
        self.path = path

    def run(self, *args, binary=False, check=True):
        # --no-optional-locks: `git status` must not even refresh the index file.
        res = subprocess.run(["git", "--no-optional-locks", "-C", str(self.path), *args],
                             capture_output=True, text=not binary)
        if check and res.returncode != 0:
            err = res.stderr if not binary else res.stderr.decode(errors="replace")
            raise Fatal(f"git {' '.join(args)}: {err.strip()}")
        return res

    def out(self, *args):
        return self.run(*args).stdout.strip()

    def exists(self, rev, path):
        return self.run("cat-file", "-e", f"{rev}:{path}", check=False).returncode == 0

    def blob(self, rev, path):
        return self.run("cat-file", "blob", f"{rev}:{path}", binary=True).stdout

    def text(self, rev, path):
        return self.blob(rev, path).decode("utf-8")

    def ls(self, rev, path):
        res = self.run("ls-tree", "--name-only", f"{rev}:{path}", check=False)
        return res.stdout.split() if res.returncode == 0 else []

    def commit(self, rev):
        return self.out("rev-parse", "--verify", "-q", f"{rev}^{{commit}}")

    def version_tags(self, rev):
        """v* tags reachable from rev, newest version first."""
        tags = self.out("tag", "--merged", rev, "-l", "v*", "--sort=-v:refname")
        return [t for t in tags.splitlines() if VERSION_TAG_RE.match(t)]


def find_checkout(explicit):
    if explicit:
        candidates = [pathlib.Path(explicit)]
    elif os.environ.get("KINETREN_CHECKOUT"):
        candidates = [pathlib.Path(os.environ["KINETREN_CHECKOUT"])]
    else:
        candidates = [ROOT.parent / name for name in SIBLINGS]
    for path in candidates:
        path = path.expanduser().resolve()
        if not (path / ".git").exists():
            continue
        res = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"],
                             capture_output=True, text=True)
        if res.returncode == 0 and ORIGIN_RE.search(res.stdout.strip()):
            return Checkout(path)
        if explicit or os.environ.get("KINETREN_CHECKOUT"):
            raise Fatal(f"{path}: origin is not kinetren/kinetren ({res.stdout.strip() or 'none'})")
    raise Fatal("no kinetren checkout found: pass --from <path> or set KINETREN_CHECKOUT "
                f"(looked for {', '.join('../' + s for s in SIBLINGS)} with origin "
                "kinetren/kinetren)")


# ---------------------------------------------------------------- site side --

def load_structure():
    return tomllib.loads((CONTENT / "structure.toml").read_text(encoding="utf-8"))


def load_catalog(code):
    return tomllib.loads((CONTENT / f"{code}.toml").read_text(encoding="utf-8"))


def read_lock():
    if not LOCK.is_file():
        return None
    return tomllib.loads(LOCK.read_text(encoding="utf-8"))


def toml_str(value):
    return json.dumps(value, ensure_ascii=False)


def write_lock(commit, tag, date, files):
    lines = [
        "# The editor commit this site was last synced to, and every file imported",
        "# from it with its SHA-256. Written by `python3 upstream.py import` only;",
        "# build.py fails when an imported file differs from its entry here.",
        "",
        f"repository = {toml_str(REPOSITORY)}",
        f"commit = {toml_str(commit)}",
        f"tag = {toml_str(tag)}",
        f"date = {toml_str(date)}",
    ]
    for path, source, digest in sorted(files):
        lines += ["", "[[file]]", f"path = {toml_str(path)}", f"source = {toml_str(source)}",
                  f"sha256 = {toml_str(digest)}"]
    LOCK.write_text("\n".join(lines) + "\n", encoding="utf-8")


def under(path, prefix):
    prefix = prefix.rstrip("/")
    return path == prefix or path.startswith(prefix + "/")


# -------------------------------------------------------------------- import --

def guide_pages(co, rev):
    return sorted(f for f in co.ls(rev, UP_GUIDE) if f.endswith(".md"))


def guide_images(co, rev, pages):
    """Editor paths of the images the guide shows, {path: [page, ...]}."""
    found = collections.defaultdict(list)
    for page in pages:
        for target in GUIDE_IMAGE_RE.findall(co.text(rev, f"{UP_GUIDE}/{page}")):
            if re.match(r"^[a-z]+:", target):
                continue
            resolved = posixpath.normpath(posixpath.join(UP_GUIDE, target))
            found[resolved].append(page)
    return found


def import_plan(co, rev, struct):
    """[(destination under ROOT, editor path)] for everything the site takes."""
    plan = []
    shots = {meta["file"] for meta in struct["shot"].values()}
    pages = guide_pages(co, rev)
    for path, users in sorted(guide_images(co, rev, pages).items()):
        if posixpath.dirname(path) != UP_IMAGES:
            raise Fatal(f"{', '.join(users)}: image {path} is outside {UP_IMAGES}/")
        shots.add(posixpath.basename(path))
    for name in sorted(shots):
        plan.append((f"assets/shots/{name}", f"{UP_IMAGES}/{name}"))
    plan.append(("assets/shots/CREDITS.md", UP_CREDITS))
    plan.append(("assets/kinetren.svg", UP_ICON))
    for page in pages:
        plan.append((f"assets/guide/{page}", f"{UP_GUIDE}/{page}"))
    return plan


def cmd_import(co, rev, args):
    struct = load_structure()
    commit = co.commit(rev)
    if not commit:
        raise Fatal(f"{rev}: no such revision in {co.path}")
    plan = import_plan(co, commit, struct)
    missing = [src for _, src in plan if not co.exists(commit, src)]
    if missing:
        for src in missing:
            print(f"missing at {commit[:10]}: {src}", file=sys.stderr)
        print("nothing changed", file=sys.stderr)
        return 1
    blobs = [(dst, src, co.blob(commit, src)) for dst, src in plan]

    keep = set()
    for dst, src, data in blobs:
        target = ROOT / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != data:
            target.write_bytes(data)
            print(f"{dst}  <-  {src}")
        keep.add(target)
    for folder in (SHOTS, GUIDE):
        for old in sorted(folder.iterdir()):
            if old.is_file() and old not in keep:
                old.unlink()
                print(f"removed {old.relative_to(ROOT)} (the editor no longer has it or nothing uses it)")

    tags = co.version_tags(commit)
    date = co.out("log", "-1", "--format=%cI", commit)
    write_lock(commit, tags[0] if tags else "", date,
               [(dst, src, hashlib.sha256(data).hexdigest()) for dst, src, data in blobs])
    print(f"upstream.lock -> {commit[:10]} {tags[0] if tags else '(no tag)'} {date}")
    print("next: python3 build.py && python3 build.py --check && python3 upstream.py facts")
    return 0


# -------------------------------------------------------------------- status --

def section_sources(struct):
    return [(sec["id"], sec.get("upstream")) for sec in struct["section"]]


def status_data(co, rev):
    struct = load_structure()
    lock = read_lock()
    if not lock:
        raise Fatal("no upstream.lock yet: run python3 upstream.py import")
    base = lock["commit"]
    if not co.commit(base):
        raise Fatal(f"the checkout does not have the locked commit {base[:10]}: "
                    "pull in the editor repository")
    target = co.commit(rev)
    if not target:
        raise Fatal(f"{rev}: no such revision in {co.path}")

    data = {
        "checkout": str(co.path),
        "lock": {"commit": base, "tag": lock.get("tag", ""), "date": lock.get("date", "")},
        "target": {"commit": target, "rev": rev},
        "up_to_date": base == target,
        "commits": [], "tags": [], "sections": {}, "guide": [], "images": [],
        "icon": False, "not_mapped": {}, "missing_upstream": {}, "notes": [],
    }

    sources = section_sources(struct)
    for sec_id, paths in sources:
        if paths is None:
            data["missing_upstream"].setdefault(sec_id, []).append("(no upstream list)")
            continue
        gone = [p for p in paths if not co.exists(target, p)]
        if gone:
            data["missing_upstream"][sec_id] = gone

    watched = sorted({p for _, paths in sources for p in (paths or [])}
                     | {UP_GUIDE, UP_IMAGES, UP_ICON})
    dirty = co.out("status", "--porcelain", "--", *watched)
    if dirty:
        data["notes"].append("uncommitted changes under watched paths are ignored "
                             "(only committed revisions are read): "
                             + ", ".join(line[3:] for line in dirty.splitlines()))
    branch = co.run("symbolic-ref", "--short", "-q", "HEAD", check=False).stdout.strip()
    if branch and co.commit(f"origin/{branch}"):
        ahead = co.out("rev-list", "--count", f"HEAD..origin/{branch}")
        if ahead != "0":
            data["notes"].append(f"origin/{branch} is {ahead} commit(s) ahead of HEAD in the "
                                 "last fetched refs: pull in the editor repository to sync those too")

    if data["up_to_date"]:
        return data

    log = co.out("log", "--format=%h%x09%cs%x09%s", f"{base}..{target}")
    data["commits"] = [dict(zip(("hash", "date", "subject"), line.split("\t", 2)))
                       for line in log.splitlines() if line]
    old_tags = set(co.version_tags(base))
    for tag in reversed(co.version_tags(target)):
        if tag not in old_tags:
            data["tags"].append({"tag": tag, "date": co.out("log", "-1", "--format=%cs", tag)})

    changed = co.out("diff", "--name-only", base, target).splitlines()
    imported = {src for _, src in import_plan(co, target, struct)}
    not_mapped = collections.Counter()
    for path in changed:
        hit = False
        for sec_id, paths in sources:
            if any(under(path, p) for p in paths or []):
                data["sections"].setdefault(sec_id, []).append(path)
                hit = True
        if under(path, UP_GUIDE):
            data["guide"].append(path)
            hit = True
        elif path in imported and under(path, UP_IMAGES):
            data["images"].append(path)
            hit = True
        elif path == UP_ICON:
            data["icon"] = hit = True
        if not hit:
            parts = path.split("/")
            not_mapped["/".join(parts[:2]) if len(parts) > 2 else parts[0]] += 1
    data["not_mapped"] = dict(sorted(not_mapped.items(), key=lambda kv: (-kv[1], kv[0])))
    return data


def print_status(data):
    lock, target = data["lock"], data["target"]
    print(f"editor checkout  {data['checkout']}")
    print(f"locked           {lock['commit'][:10]} {lock['tag'] or '(no tag)'} {lock['date']}")
    print(f"target           {target['commit'][:10]} ({target['rev']})")
    for note in data["notes"]:
        print(f"note: {note}")
    for sec_id, paths in data["missing_upstream"].items():
        print(f"missing upstream: section {sec_id}: {', '.join(paths)}")
    if data["up_to_date"]:
        print("\nthe site is up to date with the editor")
        return
    print(f"\n{len(data['commits'])} commit(s):")
    for c in data["commits"]:
        print(f"  {c['hash']} {c['date']} {c['subject']}")
    if data["tags"]:
        print("\nnew version tags (the roadmap needs an entry per date):")
        for t in data["tags"]:
            print(f"  {t['tag']}  {t['date']}")
    if data["sections"]:
        print("\nsections whose sources changed:")
        for sec_id, paths in data["sections"].items():
            print(f"  {sec_id}:")
            for p in paths:
                print(f"    {p}")
    if data["guide"]:
        print("\nguide pages changed (re-import; /docs/ follows):")
        for p in data["guide"]:
            print(f"  {p}")
    if data["images"] or data["icon"]:
        print("\nimported images changed (re-import):")
        for p in data["images"] + ([UP_ICON] if data["icon"] else []):
            print(f"  {p}")
    if data["not_mapped"]:
        print("\nnot mapped to any section (files changed, by directory):")
        for d, n in data["not_mapped"].items():
            print(f"  {n:4d}  {d}")


def cmd_status(co, rev, args):
    data = status_data(co, rev)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_status(data)
    return 0


# --------------------------------------------------------------------- facts --

class Facts:
    def __init__(self):
        self.rows = []

    def compare(self, name, site, editor):
        """site and editor are lists of names (editor None = cannot extract)."""
        if editor is None or not editor or len(set(editor)) != len(editor):
            why = "nothing found" if not editor else "names repeat"
            self.rows.append(("?", name, f"cannot verify from the editor ({why})"))
            return
        # Spelling is compared without spaces and case: "Event Grid" on the site is
        # the editor's "EventGrid" — the same effect, reported as a note.
        norm = lambda s: re.sub(r"\s+", "", s).casefold()
        site_n = {norm(x): x for x in site}
        editor_n = {norm(x): x for x in editor}
        missing = [x for k, x in editor_n.items() if k not in site_n]
        extra = [x for k, x in site_n.items() if k not in editor_n]
        spelled = [f"{site_n[k]} (editor: {x})" for k, x in editor_n.items()
                   if k in site_n and site_n[k] != x]
        if missing or extra or len(site) != len(editor):
            parts = [f"site {len(site)}, editor {len(editor)}"]
            if missing:
                parts.append("missing on the site: " + ", ".join(missing))
            if extra:
                parts.append("not in the editor: " + ", ".join(extra))
            self.rows.append(("FAIL", name, "; ".join(parts)))
        else:
            self.rows.append(("ok", name, f"{len(site)}"))
        if spelled:
            self.note(name, "spelled differently: " + ", ".join(spelled))

    def check(self, ok, name, detail):
        self.rows.append(("ok" if ok else "FAIL", name, detail))

    def note(self, name, detail):
        self.rows.append(("note", name, detail))

    def failed(self):
        return any(r[0] == "FAIL" for r in self.rows)


def parse_catalog(text):
    """{section: {key: value}} from the editor's catalog. Not tomllib: the editor's
    own reader accepts a key and a table of the same name ([trn] kind = ... next to
    [trn.kind]), which TOML forbids. Each `key = "value"` line is parsed alone."""
    out, section = {}, ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([A-Za-z0-9_.-]+)\]$", line)
        if m:
            section = m.group(1)
            out.setdefault(section, {})
            continue
        try:
            pair = tomllib.loads(line)
        except tomllib.TOMLDecodeError:
            continue
        out.setdefault(section, {}).update(pair)
    return out


def split_list(value):
    return [x.strip() for x in str(value).split(" · ") if x.strip()]


def cmd_facts(co, rev, args):
    struct = load_structure()
    target = co.commit(rev)
    if not target:
        raise Fatal(f"{rev}: no such revision in {co.path}")
    en = load_catalog("en")
    langs = struct["site"]["langs"]
    hero = next(s for s in struct["section"] if s["component"] == "hero")
    numbers = dict(zip(hero["stat_ids"], hero["stats"]))
    facts = Facts()

    editor_cat = None
    if co.exists(target, UP_CATALOG):
        editor_cat = parse_catalog(co.text(target, UP_CATALOG))

    # Language self-names: byte-identical in every catalog and in the editor.
    editor_lang = (editor_cat or {}).get("lang")
    for code in langs:
        site_lang = load_catalog(code).get("lang", {})
        if not editor_lang:
            facts.compare(f"[lang] in {code}.toml", [], None)
        else:
            same = site_lang == editor_lang
            facts.check(same, f"[lang] in {code}.toml",
                        "identical to the editor" if same else
                        f"differs: site {site_lang} vs editor {editor_lang}")
    if editor_lang:
        facts.compare("interface languages (stats.langs_list)",
                      split_list(en["stats"]["langs_list"]), list(editor_lang.values()))

    # Transitions: the editor catalog's [trn.kind] is the list of kinds.
    kinds = (editor_cat or {}).get("trn.kind")
    editor_trn = [v for v in kinds.values() if isinstance(v, str)] if kinds else None
    facts.compare("transitions (stats.transitions_list)",
                  split_list(en["stats"]["transitions_list"]), editor_trn)

    # Effects: the editor's registry. A regex over Rust source — when it finds
    # nothing, the result is "cannot verify", never a silent match.
    fx_src = co.text(target, UP_FX) if co.exists(target, UP_FX) else ""
    editor_vfx = VIDEO_FX_RE.findall(fx_src) or None
    editor_afx = AUDIO_FX_RE.findall(fx_src) or None
    facts.compare("video effects ([fx] names)", struct["fx"]["names"], editor_vfx)
    facts.compare("video effects (stats.vfx_list)", split_list(en["stats"]["vfx_list"]), editor_vfx)
    facts.compare("audio effects (stats.afx_list)", split_list(en["stats"]["afx_list"]), editor_afx)
    body = re.sub(r"<[^>]+>", "", en["effects"]["list_body"]).split(". ")[0]
    facts.compare("audio effects (effects.list_body)",
                  [x.strip() for x in body.split(",") if x.strip()], editor_afx)

    # Every hero number is the length of the list it opens.
    for stat_id, number in numbers.items():
        count = len(split_list(en["stats"][f"{stat_id}_list"]))
        facts.check(str(count) == str(number), f"hero number {stat_id}",
                    f"{number} on the page, {count} in stats.{stat_id}_list")

    # Versions: one roadmap entry per tag date.
    roadmap = next(s for s in struct["section"] if s["component"] == "roadmap")
    site_versions = set(roadmap["versions"])
    tag_dates = collections.OrderedDict()
    for tag in co.version_tags(target):
        tag_dates.setdefault(VERSION_TAG_RE.match(tag).group(1), []).append(tag)
    missing = [f"{', '.join(tags)}" for day, tags in tag_dates.items() if day not in site_versions]
    facts.check(not missing, "roadmap versions vs v* tags",
                f"{len(tag_dates)} tag date(s) listed" if not missing else
                "no roadmap entry for " + "; ".join(missing))
    for day in tag_dates:
        for code in langs:
            if f"v{day.replace('.', '')}" not in load_catalog(code).get("roadmap", {}):
                facts.check(False, f"roadmap.v{day.replace('.', '')} in {code}.toml", "missing")

    # Notes, not failures: links in the editor's README that differ from the site.
    if co.exists(target, UP_README):
        readme = co.text(target, UP_README)
        invites = sorted(set(re.findall(r"https://discord\.gg/[A-Za-z0-9]+", readme)))
        if invites and invites != [struct["site"]["discord"]]:
            facts.note("Discord invite", f"the editor README links {', '.join(invites)}, "
                                         f"the site {struct['site']['discord']}")
        sys.path.insert(0, str(ROOT))
        from build import DEFAULT_BASE
        if DEFAULT_BASE not in readme:
            sites = sorted(set(re.findall(r"\]\((https://kinetren[^)/]*)\)", readme)))
            facts.note("site address", f"the editor README links {', '.join(sites) or 'no site'}, "
                                       f"the site is {DEFAULT_BASE}")

    width = max(len(r[1]) for r in facts.rows)
    for mark, name, detail in facts.rows:
        print(f"{mark:4}  {name:<{width}}  {detail}")
    print(f"\nagainst {target[:10]} ({rev}); "
          + ("mismatches found" if facts.failed() else "no mismatches"))
    return 1 if facts.failed() else 0


# ---------------------------------------------------------------------- main --

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("status", "import", "facts"))
    ap.add_argument("--from", dest="checkout", metavar="CHECKOUT",
                    help="path to a kinetren checkout (default: $KINETREN_CHECKOUT, "
                         "then ../kinetren or ../kinotrain.9)")
    ap.add_argument("--rev", default="HEAD",
                    help="editor revision to read (default HEAD; never the working tree)")
    ap.add_argument("--json", action="store_true", help="status: print one JSON object")
    args = ap.parse_args()
    try:
        co = find_checkout(args.checkout)
        return {"status": cmd_status, "import": cmd_import, "facts": cmd_facts}[args.command](
            co, args.rev, args)
    except Fatal as e:
        print(f"upstream.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
