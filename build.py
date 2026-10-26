#!/usr/bin/env python3
"""Build the kinetren landing page from formal sources.

Introduced in round R.19 on three requests from the owner: generate the landing
page from something formal, stop shipping one fat HTML blob, and go
multilingual with the language in the path for SEO. Before that, index.html
was a hand-written 446 KB file, 89 % of it base64, one image embedded twice.

Inputs:
    content/structure.toml   page form: section order, components, images,
                             effect names, numbers, guide page order
    content/<lang>.toml      prose only; en.toml is the reference for the key
                             set and order, exactly like the editor's i18n/en.toml
    assets/kt.css            styles (a source, not generated)
    assets/shots/*.webp      screenshots, one set for every language, and the
                             images of the guide, from the editor's docs/images/
    assets/shots/CREDITS.md  authors and licenses of the footage -> credits.html
    assets/kinetren.svg      the icon (= the editor's src/packaging/kinetren.svg)
    assets/guide/*.md        the editor's user guide (docs/guide/) -> dist/docs/
    upstream.lock            the editor commit of those imports and their SHA-256;
                             everything above under assets/ except kt.css comes
                             from `python3 upstream.py import` and is never edited
Outputs:
    dist/                    the finished site, THE ROOT THAT IS PUBLISHED
    assets/fonts/            font subsets + FONT-MANIFEST.txt

The checks mirror the editor's apps/kt-app/build.rs: a missing or extra key, an
empty value, placeholders that differ from English, an ASCII comma in Arabic
are build errors. A value identical to English is a warning, and it decides the
language's fate: a catalog translated below translated_min is built but gets
noindex and stays out of the sitemap and hreflang. Once translated, the
language is indexed by itself; nothing is marked by hand.

Requires fontTools (pyftsubset) and Pillow. Nothing outside the repository is
read except the system fonts.

    python3 build.py
    python3 build.py --base-url https://example.org
    python3 build.py --check     # does dist/ match the sources?
    python3 build.py --serve     # build and serve at http://127.0.0.1:8000/
"""

import argparse
import collections
import hashlib
import html
import json
import os
import pathlib
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
FONTS_OUT = ASSETS / "fonts"
DIST = ROOT / "dist"
FONT_MANIFEST = FONTS_OUT / "FONT-MANIFEST.txt"

SHOTS = ASSETS / "shots"
ICON = ASSETS / "kinetren.svg"
CREDITS = SHOTS / "CREDITS.md"
GUIDE = ASSETS / "guide"
LOCK = ROOT / "upstream.lock"
REPOSITORY = "https://github.com/kinetren/kinetren"
IMPORT_HINT = "python3 upstream.py import"

DEFAULT_BASE = "https://www.kinetren.com"

# Markup allowed inside translated values. Everything else is escaped: a
# translator must not be able to break the layout.
INLINE_TAGS = ("em", "strong", "kbd", "code", "br")
TAG_RE = re.compile(r"&lt;(/?)(" + "|".join(INLINE_TAGS) + r")\s*/?&gt;")
ANY_TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)")
PLACEHOLDER_RE = re.compile(r"\{(\d+)\}")

