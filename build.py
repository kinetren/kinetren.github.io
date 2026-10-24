#!/usr/bin/env python3
"""Build the kinetren landing page from formal sources.

Introduced in round R.19 on three requests from the owner: generate the landing
page from something formal, stop shipping one fat HTML blob, and go
multilingual with the language in the path for SEO. Before that, index.html
was a hand-written 446 KB file, 89 % of it base64, one image embedded twice.

Inputs:
    content/structure.toml   page form: section order, components, images,
                             key chords, effect names, numbers
    content/<lang>.toml      prose only; en.toml is the reference for the key
                             set and order, exactly like the editor's i18n/en.toml
    assets/kt.css            styles (a source, not generated)
    assets/shots/*.webp      screenshots, one set for every language, from the
                             editor's docs/images/: import-shots.py --from <kinetren>
    assets/shots/CREDITS.md  authors and licenses of the footage -> credits.html
    assets/kinetren.svg      the icon (= the editor's src/packaging/kinetren.svg)
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
import hashlib
import html
import os
import pathlib
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

DEFAULT_BASE = "https://kinetren.github.io"

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
    are the editor's own showcase shots, imported by import-shots.py. A slot
    whose file is missing is a build error, not a silent fallback.

    Returns (src, w, h) or None. The size is read from the image itself: the
    editor's pipeline crops by probe rectangles, so the size is data."""
    path = SHOTS / file
    if not path.is_file():
        fail(f"[shot.{slot}]: no file assets/shots/{file} — "
             f"python3 import-shots.py --from <kinetren checkout>")
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
    <p class="eyebrow hero-anim d1">{t("hero.eyebrow")}</p>
    <h1 class="hero-anim d2">{t("hero.h1")}</h1>
    <p class="lede hero-anim d3">{t("hero.lede")}</p>
    <div class="cta hero-anim d4">
      <a class="btn btn-primary" href="#get">{t("hero.cta_primary")}</a>
      <a class="btn" href="#edit">{t("hero.cta_secondary")}</a>
      <span class="cta-note">{t("hero.cta_note")}</span>
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


def c_keys(sec, struct, t, ctx):
    out = []
    for group in sec["groups"]:
        out.append(f'<h3>{t(f"keys.g_{group}")}</h3>')
        for row in struct["keys"][group]["rows"]:
            chords = "".join(
                f'<i>{attr(k)}</i>' if k == "+" else f'<kbd>{attr(k)}</kbd>'
                for k in row["keys"])
            out.append(f'<div><span class="k">{chords}</span>'
                       f'<span class="a">{t(f"keys.{group}_{row["id"]}")}</span></div>')
    return wrap_section(sec, t, f'<div class="keys">{"".join(out)}</div>')


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
      <div class="cta" style="margin-top:32px">
        <a class="btn btn-primary" href="{attr(struct["site"]["releases"])}">{t("get.cta")}</a>
        <span class="cta-note">{t("get.cta_note")}</span>
      </div>
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
    "list_and_shots": c_list_and_shots, "effects": c_effects, "keys": c_keys,
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
})();"""


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
                  for i in ("edit", "effects", "morpher", "export", "roadmap", "get"))
    nav += (f'<a href="{attr(struct["site"]["github"])}">GitHub</a>'
            f'<a href="{attr(struct["site"]["discord"])}">Discord</a>')
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
  {robots}{follow}<link rel="icon" href="../assets/kinetren.svg" type="image/svg+xml">
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
    <span class="sep">/</span><a href="../credits.html">{t("site.credits")}</a>
  </div>
</footer>
</div>
<script>{PAGE_JS}</script>
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
        fail("no assets/shots/CREDITS.md — python3 import-shots.py --from <kinetren checkout>")
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


# -------------------------------------------------------------------- fonts --

def collect_chars(cats, struct, extra=""):
    text = [extra]
    for cat in cats.values():
        text.extend(str(v) for v in cat.values())
    text.append("".join(str(v) for v in flatten(struct).values() if isinstance(v, str)))
    text.extend(struct["fx"]["names"])
    for group in struct["keys"].values():
        for row in group["rows"]:
            text.extend(row["keys"])
    for line in struct["install"]["lines"]:
        text.append(str(line.get("cmd", "")))
    for sec in struct["section"]:
        text.extend(str(x) for x in sec.get("stats", []))
    # Ruler timecodes and labels that build.py prints itself
    text.append("kinetren 0123456789:×·—/©")
    chars = set("".join(text))
    latin = {c for c in chars if ord(c) < 0x0500 or 0x2000 <= ord(c) <= 0x22FF}
    cjk = {c for c in chars if in_ranges(ord(c), CJK_RANGES)}
    arabic = {c for c in chars if in_ranges(ord(c), AR_RANGES)}
    rest = chars - latin - cjk - arabic
    if rest:
        fail("characters outside the known ranges, no font covers them: "
             + " ".join(f"U+{ord(c):04X}" for c in sorted(rest)))
    return latin, cjk, arabic


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
    latin, cjk, arabic = collect_chars(cats, struct, extra)
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
    # Every slot must have its file before anything is written: a missing shot
    # is an error naming the slot, never a page with a hole in it.
    for slot, meta in struct["shot"].items():
        if not (SHOTS / meta["file"]).is_file():
            fail(f"[shot.{slot}]: no file assets/shots/{meta['file']} — "
                 f"python3 import-shots.py --from <kinetren checkout>")
    if problems:
        return
    coverage = validate(cats)
    credit_rows, credit_notes = load_credits()
    if problems:
        return
    font_css, _ = build_fonts(cats, struct, credits_text(credit_rows, credit_notes))
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
    for slot, meta in sorted(struct["shot"].items()):
        if (SHOTS / meta["file"]).is_file():
            shutil.copy2(SHOTS / meta["file"], assets / "shots" / meta["file"])
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

    urls = "".join(f"  <url><loc>{base}/{c}/</loc></url>\n" for c in langs if indexable[c])
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
