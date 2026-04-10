"""
Create Gold knockout Round 1 (Final) fixture from Round 2 winners.

Rules:
1) Round 2 must be fully complete (no ' VS ' remaining)
2) Winners are extracted from Round 2 scored folder names
3) Create 1 final match
4) Prevent image reuse by team (group + knockout history), with 13-match support
"""
import os
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
from Gold_paths import GOLD_ROUND1_FIXTURE, GOLD_ROUND2_FIXTURE, PIC_SELECTION


def _round2_match_dirs():
    return [
        x
        for x in _listdir_skip_junk(GOLD_ROUND2_FIXTURE)
        if os.path.isdir(os.path.join(GOLD_ROUND2_FIXTURE, x))
    ]


def _assert_round2_complete():
    if not os.path.isdir(GOLD_ROUND2_FIXTURE):
        raise FileNotFoundError(f"Missing Round 2 fixture folder: {GOLD_ROUND2_FIXTURE}")
    matches = _round2_match_dirs()
    if not matches:
        raise ValueError("Round 2 fixture has no match folders.")
    for m in matches:
        if " VS " in m:
            raise ValueError(
                "Round 2 not complete: pending match folder still has 'VS': {}".format(m)
            )


def _round2_winners():
    winners = []
    matches = sorted(_round2_match_dirs())
    for m in matches:
        try:
            _i, left, s1, s2, right = parse_scored_match_folder_name(m)
        except ValueError as e:
            raise ValueError(f"Round 2 folder format invalid (expect scored): {m}") from e
        if s1 == s2:
            raise ValueError(
                f"Round 2 match has draw score {s1}-{s2}; cannot pick winner automatically: {m}"
            )
        winners.append(left if s1 > s2 else right)
    if len(winners) != 2:
        raise ValueError(f"Round 2 must produce 2 winners; got {len(winners)}")
    return winners


def _round1_has_existing_data():
    return bool(_listdir_skip_junk(GOLD_ROUND1_FIXTURE))


def _confirm_replace_round1(force):
    if not _round1_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Round 1 fixture already has data; refusing to replace without confirmation. "
            "Use a terminal prompt or pass -y."
        )
    ans = input("Round 1 fixture already exists. Replace it? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateGoldKnockoutCancelled("Cancelled; existing Round 1 fixture kept.")


def _prepare_round1_folder():
    if os.path.isdir(GOLD_ROUND1_FIXTURE):
        shutil.rmtree(GOLD_ROUND1_FIXTURE)
    os.makedirs(GOLD_ROUND1_FIXTURE, exist_ok=True)


def create_gold_knockout_round1(force=False):
    """
    Build Round 1 (Final) from Round 2 winners.
    """
    _assert_round2_complete()
    _confirm_replace_round1(force=force)

    t1, t2 = _round2_winners()
    used = _collect_used_pic_indices()

    _prepare_round1_folder()

    p1 = _pick_fresh_pic_index(t1, used.get(t1, set()))
    used.setdefault(t1, set()).add(p1)
    p2 = _pick_fresh_pic_index(t2, used.get(t2, set()))
    used.setdefault(t2, set()).add(p2)

    ext1 = _detect_pic_ext(t1, p1)
    ext2 = _detect_pic_ext(t2, p2)

    match_name = f"1. {t1} VS {t2}"
    match_dir = os.path.join(GOLD_ROUND1_FIXTURE, match_name)
    os.makedirs(match_dir, exist_ok=True)

    src1 = os.path.join(PIC_SELECTION, t1, f"LeaguePIC_{p1}{ext1}")
    src2 = os.path.join(PIC_SELECTION, t2, f"LeaguePIC_{p2}{ext2}")
    dst1 = os.path.join(match_dir, f"LeaguePIC_{p1}{ext1}")
    dst2 = os.path.join(match_dir, f"LeaguePIC_{p2}(A){ext2}")
    copyfile(src1, dst1)
    copyfile(src2, dst2)

    print(f"Round1 Final: {t1} VS {t2}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Create Gold Knockout Round 1 (Final) from Round 2 winners"
    )
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when Round 1 fixture already has data",
    )
    ns = ap.parse_args()
    try:
        create_gold_knockout_round1(force=ns.yes)
    except (CreateGoldKnockoutCancelled, ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
