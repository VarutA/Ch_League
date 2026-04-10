"""
Seed Diamond (30) + Gold (80) + Silver (146) with overlapping / tricky display names,
all unique across leagues for World Cup. Also writes LeaguePIC_1..50 per team.

Run from repo root:
  python3 Code/seed_complex_name_rosters.py
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from PIL import Image

from World_paths import DIAMOND_PICK, GOLD_PICK, SILVER_PICK, WORLD_CUP_TEAM_TOTAL

CHARACTER_ROOT = os.path.join(_PROJECT_ROOT, "Character")
MASTER_DIAMOND = os.path.join(CHARACTER_ROOT, "Character Diamond")
MASTER_GOLD = os.path.join(CHARACTER_ROOT, "Character Gold")
MASTER_SILVER = os.path.join(CHARACTER_ROOT, "Character Silver")
PICS = os.path.join(CHARACTER_ROOT, "Pic Selection")

IMG_SIZE = 72
NUM_PICS = 50

# Edge-case heavy names (substring / punctuation / spaces / hyphens / short tokens).
CORE_NAMES: list[str] = [
    "Mr. Kid",
    "CC",
    "Mik",
    "Mikle",
    "Arisawa Tatsuki",
    "Tatsuki-1",
    "Arisawa",
    "Sumeragi Lee Noriega",
    "Vivi Vi Ville",
    "Ms. Valentine",
    "Moe-Kamiji",
    "Moda",
    "Miyuki2",
    "Miss Goldenweek",
    "Dr. No",
    "Team",
    "Team B",
    "A-1",
    "A-12",
    "Edge Case",
]


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


def _is_junk(name: str) -> bool:
    return name in ("Thumbs.db", ".DS_Store") or name.startswith(".")


def _clear_master_and_pics(master: str) -> None:
    if not os.path.isdir(master):
        os.makedirs(master, exist_ok=True)
        return
    for name in os.listdir(master):
        if _is_junk(name):
            continue
        p = os.path.join(master, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.isfile(p):
            os.remove(p)
        pic = os.path.join(PICS, name)
        if os.path.isdir(pic):
            shutil.rmtree(pic)


def _build_roster() -> tuple[list[str], list[str], list[str]]:
    if DIAMOND_PICK + GOLD_PICK + SILVER_PICK != WORLD_CUP_TEAM_TOTAL:
        raise RuntimeError("WORLD_CUP_TEAM_TOTAL mismatch with picks")
    seen: set[str] = set()
    ordered: list[str] = []
    for n in CORE_NAMES:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    i = 0
    while len(ordered) < WORLD_CUP_TEAM_TOTAL:
        cand = f"Bench Roster {i}"
        i += 1
        if cand in seen:
            continue
        seen.add(cand)
        ordered.append(cand)
    if len(ordered) != WORLD_CUP_TEAM_TOTAL:
        raise RuntimeError("internal roster size error")
    d = ordered[:DIAMOND_PICK]
    g = ordered[DIAMOND_PICK : DIAMOND_PICK + GOLD_PICK]
    s = ordered[DIAMOND_PICK + GOLD_PICK :]
    return d, g, s


def _seed_league(names: list[str], master: str) -> None:
    os.makedirs(master, exist_ok=True)
    os.makedirs(PICS, exist_ok=True)
    for name in names:
        os.makedirs(os.path.join(master, name), exist_ok=True)
        pic_dir = os.path.join(PICS, name)
        os.makedirs(pic_dir, exist_ok=True)
        for j in range(1, NUM_PICS + 1):
            _write_league_pic(os.path.join(pic_dir, f"LeaguePIC_{j}.jpg"), name, j)


def main() -> None:
    p = argparse.ArgumentParser(description="Seed D/G/S rosters with complex display names.")
    p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Required to confirm wiping Character Diamond/Gold/Silver + Pic folders for those names",
    )
    ns = p.parse_args()
    if not ns.yes:
        print(
            "This deletes existing Character Diamond, Gold, Silver (dirs) and matching Pic Selection.\n"
            "Re-run with: python3 Code/seed_complex_name_rosters.py -y"
        )
        sys.exit(1)

    d, g, s = _build_roster()
    for m in (MASTER_DIAMOND, MASTER_GOLD, MASTER_SILVER):
        _clear_master_and_pics(m)
    _seed_league(d, MASTER_DIAMOND)
    _seed_league(g, MASTER_GOLD)
    _seed_league(s, MASTER_SILVER)

    print(
        f"Seeded Diamond={len(d)}, Gold={len(g)}, Silver={len(s)} "
        f"(total {len(d) + len(g) + len(s)} == {WORLD_CUP_TEAM_TOTAL})."
    )
    print("Sample names:", ", ".join(CORE_NAMES[:6]), "...")


if __name__ == "__main__":
    main()
