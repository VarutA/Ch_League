"""
Gold knockout: create the next round automatically (single entrypoint).

Order: Round 4 -> Round 3 -> Round 2 -> Round 1 (Final).

Rules:
- If the next round folder is missing or has no match subfolders, create that round
  (delegates to Gold_Knockout_Create_4/3/2/1).
- If a round exists with matches but any folder name still contains ' VS ',
  raise error (same as Swiss: previous round must be complete).
- If Round 1 (Final) exists and is fully scored, print message and exit 0 (nothing to create).
"""
from __future__ import annotations

import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Gold_Knockout_Create_1 import create_gold_knockout_round1
from Gold_Knockout_Create_2 import create_gold_knockout_round2
from Gold_Knockout_Create_3 import create_gold_knockout_round3
from Gold_Knockout_Create_4 import CreateGoldKnockoutCancelled, create_gold_knockout_round4
from Gold_paths import (
    GOLD_ROUND1_FIXTURE,
    GOLD_ROUND2_FIXTURE,
    GOLD_ROUND3_FIXTURE,
    GOLD_ROUND4_FIXTURE,
)


def _listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        out.append(name)
    return out


def _match_dirs(fixture_root: str) -> list[str]:
    if not os.path.isdir(fixture_root):
        return []
    return [
        x
        for x in _listdir_skip_junk(fixture_root)
        if os.path.isdir(os.path.join(fixture_root, x))
    ]


def _round_has_matches(fixture_root: str) -> bool:
    return len(_match_dirs(fixture_root)) > 0


def _round_is_complete(fixture_root: str) -> bool:
    matches = _match_dirs(fixture_root)
    if not matches:
        return False
    for name in matches:
        if " VS " in name:
            return False
    return True


def create_gold_knockout_next(force: bool = False) -> int:
    """
    Create exactly one next knockout stage if possible.

    Returns:
        4, 3, 2, or 1 = which round was created
        0 = knockout already complete through Final (all matches scored)
    """
    if _round_has_matches(GOLD_ROUND4_FIXTURE):
        if not _round_is_complete(GOLD_ROUND4_FIXTURE):
            raise ValueError(
                "Round 4 is not complete yet (still has pending ' VS ' matches)."
            )
    else:
        create_gold_knockout_round4(force=force)
        return 4

    if _round_has_matches(GOLD_ROUND3_FIXTURE):
        if not _round_is_complete(GOLD_ROUND3_FIXTURE):
            raise ValueError(
                "Round 3 is not complete yet (still has pending ' VS ' matches)."
            )
    else:
        create_gold_knockout_round3(force=force)
        return 3

    if _round_has_matches(GOLD_ROUND2_FIXTURE):
        if not _round_is_complete(GOLD_ROUND2_FIXTURE):
            raise ValueError(
                "Round 2 is not complete yet (still has pending ' VS ' matches)."
            )
    else:
        create_gold_knockout_round2(force=force)
        return 2

    if _round_has_matches(GOLD_ROUND1_FIXTURE):
        if not _round_is_complete(GOLD_ROUND1_FIXTURE):
            raise ValueError(
                "Round 1 (Final) is not complete yet (still has pending ' VS ' matches)."
            )
        print(
            "Gold knockout is complete through Final; no new round to create."
        )
        return 0

    create_gold_knockout_round1(force=force)
    return 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Create next Gold knockout round (R4 -> R3 -> R2 -> R1) automatically."
    )
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation when target round folder already has data",
    )
    ns = ap.parse_args()
    try:
        n = create_gold_knockout_next(force=ns.yes)
        if n:
            print(f"gold_knockout_next: created round stage (return_code_round={n}).")
    except CreateGoldKnockoutCancelled as e:
        print(e)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
