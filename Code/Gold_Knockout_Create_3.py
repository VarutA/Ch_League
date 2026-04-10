"""
Create Gold knockout Round 3 (Quarter Final) fixture from Round 4 winners.

Rules implemented:
1) Round 4 must be fully complete (no ' VS ' remaining)
2) Winners are extracted from Round 4 scored folder names
3) Random draw winners into 4 quarter-final pairings
4) Prevent image reuse by team (group + knockout history), with max 13-match support
"""
import os
import random
import shutil
import sys
from shutil import copyfile

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from match_folder_parse import parse_scored_match_folder_name
from Gold_Knockout_Create_4 import (
    CreateGoldKnockoutCancelled,
    _collect_used_pic_indices,
    _detect_pic_ext,
    _listdir_skip_junk,
    _pick_fresh_pic_index,
)
from Gold_paths import GOLD_ROUND3_FIXTURE, GOLD_ROUND4_FIXTURE, PIC_SELECTION


def _round4_match_dirs():
    return [
        x
        for x in _listdir_skip_junk(GOLD_ROUND4_FIXTURE)
        if os.path.isdir(os.path.join(GOLD_ROUND4_FIXTURE, x))
    ]


def _assert_round4_complete():
    if not os.path.isdir(GOLD_ROUND4_FIXTURE):
        raise FileNotFoundError(f"Missing Round 4 fixture folder: {GOLD_ROUND4_FIXTURE}")
    matches = _round4_match_dirs()
    if not matches:
        raise ValueError("Round 4 fixture has no match folders.")
    for m in matches:
        if " VS " in m:
            raise ValueError(
                "Round 4 not complete: pending match folder still has 'VS': {}".format(m)
            )


def _round4_winners():
    winners = []
    matches = sorted(_round4_match_dirs())
    for m in matches:
        try:
            _i, left, s1, s2, right = parse_scored_match_folder_name(m)
        except ValueError as e:
            raise ValueError(f"Round 4 folder format invalid (expect scored): {m}") from e
        if s1 == s2:
            raise ValueError(
                f"Round 4 match has draw score {s1}-{s2}; cannot pick winner automatically: {m}"
            )
        winners.append(left if s1 > s2 else right)
    if len(winners) != 8:
        raise ValueError(f"Round 4 must produce 8 winners; got {len(winners)}")
    return winners


def _round3_has_existing_data():
    return bool(_listdir_skip_junk(GOLD_ROUND3_FIXTURE))


def _confirm_replace_round3(force):
    if not _round3_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Round 3 fixture already has data; refusing to replace without confirmation. "
            "Use a terminal prompt or pass -y."
        )
    ans = input("Round 3 fixture already exists. Replace it? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateGoldKnockoutCancelled("Cancelled; existing Round 3 fixture kept.")


def _prepare_round3_folder():
    if os.path.isdir(GOLD_ROUND3_FIXTURE):
        shutil.rmtree(GOLD_ROUND3_FIXTURE)
    os.makedirs(GOLD_ROUND3_FIXTURE, exist_ok=True)


def create_gold_knockout_round3(force=False):
    """
    Build Round 3 (Quarter Final) from Round 4 winners:
    - verify round 4 complete
    - extract 8 winners
    - random pairings into 4 matches
    - copy non-reused team images
    """
    _assert_round4_complete()
    _confirm_replace_round3(force=force)

    winners = _round4_winners()
    random.shuffle(winners)
    used = _collect_used_pic_indices()

    _prepare_round3_folder()
    for i in range(4):
        t1 = winners[2 * i]
        t2 = winners[2 * i + 1]

        p1 = _pick_fresh_pic_index(t1, used.get(t1, set()))
        used.setdefault(t1, set()).add(p1)
        p2 = _pick_fresh_pic_index(t2, used.get(t2, set()))
        used.setdefault(t2, set()).add(p2)

        ext1 = _detect_pic_ext(t1, p1)
        ext2 = _detect_pic_ext(t2, p2)

        match_name = f"{i + 1}. {t1} VS {t2}"
        match_dir = os.path.join(GOLD_ROUND3_FIXTURE, match_name)
        os.makedirs(match_dir, exist_ok=True)

        src1 = os.path.join(PIC_SELECTION, t1, f"LeaguePIC_{p1}{ext1}")
        src2 = os.path.join(PIC_SELECTION, t2, f"LeaguePIC_{p2}{ext2}")
        dst1 = os.path.join(match_dir, f"LeaguePIC_{p1}{ext1}")
        dst2 = os.path.join(match_dir, f"LeaguePIC_{p2}(A){ext2}")
        copyfile(src1, dst1)
        copyfile(src2, dst2)

        print(f"Round3 #{i + 1}: {t1} VS {t2}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Create Gold Knockout Round 3 (Quarter Final) from Round 4 winners"
    )
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when Round 3 fixture already has data",
    )
    ns = ap.parse_args()
    try:
        create_gold_knockout_round3(force=ns.yes)
    except (CreateGoldKnockoutCancelled, ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
