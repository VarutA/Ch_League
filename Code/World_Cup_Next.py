"""
World Cup knockout: auto-create the next round until Final (Round 8).

Requires World_Cup_Create Round 1 first. Each prior round must be fully scored
(no ' VS ' in folder names). Pairings among winners are randomized each round.
"""
from __future__ import annotations

import os
import random
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from World_paths import WORLD_CUP_TEAM_TOTAL
from World_Cup_lib import (
    collect_used_world_pic_indices,
    listdir_skip_junk,
    round_has_matches,
    round_is_complete,
    winners_from_completed_round,
    world_round_path,
    write_pair_match,
)


def _build_round_from_winners(target_round: int, prev_path: str) -> None:
    winners = winners_from_completed_round(prev_path)
    expected = WORLD_CUP_TEAM_TOTAL // (2 ** (target_round - 1))
    if len(winners) != expected:
        raise ValueError(
            f"Expected {expected} winners from previous round for World Cup round {target_round}; "
            f"got {len(winners)} from {prev_path!r}"
        )
    random.shuffle(winners)
    used = collect_used_world_pic_indices()
    outp = world_round_path(target_round)
    if os.path.isdir(outp) and listdir_skip_junk(outp):
        raise ValueError(
            f"Target round folder already has content: {outp!r}. "
            "Remove it manually if you need to recreate this round."
        )
    os.makedirs(outp, exist_ok=True)
    n_pairs = len(winners) // 2
    for i in range(n_pairs):
        write_pair_match(i + 1, winners[2 * i], winners[2 * i + 1], outp, used)
    print(f"World Cup Round {target_round} created: {n_pairs} matches under {outp!r}")


def create_world_cup_next() -> int:
    """
    Create exactly one next round if possible.

    Returns:
        Round index 2..8 that was created, or 0 if Final already complete.
    """
    for i in range(1, 9):
        p = world_round_path(i)
        has = round_has_matches(p)
        if not has:
            if i == 1:
                raise ValueError(
                    "World Cup Round 1 missing. Run World_Cup_Create.py first (optionally with -y)."
                )
            prev = world_round_path(i - 1)
            if not round_is_complete(prev):
                raise ValueError(
                    f"World Cup round {i - 1} is not complete yet (pending ' VS ' matches)."
                )
            _build_round_from_winners(i, prev)
            return i
        if not round_is_complete(p):
            raise ValueError(
                f"World Cup round {i} is not complete yet (still has pending ' VS ' matches)."
            )

    print("World Cup is complete through Final (Round 8); no new round to create.")
    return 0


if __name__ == "__main__":
    try:
        n = create_world_cup_next()
        if n:
            print(f"world_cup_next: created round {n}.")
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
