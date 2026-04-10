"""
Rename unplayed Diamond fixture folders (contain ' VS ') to scored names, like match.py:
  "3. A VS B" -> "3. A 2-1 B"

Usage:
  python3 Code/simulate_diamond_scores.py 3
  python3 Code/simulate_diamond_scores.py 3 --seed 42
"""
from __future__ import annotations

import argparse
import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Diamond_paths import LEAGUE_DIAMOND_FIXTURE
from fixture_vs_sim import simulate_vs_in_folder


def simulate_week(week: int, seed: int | None = None) -> int:
    week_path = os.path.join(LEAGUE_DIAMOND_FIXTURE, f"week {week}")
    if not os.path.isdir(week_path):
        raise FileNotFoundError(week_path)
    return simulate_vs_in_folder(week_path, seed=seed)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("week", type=int, help="Week number (e.g. 3)")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()
    count = simulate_week(args.week, seed=args.seed)
    print(f"Renamed {count} match(es) in week {args.week}.")


if __name__ == "__main__":
    main()
