#!/usr/bin/env python3
"""Import the screenshots, the icon and the footage credits from a kinetren checkout.

The screenshots are not taken here. The editor's own pipeline
(`src/scripts/readme-shots.py` in github.com/kinetren/kinetren) shoots them on free
footage and publishes them in `docs/images/`; this script copies the ones the site
declares in `content/structure.toml` ([shot.*] file = ...), byte for byte, so their
provenance stays checkable.

    python3 import-shots.py --from ../kinetren

Copies:
    <checkout>/docs/images/<file>          -> assets/shots/<file>   (every declared slot)
    <checkout>/docs/images/CREDITS.md      -> assets/shots/CREDITS.md
    <checkout>/src/packaging/kinetren.svg  -> assets/kinetren.svg
and deletes images in assets/shots/ that no slot declares. Every source is checked
first: if one is missing, nothing is changed. Rebuild afterwards: python3 build.py
"""

import argparse
import pathlib
import shutil
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
SHOTS = ROOT / "assets" / "shots"
ICON = ROOT / "assets" / "kinetren.svg"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="checkout", required=True, metavar="CHECKOUT",
                    help="path to a kinetren checkout (the repository root)")
    args = ap.parse_args()
    checkout = pathlib.Path(args.checkout).resolve()
    images = checkout / "docs" / "images"

    structure = tomllib.loads((ROOT / "content" / "structure.toml").read_text(encoding="utf-8"))
    declared = {slot: meta["file"] for slot, meta in structure["shot"].items()}

    copies = [(images / f, SHOTS / f) for f in sorted(set(declared.values()))]
    copies.append((images / "CREDITS.md", SHOTS / "CREDITS.md"))
    copies.append((checkout / "src" / "packaging" / "kinetren.svg", ICON))

    missing = [str(src) for src, _ in copies if not src.is_file()]
    if missing:
        for path in missing:
            print(f"missing in the checkout: {path}", file=sys.stderr)
        print("nothing changed", file=sys.stderr)
        return 1

    SHOTS.mkdir(parents=True, exist_ok=True)
    for src, dst in copies:
        shutil.copyfile(src, dst)
        print(f"{dst.relative_to(ROOT)}  <-  {src.relative_to(checkout)}")

    keep = set(declared.values())
    for old in sorted(SHOTS.glob("*.webp")):
        if old.name not in keep:
            old.unlink()
            print(f"removed {old.relative_to(ROOT)} (no slot declares it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