# The same ranges as the editor's scripts/subset-fonts.py and bidi.rs.
CJK_RANGES = [(0x2E80, 0x9FFF), (0x3000, 0x303F), (0x3400, 0x4DBF), (0xFF00, 0xFFEF)]
AR_RANGES = [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
             (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]

UBUNTU_VAR = pathlib.Path("/usr/share/fonts/truetype/ubuntu/Ubuntu[wdth,wght].ttf")
UBUNTU_MONO = pathlib.Path("/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf")
CJK_SOURCES = [("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2)]
AR_SOURCES = [("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf", 0),
              ("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf", 0)]
# Ubuntu has no arrows: the guide's "File → Render to MP4…", ↑/↓ and ▸ come
# from this face, subset to exactly the characters Ubuntu lacks.
SYMBOL_SOURCES = [("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0)]
# Arabic joining lives in these features: without init/medi/fina/isol the
# letters fall apart into isolated forms, and it shows.
AR_FEATURES = "ccmp,locl,init,medi,fina,isol,rlig,liga,calt,mark,mkmk,kern"

# fontTools stamps the current time into head.modified, so the same source
# gave new bytes every run — a new hashed file name, new CSS, new pages, and
# --check failed every time. Pin the build date: fontTools reads
# SOURCE_DATE_EPOCH, the standard way to make builds reproducible.
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

problems: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    if msg not in problems:
        problems.append(msg)


# ------------------------------------------------------------------ sources --

def load_sources():
    structure = tomllib.loads((CONTENT / "structure.toml").read_text(encoding="utf-8"))
    langs = structure["site"]["langs"]
    cats = {}
    for code in langs:
        path = CONTENT / f"{code}.toml"
        if not path.exists():
            fail(f"missing catalog {path.name}")
            continue
        cats[code] = flatten(tomllib.loads(path.read_text(encoding="utf-8")))
    return structure, cats


def flatten(tree, prefix=""):
    """{'a': {'b': 'x'}} -> {'a.b': 'x'}"""
    out = {}
    for key, value in tree.items():
        full = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(flatten(value, full + "."))
        else:
            out[full] = value
    return out


# ------------------------------------------------------------------- checks --

def validate(cats, ref="en"):
    """Errors fail the build; warnings are only counted."""
    reference = cats[ref]
    for key, value in reference.items():
        if not str(value).strip():
            fail(f"{ref}: empty value {key}")
    coverage = {}
    for code, cat in cats.items():
        missing = [k for k in reference if k not in cat]
        extra = [k for k in cat if k not in reference]
        for k in missing:
            fail(f"{code}: missing key {k}")
        for k in extra:
            fail(f"{code}: key {k} exists only here, add it to {ref}.toml")
        same = 0
        counted = 0
        for key, value in cat.items():
            text = str(value)
            if not text.strip():
                fail(f"{code}: empty value {key}")
                continue
            check_markup(code, key, text)
            if key in reference:
                a = sorted(PLACEHOLDER_RE.findall(str(reference[key])))
                b = sorted(PLACEHOLDER_RE.findall(text))
                if a != b:
                    fail(f"{code}: placeholders of {key} differ from {ref} ({a} vs {b})")
            # Arabic needs its own punctuation: it is inside the Arabic block
            # and does not break the word (the same rule as i18n/README.md).
            if code == "ar" and has_arabic(text):
                for bad, good in ((",", "،"), (";", "؛"), ("?", "؟")):
                    if bad in text:
                        fail(f"ar: {key} — ASCII '{bad}', use '{good}'")
            # [lang] is identical in every catalog by design; leave it out of the count
            if key.startswith("lang."):
                continue
            counted += 1
            if key in reference and text == str(reference[key]):
                same += 1
        coverage[code] = 1.0 if code == ref else (1.0 - same / counted if counted else 0.0)
        if code != ref and same:
            notes.append(f"{code}: {same} of {counted} values equal English "
                         f"→ {coverage[code]*100:.0f}% translated")
    return coverage


def check_markup(code, key, text):
    for tag in sorted(set(ANY_TAG_RE.findall(text))):   # <script>…</script> is one complaint, not two
        if tag.lower() not in INLINE_TAGS:
            fail(f"{code}: {key} — tag <{tag}> is not allowed, only "
                 f"{', '.join('<%s>' % t for t in INLINE_TAGS)}")
    for tag in INLINE_TAGS:
        if tag == "br":
            continue
        if text.count(f"<{tag}>") != text.count(f"</{tag}>"):
            fail(f"{code}: {key} — unpaired <{tag}>")


def has_arabic(text):
    return any(in_ranges(ord(c), AR_RANGES) for c in text)


def in_ranges(cp, ranges):
    return any(lo <= cp <= hi for lo, hi in ranges)


# ------------------------------------------------------------------- output --

def esc(text):
    """Escape everything, then restore the allowed inline tags."""
    return TAG_RE.sub(r"<\1\2>", html.escape(str(text), quote=False))


def attr(text):
    return html.escape(str(text), quote=True)


class Cat:
    """A catalog that falls back to English, so an untranslated page is built
    whole instead of falling apart into holes."""

    def __init__(self, cat, fallback):
        self.cat, self.fallback = cat, fallback

    def __call__(self, key, default=None):
        value = self.cat.get(key, self.fallback.get(key, default))
        if value is None:
            fail(f"key {key} is in neither the catalog nor English")
            return ""
        return esc(value)

    def raw(self, key):
        return str(self.cat.get(key, self.fallback.get(key, "")))


# --------------------------------------------------------------- components --

def head_block(sec, t):
    tc = sec.get("timecode")
    # clock = true: the page script replaces the text with the current time.
    clock = ' data-clock' if sec.get("clock") else ""
    tc_html = f'<span class="tc"{clock}>{attr(tc)}</span>' if tc else ""
    return (f'<div class="head">{tc_html}'
            f'<h2>{t(sec["id"] + ".title")}</h2><span class="rule"></span></div>')


def standfirst(sec, t):
    key = sec["id"] + ".standfirst"
    text = t(key, "")
    return f'<p class="standfirst">{text}</p>' if text else ""


def shot_src(slot, file):
    """One English set serves every language (owner, 2026-10-24): the files
    are the editor's own showcase shots, imported by upstream.py. A slot
    whose file is missing is a build error, not a silent fallback.

    Returns (src, w, h) or None. The size is read from the image itself: the
    editor's pipeline crops by probe rectangles, so the size is data."""
    path = SHOTS / file
    if not path.is_file():
        fail(f"[shot.{slot}]: no file assets/shots/{file} — {IMPORT_HINT}")
        return None
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    return f"../assets/shots/{file}", w, h


def shot(struct, name, t, prefix, *, cap_key=None, alt_key=None, klass=""):
    meta = struct["shot"][name]
    alt = t(alt_key or f"{prefix}.shot_alt", "")
    cap = t(cap_key, "") if cap_key else ""
    found = shot_src(name, meta["file"])
    if not found:
        return ""
    src, w, h = found
    out = (f'<div class="shot {klass}" style="--nw:{w}px">'
           f'<img src="{src}" width="{w}" '
           f'height="{h}" alt="{attr(strip_tags(alt))}" loading="lazy" '
           f'decoding="async"></div>')
    if cap:
        out += f'<p class="cap">{cap}</p>'
    return out


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)


def download_panel(struct, t):
    """The download panel of the hero and of the "Download" section. Static,
    it offers both builds through GitHub's latest-release page. The head script
    marks the visitor's system on <html> (os-win / os-linux) and the CSS keeps
    that system's button with the other build as a small link; the page script
    points [data-dl] at the latest release's files and writes the version and
    size into [data-dl-label]."""
    latest = attr(struct["site"]["releases_latest"])
    items = "".join(
        f'<div class="dl-item" data-os="{os}">'
        f'<a class="btn btn-primary" data-dl="{os}" href="{latest}">{t("dl." + os)}</a>'
        f'<span class="dl-note">{t("dl." + os + "_note")}'
        f'<span class="dl-label" data-dl-label="{os}"></span></span></div>'
        for os in ("win", "linux"))
    others = "".join(
        f'<a class="dl-other" data-dl="{os}" data-os-other="{os}" href="{latest}">'
        f'{t("dl.other_" + os)}</a>' for os in ("win", "linux"))
    return f"""<div class="dl">
      {items}
      <p class="dl-systems">{t("dl.systems")}</p>
      <p class="dl-links">{others}<a href="{attr(struct["site"]["releases"])}">{t("dl.all_releases")}</a><a href="#roadmap">{t("dl.whats_new")}</a></p>
    </div>"""


def headline(cats_en, t):
    """The rotating headline: l1 is the <h1>; the other lines sit in the same
    grid cell, hidden from assistive technology, and the page script shows
    them in turn."""
    keys = sorted((k for k in cats_en if k.startswith("headline.l")),
                  key=lambda k: int(k[len("headline.l"):]))
    lines = [f'<h1 class="hl on">{t(keys[0])}</h1>']
    lines += [f'<p class="hl" aria-hidden="true">{t(k)}</p>' for k in keys[1:]]
    return "".join(lines)


def c_hero(sec, struct, t, ctx):
    # Each number opens what it counts on hover or keyboard focus.
    stats = "".join(
        f'<div class="stat" tabindex="0"><b>{attr(n)}</b><span>{t("stats." + i)}</span>'
        f'<div class="pop" role="tooltip">{t("stats." + i + "_list")}</div></div>'
        for n, i in zip(sec["stats"], sec["stat_ids"]))
    hero = shot_src(sec["shot"], struct["shot"][sec["shot"]]["file"])
    inset = shot_src(sec["inset"], struct["shot"][sec["inset"]]["file"])
    if not hero or not inset:
        return ""
    hero_src, hero_w, hero_h = hero
    inset_src, inset_w, inset_h = inset
    ticks = "".join(
        f'<span class="ruler-tc" style="inset-inline-start:{p}%">{v}</span>'
        for p, v in ((0, "00:00"), (20, "00:20"), (40, "00:40"), (60, "01:00"), (80, "01:20")))
    return f"""
<div class="hero">
  <div class="wrap">
    <div class="hero-top">
      <div class="hero-text">
        <p class="eyebrow hero-anim d1">{t("hero.eyebrow")}</p>
        <div class="headline hero-anim d2">{headline(t.fallback, t)}</div>
        <p class="lede hero-anim d3">{t("hero.lede")}</p>
        <div class="cta hero-anim d4">
          <a class="btn" href="#edit">{t("hero.cta_secondary")}</a>
        </div>
      </div>
      <div class="hero-dl hero-anim d4">{download_panel(struct, t)}</div>
    </div>
  </div>
  <div class="wrap hero-anim d5">
    <div class="ruler" aria-hidden="true">
      <div class="ruler-ticks"></div>{ticks}<div class="playhead"></div>
    </div>
    <div class="stage">
      <div class="stage-inner">
        <div class="stage-shot">
          <img src="{hero_src}" width="{hero_w}"
               height="{hero_h}" alt="{attr(strip_tags(t("hero.shot_alt")))}"
               fetchpriority="high" decoding="async">
        </div>
        <div class="inset" aria-hidden="true">
          <img src="{inset_src}" width="{inset_w}"
               height="{inset_h}" alt="" loading="lazy" decoding="async">
        </div>
      </div>
    </div>
  </div>
  <div class="wrap"><div class="stats">{stats}</div></div>
</div>"""


def cards(sec, t):
    return "".join(
        f'<div class="cell rise"><h3>{t(f"{sec["id"]}.{i}_title")}</h3>'
        f'<p>{t(f"{sec["id"]}.{i}_body")}</p></div>' for i in sec["items"])


def item_list(sec_id, ids, t):
    rows = "".join(f'<li><b>{t(f"{sec_id}.{i}_title")}</b>'
                   f'<span>{t(f"{sec_id}.{i}_body")}</span></li>' for i in ids)
    return f'<ul class="list">{rows}</ul>'


def c_cards(sec, struct, t, ctx):
    cls = "g4" if sec.get("cols", 4) == 4 else "g3"
    return (f'<section class="{section_class(sec)}" id="{sec["id"]}"><div class="wrap">'
            f'{head_block(sec, t)}{standfirst(sec, t)}'
            f'<div class="grid {cls}">{cards(sec, t)}</div></div></section>')


def c_shot_then_lists(sec, struct, t, ctx):
    body = (f'{shot(struct, sec["shot"], t, sec["id"], cap_key=sec["id"] + ".shot_cap", klass="rise")}'
            f'<div class="split" style="margin-top:48px">'
            f'{item_list(sec["id"], sec["left"], t)}'
            f'{item_list(sec["id"], sec["right"], t)}</div>')
    return wrap_section(sec, t, body)


def c_list_and_shot(sec, struct, t, ctx):
    body = (f'<div class="split">{item_list(sec["id"], sec["items"], t)}'
            f'<div>{shot(struct, sec["shot"], t, sec["id"], cap_key=sec["id"] + ".shot_cap")}</div></div>')
    return wrap_section(sec, t, body)


def c_shot_and_list(sec, struct, t, ctx):
    body = (f'<div class="split split-rev">'
            f'<div>{shot(struct, sec["shot"], t, sec["id"], cap_key=sec["id"] + ".shot_cap")}</div>'
            f'{item_list(sec["id"], sec["items"], t)}</div>')
    return wrap_section(sec, t, body)


def c_list_and_shots(sec, struct, t, ctx):
    shots = (shot(struct, sec["shot"], t, sec["id"])
             + shot(struct, sec["shot2"], t, sec["id"], alt_key=sec["id"] + ".shot2_alt")
             + f'<p class="cap" style="margin-top:-10px">{t(sec["id"] + ".cap")}</p>')
    body = (f'<div class="split">{item_list(sec["id"], sec["items"], t)}'
            f'<div class="stack">{shots}</div></div>')
    return wrap_section(sec, t, body)


def c_effects(sec, struct, t, ctx):
    tiles = "".join(f'<div><h3>{attr(name)}</h3></div>' for name in struct["fx"]["names"])
    audio = "".join(f'<li><b>{t(f"{sec["id"]}.{i}_title")}</b>'
                    f'<span>{t(f"{sec["id"]}.{i}_body")}</span></li>' for i in sec["audio"])
    body = f"""<div class="fx rise">{tiles}</div>
  <p class="cap">{t(sec["id"] + ".fx_cap")}</p>
  <div class="split split-rev" style="margin-top:60px">
    <div>{shot(struct, sec["shot"], t, sec["id"])}</div>
    <div>
      <h3 class="sub">{t(sec["id"] + ".audio_title")}</h3>
      <ul class="list">{audio}</ul>
      <p style="color:var(--muted); font-size:15.5px; margin-top:24px">{t(sec["id"] + ".note")}</p>
      <div style="margin-top:28px">{shot(struct, sec["shot2"], t, sec["id"],
            alt_key=sec["id"] + ".shot2_alt", cap_key=sec["id"] + ".shot2_cap")}</div>
    </div>
  </div>"""
    return wrap_section(sec, t, body)


def c_roadmap(sec, struct, t, ctx):
    nxt = "".join(f'<li>{t("roadmap.n_" + i)}</li>' for i in sec["next"])
    # The version IS the label: v26.10.24 is shown once, as 26:10:24.
    log = "".join(
        f'<li><span class="tc" title="v{v}">{v.replace(".", ":")}</span>'
        f'<p>{t("roadmap.v" + v.replace(".", ""))}</p></li>'
        for v in sec["versions"])
    body = f"""<div class="road">
    <div class="road-now rise"><h3>{t("roadmap.shipped_title")}</h3><ol class="road-log">{log}</ol></div>
    <div class="road-next rise"><h3>{t("roadmap.next_title")}</h3><ul>{nxt}</ul></div>
  </div>"""
    return wrap_section(sec, t, body)


def c_install(sec, struct, t, ctx):
    lines = []
    for line in struct["install"]["lines"]:
        if line.get("blank"):
            lines.append("")
        elif "comment" in line:
            lines.append(f'<span class="c"># {t("get." + line["comment"])}</span>')
        else:
            lines.append(attr(line["cmd"]))
    reqs = "".join(f'<dt>{t(f"get.{r}_label")}</dt><dd>{t(f"get.{r}_value")}</dd>'
                   for r in sec["req"])
    body = f"""<div class="split">
    <div>
      <p class="standfirst" style="margin-bottom:28px">{t("get.standfirst")}</p>
<pre>{chr(10).join(lines)}</pre>
      <div class="get-dl">{download_panel(struct, t)}</div>
    </div>
    <dl class="req">{reqs}</dl>
  </div>"""
    return wrap_section(sec, t, body, skip_standfirst=True)


def section_class(sec):
    slab = sec.get("slab", "none")
    return "slab" if slab == "plain" else (f"slab {slab}" if slab != "none" else "")


def wrap_section(sec, t, body, skip_standfirst=False):
    sf = "" if skip_standfirst else standfirst(sec, t)
    cls = section_class(sec)
    return (f'<section class="{cls}" id="{sec["id"]}"><div class="wrap">'
            f'{head_block(sec, t)}{sf}{body}</div></section>')


COMPONENTS = {
    "hero": c_hero, "cards": c_cards, "shot_then_lists": c_shot_then_lists,
    "list_and_shot": c_list_and_shot, "shot_and_list": c_shot_and_list,
    "list_and_shots": c_list_and_shots, "effects": c_effects,
    "roadmap": c_roadmap, "install": c_install,
}

def logo_symbol():
    """The header/footer mark as an inline <symbol id="kt">, made from the same
    assets/kinetren.svg that is the favicon and the editor's icon, so the three
    cannot drift apart."""
    src = ICON.read_text(encoding="utf-8")
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    m = re.search(r"<svg\b[^>]*\bviewBox=\"([^\"]+)\"[^>]*>(.*)</svg>", src, flags=re.S)
    if not m:
        fail(f"{ICON.relative_to(ROOT)}: no <svg viewBox=...> found")
        return ""
    inner = "\n".join(line.strip() for line in m.group(2).splitlines() if line.strip())
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">\n'
            f'<symbol id="kt" viewBox="{m.group(1)}">\n{inner}\n</symbol>\n</svg>')

# Runs in <head>, before the first paint, so the download panel never shows
# both buttons and then drops one: html.os-win / html.os-linux, or nothing for
# any other system (macOS, Android, ChromeOS, iOS), which gets both buttons.
OS_JS = """(function(){
  var n = navigator, p = ((n.userAgentData && n.userAgentData.platform) || n.platform || "") + " " + (n.userAgent || "");
  var c = /Windows|Win32|Win64/i.test(p) ? "os-win"
        : /Linux|X11/i.test(p) && !/Android|CrOS|iPhone|iPad|Mac/i.test(p) ? "os-linux" : "";
  if(c) document.documentElement.classList.add(c);
})();"""

PAGE_JS = """(function(){
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if("IntersectionObserver" in window){
    document.documentElement.classList.add("js");
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } });
    }, {rootMargin:"0px 0px -12% 0px", threshold:0.08});
    var sections = document.querySelectorAll("section");
    sections.forEach(function(s){ io.observe(s); });
    setTimeout(function(){ sections.forEach(function(s){ s.classList.add("in"); }); }, 4000);
  }
  // The hero panel straightens as the page scrolls. Compute only while the
  // hero is on screen and only when the value actually changed: otherwise
  // scrolling the whole page would repaint a large 3D layer for nothing.
  var stage = document.querySelector(".stage-inner");
  if(stage && !reduce){
    var ticking = false, last = -1, visible = true;
    var apply = function(){
      ticking = false;
      if(!visible) return;
      var t = Math.min(1, Math.max(0, window.pageYOffset / 620));
      var e = t * t * (3 - 2 * t);
      var q = Math.round(e * 200);            // ~0.5 % steps, invisible to the eye
      if(q === last) return;
      last = q;
      e = q / 200;
      stage.style.setProperty("--rx", (13 * (1 - e)).toFixed(2) + "deg");
      stage.style.setProperty("--rz", (-0.5 * (1 - e)).toFixed(2) + "deg");
      stage.style.setProperty("--sc", (0.95 + 0.05 * e).toFixed(3));
    };
    if("IntersectionObserver" in window){
      new IntersectionObserver(function(es){
        visible = es[0].isIntersecting;
        if(visible) apply();
      }, {rootMargin:"200px"}).observe(stage);
    }
    addEventListener("scroll", function(){ if(!ticking){ ticking = true; requestAnimationFrame(apply); } }, {passive:true});
    apply();
  }
  // [data-clock]: the section timecode shows the visitor's current time.
  // One text update per second, nothing else redrawn.
  var clocks = document.querySelectorAll("[data-clock]");
  if(clocks.length){
    var pad = function(n){ return (n < 10 ? "0" : "") + n; };
    var tick = function(){
      var d = new Date(), v = pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
      for(var i = 0; i < clocks.length; i++) clocks[i].textContent = v;
    };
    tick();
    setInterval(tick, 1000);
  }
  document.querySelectorAll(".lang a").forEach(function(a){
    a.addEventListener("click", function(){
      try { localStorage.setItem("lang", a.getAttribute("data-lang")); } catch(e) {}
    });
  });
  // The hero headline shows its lines in turn: only while the hero is on
  // screen and the tab is visible, never with reduced motion.
  var hl = document.querySelectorAll(".headline .hl"), hero = document.querySelector(".hero");
  if(hl.length > 1 && hero && !reduce && "IntersectionObserver" in window){
    var cur = 0, timer = null, onScreen = true;
    var step = function(){
      hl[cur].classList.remove("on");
      cur = (cur + 1) % hl.length;
      hl[cur].classList.add("on");
    };
    var sync = function(){
      var run = onScreen && !document.hidden;
      if(run && !timer) timer = setInterval(step, 5000);
      else if(!run && timer){ clearInterval(timer); timer = null; }
    };
    new IntersectionObserver(function(es){ onScreen = es[0].isIntersecting; sync(); }).observe(hero);
    document.addEventListener("visibilitychange", sync);
  }
  // Download buttons: the latest release's own files instead of its page.
  // One request per page view, its answer kept for an hour of the session;
  // on any failure the buttons keep the release-page link.
  var DL = __DL__;
  if(document.querySelector("[data-dl]") && window.fetch){
    var mb = function(b){ var m = b / 1048576; return (m < 100 ? m.toFixed(1) : Math.round(m)) + " MB"; };
    var put = function(r){
      Object.keys(DL.files).forEach(function(os){
        var f = r[os];
        if(!f) return;
        document.querySelectorAll('[data-dl="' + os + '"]').forEach(function(a){ a.href = f.url; });
        document.querySelectorAll('[data-dl-label="' + os + '"]').forEach(function(s){ s.textContent = r.tag + " · " + mb(f.size); });
      });
    };
    var cached = null;
    try { cached = JSON.parse(sessionStorage.getItem("kt-release")); } catch(e) {}
    if(cached && Date.now() - cached.at < 3600000){
      put(cached);
    } else {
      var ctl = window.AbortController ? new AbortController() : null;
      var limit = ctl && setTimeout(function(){ ctl.abort(); }, 5000);
      fetch(DL.api, ctl ? {signal: ctl.signal} : {}).then(function(res){
        if(!res.ok) throw new Error(res.status);
        return res.json();
      }).then(function(j){
        if(typeof j.tag_name !== "string") return;
        var r = {tag: j.tag_name, at: Date.now()};
        (j.assets || []).forEach(function(a){
          Object.keys(DL.files).forEach(function(os){
            var suf = DL.files[os], url = String(a.browser_download_url || "");
            if(String(a.name).slice(-suf.length) === suf && url.indexOf("https://github.com/") === 0)
              r[os] = {url: url, size: +a.size || 0};
          });
        });
        try { sessionStorage.setItem("kt-release", JSON.stringify(r)); } catch(e) {}
        put(r);
      }).catch(function(){}).then(function(){ if(limit) clearTimeout(limit); });
    }
  }
})();"""


def page_js(struct):
    cfg = {"api": struct["site"]["release_api"], "files": struct["download"]}
    return PAGE_JS.replace("__DL__", json.dumps(cfg))


# The source and community links: monochrome icons set apart from the page
# menu (owner, 2026-10-26); the full name is the tooltip and the accessible
# name. Paths: Simple Icons (CC0), 24×24, drawn in currentColor.
SOCIAL_ICONS = {
    "github": ("GitHub", "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258"
               ".82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 "
               "17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 "
               "1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 "
               "0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 "
               "1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 "
               "2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 "
               "2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 "
               "12.297c0-6.627-5.373-12-12-12"),
    "discord": ("Discord", "M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375"
                "-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 "
                "0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58"
                ".099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028"
                " 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892"
                ".077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 "
                "8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006"
                ".127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993"
                "a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177"
                "-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157"
                "-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418"
                "-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 "
                "1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"),
    "youtube": ("YouTube", "M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s"
                "-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016"
                " 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 "
                "0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12"
                "l-6.273 3.568z"),
}


def social_links(struct):
    links = "".join(
        f'<a href="{attr(struct["site"][key])}" title="{name}" aria-label="{name}">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg></a>'
        for key, (name, path) in SOCIAL_ICONS.items())
    return f'<nav class="mast-social" aria-label="GitHub, Discord, YouTube">{links}</nav>'


def lang_switcher(code, langs, cats, en, page_of):
    items = []
    for other in langs:
        label = cats.get(other, en).get(f"lang.{lang_key(other)}", other)
        cur = ' aria-current="true"' if other == code else ""
        items.append(f'<li><a href="{page_of(other)}" hreflang="{other}" lang="{other}" '
                     f'data-lang="{other}"{cur}>{esc(label)}</a></li>')
    current = cats.get(code, en).get(f"lang.{lang_key(code)}", code)
    return (f'<details class="lang"><summary>{esc(current)}</summary>'
            f'<ul>{"".join(items)}</ul></details>')


def lang_key(code):
    """zh-Hans -> zh: a TOML section name cannot contain a hyphen."""
    return code.split("-")[0]


def build_page(code, struct, cats, coverage, base, css_href, indexable):
    en = cats["en"]
    t = Cat(cats[code], en)
    langs = struct["site"]["langs"]
    rtl = code in struct["site"]["rtl"]
    body = []
    for sec in struct["section"]:
        body.append(COMPONENTS[sec["component"]](sec, struct, t, code))

    nav = "".join(f'<a href="#{i}">{t("site.nav_" + i)}</a>'
                  for i in ("edit", "effects", "morpher", "export", "roadmap"))
    nav += f'<a href="../docs/">{t("site.nav_docs")}</a><a href="#get">{t("site.nav_get")}</a>'
    switcher = lang_switcher(code, langs, cats, en, lambda c: f"../{c}/")

    alts = "".join(
        f'<link rel="alternate" hreflang="{c}" href="{base}/{c}/">\n  '
        for c in langs if indexable.get(c))
    alts += f'<link rel="alternate" hreflang="x-default" href="{base}/en/">'

    robots = "" if indexable[code] else '<meta name="robots" content="noindex, follow">\n  '
    # The default-language page is not a choice: a visitor who has not picked
    # English in the switcher goes to their system language. Other language
    # URLs are explicit and stay where they are.
    follow = ""
    if code == struct["site"]["default"]:
        follow = ("<script>" + lang_detect_js(struct) +
                  f'\n(function(){{ var c = ktLang(); if(c && c !== "{code}") '
                  'location.replace("../" + c + "/" + location.hash); })();</script>\n  ')
    title = f'kinetren — {strip_tags(t("site.footer_desc"))}'
    desc = strip_tags(t("site.tagline"))

    jsonld = (
        '{"@context":"https://schema.org","@type":"SoftwareApplication",'
        f'"name":"kinetren","applicationCategory":"MultimediaApplication",'
        f'"operatingSystem":"Linux, Windows",'
        f'"inLanguage":"{code}","url":"{base}/{code}/",'
        f'"description":"{attr(desc)}"}}')

    return f"""<!doctype html>
<html lang="{code}"{' dir="rtl"' if rtl else ''}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{attr(title)}</title>
  <meta name="description" content="{attr(desc)}">
  <link rel="canonical" href="{base}/{code}/">
  {alts}
  {robots}{follow}<script>{OS_JS}</script>
  <link rel="icon" href="../assets/kinetren.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{css_href}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{attr(title)}">
  <meta property="og:description" content="{attr(desc)}">
  <meta property="og:url" content="{base}/{code}/">
  <meta property="og:image" content="{base}/assets/og-{code}.jpg">
  <meta property="og:locale" content="{code.replace('-', '_')}">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#why">{t("site.skip")}</a>
{logo_symbol()}
<div class="rail" aria-hidden="true"></div>
<div class="page">
<header class="mast">
  <div class="wrap mast-in">
    <svg class="mark" aria-hidden="true"><use href="#kt"/></svg>
    <span class="mast-name">kinetren</span>
    <nav class="mast-links" aria-label="{attr(strip_tags(t('site.footer_desc')))}">{nav}</nav>
    {social_links(struct)}
    {switcher}
  </div>
</header>
{"".join(body)}
<footer>
  <div class="wrap foot">
    <svg class="mark" aria-hidden="true"><use href="#kt"/></svg>
    <span>kinetren</span><span class="sep">/</span>
    <span>{t("site.footer_desc")}</span><span class="sep">/</span><span>&copy; 2026</span>
    <span class="sep">/</span><a href="{attr(struct["site"]["github"])}">{t("site.source")}</a>
    <span class="sep">/</span><a href="{attr(struct["site"]["discord"])}">Discord</a>
    <span class="sep">/</span><a href="{attr(struct["site"]["youtube"])}">YouTube</a>
    <span class="sep">/</span><a href="../credits.html">{t("site.credits")}</a>
  </div>
</footer>
</div>
<script>{page_js(struct)}</script>
</body>
</html>
"""


def lang_detect_js(struct):
    """JS that defines ktLang(): the language the visitor saved with the
    switcher (localStorage "lang", the key the editor uses too), otherwise
    the first system language we have (navigator.languages, region cut off,
    zh-* to Simplified), otherwise null."""
    langs = struct["site"]["langs"]
    return """function ktLang(){
  var known = %s;
  function pick(tag){
    var base = String(tag||"").split(/[._@]/)[0].split("-")[0].toLowerCase();
    if(base === "zh") return "zh-Hans";
    for(var i=0;i<known.length;i++){ if(known[i].split("-")[0] === base) return known[i]; }
    return null;
  }
  try {
    var saved = localStorage.getItem("lang");
    if(saved && saved !== "auto" && known.indexOf(saved) >= 0) return saved;
  } catch(e) {}
  var list = navigator.languages || [navigator.language];
  for(var i=0;i<list.length;i++){ var c = pick(list[i]); if(c) return c; }
  return null;
}""" % repr(langs).replace("'", '"')


def build_root(struct, cats, base, css_href, indexable):
    """The dispatcher: the same language parsing as the editor's
    src/i18n/detect.rs — cut the region, zh-* goes to Simplified, anything
    unknown to English."""
    langs = struct["site"]["langs"]
    en = cats["en"]
    items = "".join(
        f'<li><a href="{c}/" hreflang="{c}" lang="{c}">'
        f'{esc(en.get(f"lang.{lang_key(c)}", c) if c not in cats else cats[c].get(f"lang.{lang_key(c)}", c))}'
        f'</a></li>' for c in langs)
    # The visible list has all five: a person must reach any language.
    # hreflang has only the indexable ones: pointing a search engine at a
    # noindex page contradicts itself.
    alts = "".join(f'<link rel="alternate" hreflang="{c}" href="{base}/{c}/">\n  '
                   for c in langs if indexable[c])
    js = lang_detect_js(struct) + """
location.replace((ktLang() || "%s") + "/");""" % struct["site"]["default"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kinetren</title>
  <meta name="description" content="{attr(strip_tags(esc(en['site.tagline'])))}">
  <link rel="canonical" href="{base}/">
  {alts}<link rel="alternate" hreflang="x-default" href="{base}/en/">
  <link rel="icon" href="assets/kinetren.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{css_href}">
  <script>{js}</script>
</head>
<body>
<div class="pick"><div class="pick-in">
  {logo_symbol()}
  <svg class="mark" style="width:48px;height:48px;margin:0 auto 20px" aria-hidden="true"><use href="#kt"/></svg>
  <h1>kinetren</h1>
  <p>{esc(en["site.tagline"])}</p>
  <ul>{items}</ul>
</div></div>
</body>
</html>
"""


# ------------------------------------------------------------------ credits --
# The screenshots show excerpts of CC BY films, so the site credits them. The
# list is the editor's own docs/images/CREDITS.md (imported next to the shots),
# rendered as credits.html — never retyped, so it cannot drift from the shots.

# A Markdown link whose URL may itself hold one level of parentheses — Wikimedia
# file names do: File:..._(SVS14839_-_VERTICAL).webm
MD_LINK = r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)"
CREDIT_WORK_RE = re.compile(r"^" + MD_LINK + r"\s*(.*)$")
CREDIT_LICENSE_RE = re.compile(r"^" + MD_LINK + r"$")


def md_inline(text):
    """Escape, then turn [text](url) into links and `code` into <code>."""
    out = esc(text)
    out = re.sub(MD_LINK, lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def load_credits():
    """Rows of the works table and the notes after it, from CREDITS.md.
    A row that does not parse fails the build: a format change upstream must be
    noticed, not silently drop an author."""
    if not CREDITS.is_file():
        fail(f"no assets/shots/CREDITS.md — {IMPORT_HINT}")
        return [], []
    rows, notes_after, in_table, seen_table = [], [], False, False
    for n, line in enumerate(CREDITS.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line.startswith("|"):
            in_table = seen_table = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells[0] in ("Work", "") or set(cells[0]) <= set("-: "):
                continue
            work = CREDIT_WORK_RE.match(cells[0]) if len(cells) == 3 else None
            if not work:
                fail(f"CREDITS.md:{n}: cannot parse table row: {line[:80]}")
                continue
            lic = CREDIT_LICENSE_RE.match(cells[2])
            rows.append({
                "title": work.group(1), "url": work.group(2), "rest": work.group(3),
                "author": cells[1],
                "license": lic.group(1) if lic else cells[2],
                "license_url": lic.group(2) if lic else None,
            })
            continue
        if in_table and line:
            in_table = False
        if seen_table and not in_table and line:
            notes_after.append(line)
    if not rows:
        fail("CREDITS.md: the table lists no works")
    return rows, notes_after


CREDITS_INTRO = ("The screenshots on this site show the kinetren editor at work on "
                 "excerpts of the following free works, edited. The footage itself is "
                 "not distributed with the site.")


def credits_text(rows, notes_after):
    """Everything credits.html prints, for the font subsets."""
    parts = ["Footage credits", "Work Author License", CREDITS_INTRO, *notes_after]
    for r in rows:
        parts += [r["title"], r["rest"], r["author"], r["license"]]
    return " ".join(parts)


def build_credits(rows, notes_after, base, css_href):
    body = "".join(
        f'<tr><td><a href="{attr(r["url"])}">{esc(r["title"])}</a> {esc(r["rest"])}</td>'
        f'<td>{esc(r["author"])}</td><td>'
        + (f'<a href="{attr(r["license_url"])}">{esc(r["license"])}</a>'
           if r["license_url"] else esc(r["license"]))
        + '</td></tr>' for r in rows)
    notes_html = "".join(f"<p>{md_inline(x)}</p>" for x in notes_after)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kinetren — footage credits</title>
  <link rel="canonical" href="{base}/credits.html">
  <link rel="icon" href="assets/kinetren.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{css_href}">
</head>
<body>
{logo_symbol()}
<div class="rail" aria-hidden="true"></div>
<div class="page">
<header class="mast">
  <div class="wrap mast-in">
    <svg class="mark" aria-hidden="true"><use href="#kt"/></svg>
    <a class="mast-name" href="./">kinetren</a>
  </div>
</header>
<main class="wrap credits">
  <h1>Footage credits</h1>
  <p>{esc(CREDITS_INTRO)}</p>
  <table>
    <thead><tr><th>Work</th><th>Author</th><th>License</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
  {notes_html}
</main>
</div>
</body>
</html>
"""


# --------------------------------------------------------------------- lock --
# Imported files are the editor's, byte for byte. upstream.lock holds their
# SHA-256 as of the last `upstream.py import`; a file that differs was edited
# here, and the site would then show something the editor does not have.

def verify_lock():
    if not LOCK.is_file():
        fail(f"no upstream.lock — {IMPORT_HINT}")
        return None
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    listed = set()
    for entry in lock.get("file", []):
        path = ROOT / entry["path"]
        listed.add(path)
        if not path.is_file():
            fail(f"{entry['path']}: listed in upstream.lock but missing — {IMPORT_HINT}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            fail(f"{entry['path']}: differs from upstream.lock — imported files are never "
                 f"edited here; change them in the editor, then {IMPORT_HINT}")
    for folder in (SHOTS, GUIDE):
        for path in sorted(folder.iterdir()) if folder.is_dir() else []:
            if path.is_file() and path not in listed:
                fail(f"{path.relative_to(ROOT)}: not in upstream.lock — files here come only "
                     f"from {IMPORT_HINT}")
    return lock


# -------------------------------------------------------------------- guide --
# The editor's user guide (docs/guide/*.md), rendered in English under /docs/.
# Only the Markdown the guide uses is rendered; anything else fails the build
# with file:line, so a new construct upstream is noticed, never dropped or
# passed through as raw HTML. The text is shown exactly as written.

LIST_RE = re.compile(r"^( *)([-*]|\d+\.) (.*)$")
HEADING_RE = re.compile(r"^(#{1,6}) (.+?)\s*#*\s*$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
IMAGE_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)$")


def gh_slug(text):
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to '-'."""
    return re.sub(r"[^\w\- ]", "", md_plain(text).strip().lower()).replace(" ", "-")


def md_plain(text):
    """Markdown inline text without its markup (titles, descriptions, anchors)."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(MD_LINK, r"\1", text)
    text = re.sub(r"</?kbd>", "", text)
    text = text.replace("**", "").replace("`", "").replace("\\|", "|")
    return re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"\1", text)


def heading_ids(text):
    """Anchor ids of a page's headings in order, with GitHub's -1, -2 for repeats."""
    ids, seen, fence = [], collections.Counter(), False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEADING_RE.match(line)
        if m:
            slug = gh_slug(m.group(2))
            ids.append(slug if not seen[slug] else f"{slug}-{seen[slug]}")
            seen[slug] += 1
    return ids


class GuidePage:
    """Renders one guide page. Links and images are resolved against the
    editor's tree: docs/guide/<stem>.md is where the text lives upstream."""

    def __init__(self, stem, text, anchors, commit):
        self.stem, self.text, self.anchors, self.commit = stem, text, anchors, commit
        self.file = f"assets/guide/{stem}.md"
        self.ids = list(anchors[stem])
        self.title = self.description = None
        self.images = set()

    def err(self, n, msg):
        fail(f"{self.file}:{n}: {msg}")

    def render(self):
        lines = list(enumerate(self.text.splitlines(), 1))
        return self.blocks(lines, depth=0)

    # ---- blocks
    def starts_block(self, line):
        return (line.startswith("```") or HEADING_RE.match(line) or line.startswith("|")
                or IMAGE_LINE_RE.match(line) or (LIST_RE.match(line) and not line.startswith(" ")))

    def blocks(self, lines, depth, tight=False):
        out, i = [], 0
        while i < len(lines):
            n, line = lines[i]
            s = line.strip()
            if not s:
                i += 1
                continue
            if line.startswith("```"):
                j, body = i + 1, []
                while j < len(lines) and not lines[j][1].startswith("```"):
                    body.append(lines[j][1])
                    j += 1
                if j == len(lines):
                    self.err(n, "code fence is not closed")
                out.append(f'<pre><code>{html.escape(chr(10).join(body), quote=False)}</code></pre>')
                i = j + 1
                continue
            m = HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                anchor = self.ids.pop(0) if self.ids else gh_slug(m.group(2))
                if level == 1 and depth == 0 and self.title is None:
                    self.title = md_plain(m.group(2)).strip()
                out.append(f'<h{level} id="{attr(anchor)}">{self.inline(m.group(2), n)}</h{level}>')
                i += 1
                continue
            if line.startswith("|"):
                rows = []
                while i < len(lines) and lines[i][1].startswith("|"):
                    rows.append(lines[i])
                    i += 1
                out.append(self.table(rows))
                continue
            m = IMAGE_LINE_RE.match(line)
            if m:
                out.append(self.figure(m.group(1), m.group(2), n))
                i += 1
                continue
            m = LIST_RE.match(line)
            if m and not m.group(1):
                html_list, i = self.list_block(lines, i, depth)
                out.append(html_list)
                continue
            if s.startswith(">"):
                self.err(n, "block quotes are not rendered")
            elif line.startswith(("    ", "\t")):
                self.err(n, "indented code is not rendered, use a ``` fence")
            elif re.match(r"^(\*{3,}|-{3,}|_{3,}|=+)$", s):
                self.err(n, "thematic breaks and setext headings are not rendered")
            elif s.startswith("<") and not s.startswith("<kbd>"):
                self.err(n, "raw HTML is not rendered (only <kbd>…</kbd> is)")
            elif re.match(r"^\[[^\]]+\]:", s):
                self.err(n, "reference-style link definitions are not rendered")
            para = [(n, s)]
            i += 1
            while i < len(lines) and lines[i][1].strip() and not self.starts_block(lines[i][1]):
                nn, ll = lines[i]
                if re.match(r"^\s*(=+|-+)\s*$", ll):
                    self.err(nn, "setext headings are not rendered, use #")
                para.append((nn, ll.strip()))
                i += 1
            text = " ".join(x for _, x in para)
            body = self.inline(text, n)
            if depth == 0 and self.description is None:
                self.description = " ".join(md_plain(text).split())
            out.append(body if tight else f"<p>{body}</p>")
        return "\n".join(out)

    def list_block(self, lines, i, depth):
        first = LIST_RE.match(lines[i][1])
        ordered = first.group(2)[0].isdigit()
        items = []
        while i < len(lines):
            n, line = lines[i]
            m = LIST_RE.match(line)
            if not m or m.group(1) or m.group(2)[0].isdigit() != ordered:
                break
            indent = len(m.group(2)) + 1
            body, loose = [(n, m.group(3))], False
            i += 1
            while i < len(lines):
                nn, ll = lines[i]
                if not ll.strip():
                    j = i
                    while j < len(lines) and not lines[j][1].strip():
                        j += 1
                    if j < len(lines) and lines[j][1].startswith(" " * indent):
                        body += [(lines[k][0], "") for k in range(i, j)]
                        loose, i = True, j
                        continue
                    break
                if ll.startswith(" " * indent):
                    body.append((nn, ll[indent:]))
                elif ll.startswith(" "):
                    self.err(nn, f"list item text must be indented by {indent} spaces")
                    body.append((nn, ll.strip()))
                else:
                    break
                i += 1
            items.append(f"<li>{self.blocks(body, depth + 1, tight=not loose)}</li>")
            j = i
            while j < len(lines) and not lines[j][1].strip():
                j += 1
            nxt = LIST_RE.match(lines[j][1]) if j < len(lines) else None
            if j != i and nxt and not nxt.group(1) and nxt.group(2)[0].isdigit() == ordered:
                i = j
        tag = "ol" if ordered else "ul"
        start = int(first.group(2)[:-1]) if ordered else 1
        start_attr = f' start="{start}"' if start != 1 else ""
        return f'<{tag}{start_attr}>{"".join(items)}</{tag}>', i

    def table(self, rows):
        def cells(n, line):
            parts = re.split(r"(?<!\\)\|", line.strip())
            if parts and parts[0] == "":
                parts = parts[1:]
            if parts and parts[-1] == "":
                parts = parts[:-1]
            return [p.strip().replace("\\|", "|") for p in parts]
        if len(rows) < 2 or not TABLE_SEP_RE.match(rows[1][1]):
            self.err(rows[0][0], "a table needs a header row and a |---| separator")
            return ""
        head = cells(*rows[0])
        out = ["<thead><tr>" + "".join(f"<th>{self.inline(c, rows[0][0])}</th>" for c in head)
               + "</tr></thead><tbody>"]
        for n, line in rows[2:]:
            row = cells(n, line)
            if len(row) != len(head):
                self.err(n, f"table row has {len(row)} cells, the header {len(head)}")
            out.append("<tr>" + "".join(f"<td>{self.inline(c, n)}</td>" for c in row) + "</tr>")
        return f'<div class="doc-table"><table>{"".join(out)}</tbody></table></div>'

    def figure(self, alt, src, n):
        resolved = posixpath.normpath(posixpath.join("docs/guide", src))
        if posixpath.dirname(resolved) != "docs/images":
            self.err(n, f"image {src} is not in the editor's docs/images/")
            return ""
        name = posixpath.basename(resolved)
        path = SHOTS / name
        if not path.is_file():
            self.err(n, f"image {name} is not in assets/shots/ — {IMPORT_HINT}")
            return ""
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        self.images.add(name)
        return (f'<figure class="doc-shot"><img src="../../assets/shots/{name}" width="{w}" '
                f'height="{h}" alt="{attr(alt)}" loading="lazy" decoding="async"></figure>')

    # ---- inline
    def inline(self, text, n):
        out = []
        for part in re.split(r"(`[^`]+`)", text):
            if len(part) > 1 and part.startswith("`") and part.endswith("`"):
                out.append(f"<code>{html.escape(part[1:-1], quote=False)}</code>")
                continue
            if "`" in part:
                self.err(n, "unpaired backtick")
            # <kbd>…</kbd> is the one inline HTML the guide may use (key caps,
            # drawn like the landing page's). Cut the pairs out first; any "<"
            # left — another tag, an unpaired or nested <kbd> — still fails.
            caps = []
            def cut(m):
                caps.append(m.group(1))
                return f"\x00{len(caps) - 1}\x00"
            part = re.sub(r"<kbd>([^<>`*\x00]+)</kbd>", cut, part)
            if re.search(r"<[A-Za-z/!]", part):
                self.err(n, "raw HTML is not rendered (only <kbd>…</kbd> is)")
            if "![" in part:
                self.err(n, "an image must stand on its own line")
            if re.search(r"\]\[|\[\^", part):
                self.err(n, "reference-style links and footnotes are not rendered")
            if re.search(r"\\[^|]", part):
                self.err(n, "backslash escapes are not rendered")
            if re.search(r"(?<![\w\\])_[^_\s][^_]*_(?!\w)", part):
                self.err(n, "_emphasis_ is not rendered, use *emphasis*")
            s = html.escape(part, quote=False)
            s = re.sub(MD_LINK, lambda m: f'<a href="{attr(self.href(html.unescape(m.group(2)), n))}">'
                                          f'{m.group(1)}</a>', s)
            if "](" in s:
                self.err(n, "a link was not rendered (code inside link text?)")
            s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
            s = re.sub(r"\x00(\d+)\x00",
                       lambda m: f"<kbd>{html.escape(caps[int(m.group(1))], quote=False)}</kbd>", s)
            out.append(s)
        return "".join(out)

    def href(self, target, n):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target):
            return target
        path, _, frag = target.partition("#")
        if not path:
            if frag not in self.anchors[self.stem]:
                self.err(n, f"no heading #{frag} on this page")
            return f"#{frag}"
        resolved = posixpath.normpath(posixpath.join("docs/guide", path))
        if resolved.startswith(".."):
            self.err(n, f"link {target} leaves the editor's repository")
            return target
        if posixpath.dirname(resolved) == "docs/guide" and resolved.endswith(".md"):
            stem = posixpath.basename(resolved)[:-3]
            if stem not in self.anchors:
                self.err(n, f"link {target}: no such guide page")
                return target
            if frag and frag not in self.anchors[stem]:
                self.err(n, f"link {target}: {stem}.md has no heading #{frag}")
            page = "./" if stem == self.stem else f"../{stem}/"
            return page + (f"#{frag}" if frag else "")
        return f"{REPOSITORY}/blob/{self.commit}/{resolved}" + (f"#{frag}" if frag else "")


def load_guide(struct, lock):
    """{stem: GuidePage} rendered, in the order of [docs] pages."""
    order = struct.get("docs", {}).get("pages", [])
    files = {p.stem: p for p in sorted(GUIDE.glob("*.md"))} if GUIDE.is_dir() else {}
    for stem in files:
        if stem not in order:
            fail(f"assets/guide/{stem}.md is not listed in [docs] pages of structure.toml — "
                 "place the new guide page there")
    for stem in order:
        if stem not in files:
            fail(f"[docs] pages lists {stem}, but assets/guide/{stem}.md does not exist")
    if problems:
        return {}
    texts = {stem: files[stem].read_text(encoding="utf-8") for stem in order}
    anchors = {stem: heading_ids(text) for stem, text in texts.items()}
    pages = {}
    for stem in order:
        page = GuidePage(stem, texts[stem], anchors, lock["commit"])
        page.html = page.render()
        if not page.title:
            fail(f"assets/guide/{stem}.md: no # heading to title the page")
        pages[stem] = page
    return pages


GUIDE_TITLE = "User guide"


def guide_intro(lock):
    version = lock.get("tag") or lock["commit"][:10]
    return ("The kinetren user guide, in English. It is the editor's own documentation, "
            f"docs/guide in the source repository, as of {version}.")


def guide_strings(pages, lock):
    """Everything the guide pages print, for the font subsets."""
    # "←" is the crumb arrow drawn by kt.css (.doc-crumb a::before).
    return " ".join([GUIDE_TITLE, guide_intro(lock), "Docs GitHub Source code Footage credits ←",
                     *(p.text for p in pages.values())])


def guide_chrome(prefix, base, css_href, title, desc, canonical, struct, lock, main):
    """A guide page around `main`; prefix leads from the page to dist/."""
    tree = f"{REPOSITORY}/tree/{lock['commit']}/docs/guide"
    version = lock.get("tag") or lock["commit"][:10]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{attr(title)} — kinetren</title>
  <meta name="description" content="{attr(desc)}">
  <link rel="canonical" href="{base}/{canonical}">
  <link rel="icon" href="{prefix}assets/kinetren.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{css_href}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{attr(title)} — kinetren">
  <meta property="og:description" content="{attr(desc)}">
  <meta property="og:url" content="{base}/{canonical}">
  <meta property="og:image" content="{base}/assets/og-en.jpg">
</head>
<body>
{logo_symbol()}
<div class="rail" aria-hidden="true"></div>
<div class="page">
<header class="mast">
  <div class="wrap mast-in">
    <svg class="mark" aria-hidden="true"><use href="#kt"/></svg>
    <a class="mast-name" href="{prefix}">kinetren</a>
    <nav class="mast-links" aria-label="{GUIDE_TITLE}"><a href="{prefix}docs/">Docs</a></nav>
    {social_links(struct)}
  </div>
</header>
<main class="wrap doc">
{main}
</main>
<footer>
  <div class="wrap foot">
    <svg class="mark" aria-hidden="true"><use href="#kt"/></svg>
    <span>kinetren</span><span class="sep">/</span>
    <span>{GUIDE_TITLE}, <a href="{attr(tree)}">docs/guide</a> {attr(version)}</span>
    <span class="sep">/</span><a href="{attr(struct["site"]["github"])}">Source code</a>
    <span class="sep">/</span><a href="{prefix}credits.html">Footage credits</a>
  </div>
</footer>
</div>
</body>
</html>
"""


def build_guide(out_dir, pages, struct, lock, base, css_name):
    docs = out_dir / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for stem, page in pages.items():
        (docs / stem).mkdir(exist_ok=True)
        main = (f'<p class="doc-crumb"><a href="../">{GUIDE_TITLE}</a></p>\n'
                f'<article class="doc-body">\n{page.html}\n</article>')
        (docs / stem / "index.html").write_text(
            guide_chrome("../../", base, f"../../assets/{css_name}", page.title,
                         page.description or page.title, f"docs/{stem}/", struct, lock, main),
            encoding="utf-8")
    items = "".join(
        f'<li><a href="{stem}/">{esc(page.title)}</a>'
        f'<p>{esc(page.description or "")}</p></li>' for stem, page in pages.items())
    main = (f'<h1>{GUIDE_TITLE}</h1>\n<p class="standfirst">{esc(guide_intro(lock))}</p>\n'
            f'<ol class="doc-index">{items}</ol>')
    desc = "The kinetren user guide: " + ", ".join(p.title for p in pages.values()) + "."
    (docs / "index.html").write_text(
        guide_chrome("../", base, f"../assets/{css_name}", GUIDE_TITLE, desc, "docs/",
                     struct, lock, main), encoding="utf-8")


# -------------------------------------------------------------------- fonts --

def collect_chars(cats, struct, extra=""):
    text = [extra]
    for cat in cats.values():
        text.extend(str(v) for v in cat.values())
    text.append("".join(str(v) for v in flatten(struct).values() if isinstance(v, str)))
    text.extend(struct["fx"]["names"])
    for line in struct["install"]["lines"]:
        text.append(str(line.get("cmd", "")))
    for sec in struct["section"]:
        text.extend(str(x) for x in sec.get("stats", []))
    # Ruler timecodes and labels that build.py prints itself, and the release
    # label the page script writes next to a download button ("v26.10.25 · 48.2 MB")
    text.append("kinetren 0123456789:×·—/© v. KMGB")
    chars = {c for c in "".join(text) if ord(c) >= 0x20}
    cjk = {c for c in chars if in_ranges(ord(c), CJK_RANGES)}
    arabic = {c for c in chars if in_ranges(ord(c), AR_RANGES)}
    # Latin is what Ubuntu has; whatever it lacks (arrows, ▸) goes to the
    # symbols face, and what that lacks too fails the build.
    ubuntu = font_cmap(UBUNTU_VAR)
    latin = {c for c in chars - cjk - arabic if ord(c) in ubuntu}
    sym_src, _ = pick_source(SYMBOL_SOURCES)
    symbols_cmap = font_cmap(sym_src) if sym_src else set()
    symbols = {c for c in chars - cjk - arabic - latin if ord(c) in symbols_cmap}
    rest = chars - latin - cjk - arabic - symbols
    if rest:
        fail("characters no font covers: "
             + " ".join(f"U+{ord(c):04X}" for c in sorted(rest)))
    return latin, cjk, arabic, symbols


def font_cmap(path):
    from fontTools.ttLib import TTFont
    if not pathlib.Path(path).exists():
        return set()
    return set(TTFont(path, fontNumber=0).getBestCmap())


def unicodes_arg(chars):
    return "--unicodes=" + ",".join(f"U+{ord(c):04X}" for c in sorted(chars))


def subset(src, index, chars, features, out, *, instance=None):
    """pyftsubset to WOFF. WOFF2 is unavailable: the system has no brotli module."""
    from fontTools import subset as ftsubset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    tmp = None
    source = str(src)
    if instance:
        font = instancer.instantiateVariableFont(TTFont(src), instance, inplace=False,
                                                 updateFontNames=False)
        tmp = out.with_suffix(".tmp.ttf")
        font.save(tmp)
        source = str(tmp)
    cmd = [sys.executable, "-m", "fontTools.subset", source, f"--font-number={index}",
           unicodes_arg(chars), f"--layout-features={features}", "--flavor=woff",
           "--no-hinting", "--drop-tables+=DSIG", "--desubroutinize",
           f"--output-file={out}"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    if tmp and tmp.exists():
        tmp.unlink()
    if res.returncode != 0:
        fail(f"pyftsubset {out.name}: {res.stderr.strip()[:300]}")
        return None
    return out


def pick_source(candidates):
    for path, index in candidates:
        if pathlib.Path(path).exists():
            return pathlib.Path(path), index
    return None, 0


def build_fonts(cats, struct, extra=""):
    latin, cjk, arabic, symbols = collect_chars(cats, struct, extra)
    FONTS_OUT.mkdir(parents=True, exist_ok=True)
    for old in FONTS_OUT.glob("*.woff"):
        old.unlink()
    faces = []          # (css-family, weight, path, unicode-range hint)
    manifest = ["Generated by build.py — do not edit by hand.", ""]

    jobs = [
        ("KT Display", 500, UBUNTU_VAR, 0, latin, "kern,liga", {"wdth": 75, "wght": 500}),
        ("KT Sans", 400, UBUNTU_VAR, 0, latin, "kern,liga", {"wdth": 100, "wght": 400}),
        ("KT Sans", 500, UBUNTU_VAR, 0, latin, "kern,liga", {"wdth": 100, "wght": 500}),
        ("KT Mono", 400, UBUNTU_MONO, 0, latin, "kern,liga", {"wght": 400}),
    ]
    cjk_src, cjk_idx = pick_source(CJK_SOURCES)
    if cjk and cjk_src:
        jobs.append(("KT CJK", 400, cjk_src, cjk_idx, cjk, "", None))
    ar_src, ar_idx = pick_source(AR_SOURCES)
    if arabic and ar_src:
        jobs.append(("KT Arabic", 400, ar_src, ar_idx, arabic, AR_FEATURES, None))
    sym_src, sym_idx = pick_source(SYMBOL_SOURCES)
    if symbols and sym_src:
        jobs.append(("KT Symbols", 400, sym_src, sym_idx, symbols, "kern", None))

    for family, weight, src, index, chars, features, instance in jobs:
        if not src or not pathlib.Path(src).exists():
            fail(f"missing source font {src}")
            continue
        stem = family.lower().replace(" ", "-") + f"-{weight}"
        tmp_out = FONTS_OUT / f"{stem}.woff"
        if not subset(src, index, chars, features, tmp_out, instance=instance):
            continue
        digest = hashlib.sha256(tmp_out.read_bytes()).hexdigest()
        final = FONTS_OUT / f"{stem}.{digest[:8]}.woff"
        tmp_out.rename(final)
        faces.append((family, weight, final.name))
        manifest += [
            final.name,
            f"  family   {family} {weight}",
            f"  source   {src} (face {index}, sha256:{hashlib.sha256(pathlib.Path(src).read_bytes()).hexdigest()[:16]})",
            f"  codepoints {len(chars)}",
            f"  features '{features}'",
            f"  size     {final.stat().st_size} bytes, sha256:{digest[:16]}",
            "",
        ]
    FONT_MANIFEST.write_text("\n".join(manifest), encoding="utf-8")
    css = "\n".join(
        f'@font-face{{font-family:"{fam}";src:url(fonts/{name}) format("woff");'
        f'font-weight:{w};font-style:normal;font-display:swap}}'
        for fam, w, name in faces)
    return css, [FONTS_OUT / n for _, _, n in faces]


# -------------------------------------------------------------------- build --

def make_og(src, dst):
    """The 1200×630 social card, one per language. JPEG, not PNG: the same
    frame as PNG weighed 540 KB and outweighed the rest of the site."""
    from PIL import Image
    hero = Image.open(src).convert("RGB")
    card = Image.new("RGB", (1200, 630), (7, 8, 10))
    scaled = hero.resize((1160, int(1160 * hero.height / hero.width)), Image.LANCZOS)
    card.paste(scaled, (20, (630 - scaled.height) // 2))
    card.save(dst, "JPEG", quality=80, optimize=True, progressive=True)


def build(out_dir, base):
    struct, cats = load_sources()
    if problems:
        return
    lock = verify_lock()
    if problems:
        return
    # Every slot must have its file before anything is written: a missing shot
    # is an error naming the slot, never a page with a hole in it.
    for slot, meta in struct["shot"].items():
        if not (SHOTS / meta["file"]).is_file():
            fail(f"[shot.{slot}]: no file assets/shots/{meta['file']} — {IMPORT_HINT}")
    if problems:
        return
    coverage = validate(cats)
    credit_rows, credit_notes = load_credits()
    guide = load_guide(struct, lock)
    if problems:
        return
    font_css, _ = build_fonts(cats, struct, credits_text(credit_rows, credit_notes)
                              + " " + guide_strings(guide, lock))
    if problems:
        return

    langs = struct["site"]["langs"]
    minimum = struct["site"]["translated_min"]
    indexable = {c: coverage.get(c, 0.0) >= minimum for c in langs}

    assets = out_dir / "assets"
    (assets / "shots").mkdir(parents=True, exist_ok=True)
    (assets / "fonts").mkdir(parents=True, exist_ok=True)

    css = font_css + "\n\n" + (ASSETS / "kt.css").read_text(encoding="utf-8")
    css_name = f"kt.{hashlib.sha256(css.encode()).hexdigest()[:8]}.css"
    (assets / css_name).write_text(css, encoding="utf-8")

    for font in FONTS_OUT.glob("*.woff"):
        shutil.copy2(font, assets / "fonts" / font.name)
    shown = {meta["file"] for meta in struct["shot"].values()}
    shown |= {name for page in guide.values() for name in page.images}
    for name in sorted(shown):
        if (SHOTS / name).is_file():
            shutil.copy2(SHOTS / name, assets / "shots" / name)
    shutil.copy2(ICON, assets / "kinetren.svg")
    # og:image stays per language (og-<lang>.jpg), all made from the shared hero.
    hero_file = SHOTS / struct["shot"]["hero"]["file"]
    if not hero_file.is_file():
        fail(f"[shot.hero]: no file assets/shots/{hero_file.name}")
        return
    for code in langs:
        make_og(hero_file, assets / f"og-{code}.jpg")

    for code in langs:
        page_dir = out_dir / code
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            build_page(code, struct, cats, coverage, base, f"../assets/{css_name}", indexable),
            encoding="utf-8")
    (out_dir / "index.html").write_text(
        build_root(struct, cats, base, f"assets/{css_name}", indexable), encoding="utf-8")
    (out_dir / "credits.html").write_text(
        build_credits(credit_rows, credit_notes, base, f"assets/{css_name}"), encoding="utf-8")
    build_guide(out_dir, guide, struct, lock, base, css_name)

    urls = "".join(f"  <url><loc>{base}/{c}/</loc></url>\n" for c in langs if indexable[c])
    urls += f"  <url><loc>{base}/docs/</loc></url>\n"
    urls += "".join(f"  <url><loc>{base}/docs/{stem}/</loc></url>\n" for stem in guide)
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{base}/</loc></url>\n{urls}</urlset>\n', encoding="utf-8")
    (out_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")

    for code in langs:
        state = "indexed" if indexable[code] else "noindex (translation not ready)"
        notes.append(f"{code}: {coverage.get(code, 0)*100:5.1f}% — {state}")


def tree_digest(root):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE,
                    help=f"site address for canonical/hreflang/sitemap (default {DEFAULT_BASE})")
    ap.add_argument("--check", action="store_true",
                    help="build into a temporary directory and compare with dist/")
    ap.add_argument("--serve", nargs="?", const=8000, type=int, metavar="PORT",
                    help="build and serve dist/ over http (default port 8000). "
                         "View the site THIS way: a viewer that opens one page as a "
                         "file may not serve the neighbouring assets")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "dist"
            build(target, base)
            if problems:
                report()
                return 1
            want, have = tree_digest(target), tree_digest(DIST)
            if want != have:
                only_want = sorted(set(want) - set(have))
                only_have = sorted(set(have) - set(want))
                diff = sorted(k for k in set(want) & set(have) if want[k] != have[k])
                for k in only_want:
                    print(f"missing in dist/: {k}")
                for k in only_have:
                    print(f"extra in dist/: {k}")
                for k in diff:
                    print(f"differs: {k}")
                print("\ndist/ does not match the sources — run build.py")
                return 1
            print(f"ok: dist/ matches the sources ({len(have)} files)")
            return 0

    if DIST.exists():
        shutil.rmtree(DIST)
    build(DIST, base)
    if problems:
        report()
        return 1
    report()
    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"\nbuilt {DIST.relative_to(ROOT)}/ — "
          f"{len(list(DIST.rglob('*')))} entries, {total/1024:.0f} KB, base {base}")

    if args.serve:
        import functools, http.server, socketserver
        handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                    directory=str(DIST))
        with socketserver.TCPServer(("127.0.0.1", args.serve), handler) as srv:
            print(f"\nopen http://127.0.0.1:{args.serve}/ — Ctrl+C to stop")
            try:
                srv.serve_forever()
            except KeyboardInterrupt:
                print("\nstopped")
    return 0


def report():
    for note in notes:
        print(f"  {note}")
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
