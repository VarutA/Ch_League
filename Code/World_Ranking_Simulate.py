"""
Build World Ranking at project root (sibling of World Cup/), folder World Ranking/.

Reads character folders from:
- Character/Character Diamond
- Character/Character Gold
- Character/Character Silver

Creates one folder per character named:
  "N. <name> [<point>]"
where N is rank 1..total after a random shuffle of names, and <point> is a random integer.

Run:
  python3 Code/World_Ranking_Simulate.py
  python3 Code/World_Ranking_Simulate.py -y
  python3 Code/World_Ranking_Simulate.py -y --seed 42
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Diamond_paths import CHARACTER_DIAMOND_MASTER
from Gold_paths import CHARACTER_GOLD_MASTER
from Silver_paths import CHARACTER_SILVER_MASTER
from World_paths import WORLD_RANKING


class WorldRankingCancelled(Exception):
    """User declined replacing existing World Ranking."""


def _listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store") or name.startswith("."):
            continue
        out.append(name)
    return out


def _team_dirs(master_root: str) -> list[str]:
    if not os.path.isdir(master_root):
        return []
    names = []
    for n in _listdir_skip_junk(master_root):
        p = os.path.join(master_root, n)
        if os.path.isdir(p):
            names.append(n)
    return names


def _collect_all_characters() -> list[str]:
    d = _team_dirs(CHARACTER_DIAMOND_MASTER)
    g = _team_dirs(CHARACTER_GOLD_MASTER)
    s = _team_dirs(CHARACTER_SILVER_MASTER)
    all_names = d + g + s
    if not all_names:
        raise ValueError(
            "No character folders found under Character Diamond / Gold / Silver masters."
        )
    if len(set(all_names)) != len(all_names):
        raise ValueError("Duplicate character name across Diamond/Gold/Silver masters.")
    return all_names


def _ranking_has_data() -> bool:
    return os.path.isdir(WORLD_RANKING) and bool(_listdir_skip_junk(WORLD_RANKING))


def _confirm_replace(force: bool) -> None:
    if not _ranking_has_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "World Ranking already has data; refusing to replace without confirmation. "
            "Use a terminal prompt or pass -y."
        )
    print(
        f"World Ranking already exists at:\n  {WORLD_RANKING}\n"
        "This will DELETE it and rebuild from all master characters."
    )
    ans = input("Replace World Ranking? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise WorldRankingCancelled("Cancelled; existing World Ranking kept.")


def simulate_world_ranking(force: bool = False, seed: int | None = None) -> int:
    """
    Randomize order of all characters, assign random points, write folder names
    "N. name [point]" under WORLD_RANKING.

    Returns number of entries created.
    """
    if seed is not None:
        random.seed(seed)

    _confirm_replace(force=force)
    names = _collect_all_characters()
    random.shuffle(names)

    if os.path.isdir(WORLD_RANKING):
        shutil.rmtree(WORLD_RANKING)
    os.makedirs(WORLD_RANKING, exist_ok=True)

    for rank, name in enumerate(names, start=1):
        point = random.randint(0, 9999)
        folder = f"{rank}. {name} [{point}]"
        os.makedirs(os.path.join(WORLD_RANKING, folder), exist_ok=True)

    print(
        f"World Ranking: created {len(names)} entries under {WORLD_RANKING!r} "
        f"(random order + random points 0..9999)."
    )
    return len(names)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Simulate World Ranking from all master characters.")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when World Ranking already exists",
    )
    ap.add_argument("--seed", type=int, default=None, help="Optional RNG seed (reproducible run)")
    ns = ap.parse_args()
    try:
        simulate_world_ranking(force=ns.yes, seed=ns.seed)
    except WorldRankingCancelled as e:
        print(e)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
