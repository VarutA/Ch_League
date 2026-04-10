"""
World Cup knockout: create Round 1 (256 teams, 128 matches).

1) Snapshot-copy Diamond League Standing, Gold Rank Summary, Silver League Standing,
   and project-root World Ranking -> World Cup Source/World Ranking Pre-Tournament.
2) Select 256 teams: Diamond ranks 1-30, Gold summary 1-80, Silver ranks 1-146.
3) Copy those teams into World Cup/World Cup Character.
4) Random draw pairings across all leagues (full shuffle), then create Round 1 fixture.
"""
from __future__ import annotations

import os
import random
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from World_Cup_lib import (
    CreateWorldCupCancelled,
    collect_world_cup_teams,
    confirm_replace_world_cup,
    copy_source_snapshots,
    copy_world_cup_characters,
    prepare_fresh_fixture_root,
    world_round_path,
    write_pair_match,
)


def create_world_cup_round1(force: bool = False) -> None:
    confirm_replace_world_cup(force=force)

    diamond_teams, gold_teams, silver_teams = collect_world_cup_teams()
    teams = diamond_teams + gold_teams + silver_teams

    copy_source_snapshots()
    copy_world_cup_characters(teams)
    prepare_fresh_fixture_root()

    random.shuffle(teams)
    used: dict[str, set[int]] = {}
    r1 = world_round_path(1)
    os.makedirs(r1, exist_ok=True)

    n_matches = len(teams) // 2
    for i in range(n_matches):
        write_pair_match(i + 1, teams[2 * i], teams[2 * i + 1], r1, used)
        if (i + 1) % 32 == 0:
            print(f"World Cup Round 1: created matches 1..{i + 1} / {n_matches}")

    print(
        f"World Cup Round 1 created: {n_matches} matches under {r1!r}\n"
        f"  Diamond picks: {len(diamond_teams)}, Gold: {len(gold_teams)}, Silver: {len(silver_teams)}"
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Create World Cup knockout Round 1 (256 teams).")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when World Cup folder already has data",
    )
    ns = ap.parse_args()
    try:
        create_world_cup_round1(force=ns.yes)
    except CreateWorldCupCancelled as e:
        print(e)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
