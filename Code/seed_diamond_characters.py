"""
One-off / repeatable seed: 30 random roster folders under Character/Character Diamond
and LeaguePIC_1..50 small JPEGs under Character/Pic Selection/<name>/.

Run from anywhere:
  python3 Code/seed_diamond_characters.py
  python3 Code/seed_diamond_characters.py --keep-templates   # do not delete ${...} folders
"""
from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from PIL import Image

CHARACTER_ROOT = os.path.join(_PROJECT_ROOT, "Character")
MASTER = os.path.join(CHARACTER_ROOT, "Character Diamond")
PICS = os.path.join(CHARACTER_ROOT, "Pic Selection")

IMG_SIZE = 72
NUM_PICS = 50
NUM_CHARS = 30


def _rgb_for(name: str, index: int) -> tuple[int, int, int]:
    h = hashlib.sha256(f"{name}:{index}".encode()).digest()
    return h[0], h[1], h[2]


def _write_league_pic(out_path: str, name: str, index: int) -> None:
    r, g, b = _rgb_for(name, index)
    band = max(24, min(index * 2 % 200, 200))
    img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (r, g, b))
    px = img.load()
    for x in range(IMG_SIZE):
        px[x, x % IMG_SIZE] = (band, (g + x) % 256, (b + x) % 256)
        px[(x * 3) % IMG_SIZE, x] = ((r + band) % 256, band, x % 256)
    img.save(out_path, "JPEG", quality=82, optimize=True)


def _is_junk_entry(name: str) -> bool:
    return name in (".DS_Store", "Thumbs.db") or name.startswith(".")


def _clear_targets(keep_templates: bool) -> None:
    for base in (MASTER, PICS):
        if not os.path.isdir(base):
            os.makedirs(base, exist_ok=True)
            continue
        for name in os.listdir(base):
            if _is_junk_entry(name):
                continue
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                continue
            if keep_templates and name.startswith("${"):
                continue
            shutil.rmtree(path)


def _unique_names(n: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    while len(out) < n:
        token = secrets.token_hex(3).upper()
        name = f"D_{token}"
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-templates",
        action="store_true",
        help="Keep folders whose names start with ${ (template placeholders).",
    )
    args = parser.parse_args()

    _clear_targets(keep_templates=args.keep_templates)

    names = _unique_names(NUM_CHARS)
    for name in names:
        os.makedirs(os.path.join(MASTER, name), exist_ok=True)
        pic_dir = os.path.join(PICS, name)
        os.makedirs(pic_dir, exist_ok=True)
        for i in range(1, NUM_PICS + 1):
            out = os.path.join(pic_dir, f"LeaguePIC_{i}.jpg")
            _write_league_pic(out, name, i)

    print(f"Created {NUM_CHARS} characters under:\n  {MASTER}\n  {PICS}")
    for name in names:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
