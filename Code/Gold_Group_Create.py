"""
Gold league group stage creator.

Requirements:
- 80 teams from Character/Character Gold
- Randomly split into 8 groups (A-H), 10 teams each
- Round-robin inside each group (single leg, 9 matches per team)
- Use Diamond-like fixture folder format and picture handling
"""
import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

import random
import shutil
from shutil import copy2, copyfile

from Gold_paths import (
    CHARACTER_GOLD_MASTER,
    GOLD_GROUP_LABELS,
    GOLD_GROUP_SIZE,
    GOLD_GROUP_STATE_ROOT,
    GOLD_GROUP_TEAMS_TOTAL,
    LEAGUE_GOLD_CHARACTER,
    PIC_SELECTION,
)


class CreateGoldGroupCancelled(Exception):
    """User declined replacement of existing Gold group-stage data."""


def round_robin(units, sets=None):
    """Same pairing generator style as Diamond legacy."""
    count = len(units)
    sets = sets or (count - 1)
    half = int(count / 2)
    units = list(units)
    for turn in range(sets):
        left = units[:half]
        right = units[count - half - 1 + 1 :][::-1]
        pairings = zip(left, right)
        if turn % 2 == 1:
            pairings = [(y, x) for (x, y) in pairings]
        units.insert(1, units.pop())
        yield pairings


def _listdir_skip_junk(path):
    names = []
    if not os.path.isdir(path):
        return names
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        names.append(name)
    return names


def list_gold_characters():
    return _listdir_skip_junk(CHARACTER_GOLD_MASTER)


def _rmtree_if_exists(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


def _copytree_master(dst):
    _rmtree_if_exists(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(CHARACTER_GOLD_MASTER, dst)


def _detect_pic_ext(char_name, league_pic_base):
    root = os.path.join(PIC_SELECTION, char_name)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        full = os.path.join(root, league_pic_base + ext)
        if os.path.isfile(full):
            return ext
    raise FileNotFoundError(
        f"No LeaguePIC file for {league_pic_base!r} under {root} "
        f"(tried .jpg, .gif, .png, .jpeg, .bmp)"
    )


def _group_fixture_path(label):
    return os.path.join(GOLD_GROUP_STATE_ROOT, f"Group {label} Fixture")


def _group_standing_path(label):
    return os.path.join(GOLD_GROUP_STATE_ROOT, f"Group {label} Standing")


def _gold_group_has_existing_data():
    if _listdir_skip_junk(LEAGUE_GOLD_CHARACTER):
        return True
    for label in GOLD_GROUP_LABELS:
        if _listdir_skip_junk(_group_fixture_path(label)):
            return True
        if _listdir_skip_junk(_group_standing_path(label)):
            return True
    return False


def _confirm_replace_gold_group(force):
    if not _gold_group_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Gold Group State already has data; refusing to replace without confirmation. "
            "Run in a terminal to answer prompt, pass create_gold_group_state(force=True), "
            "or run: python3 Gold_Group_Create.py -y"
        )
    print(
        "League Gold group stage already has data:\n"
        "  - League Gold/Character Gold\n"
        "  - League Gold/Gold Group State/Group A-H Fixture\n"
        "  - League Gold/Gold Group State/Group A-H Standing\n"
        "This will DELETE those and rebuild only the Group Stage."
    )
    ans = input("Replace Gold Group Stage data? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateGoldGroupCancelled("Cancelled; existing Gold Group Stage data kept.")


def _prepare_group_folders():
    os.makedirs(GOLD_GROUP_STATE_ROOT, exist_ok=True)
    for label in GOLD_GROUP_LABELS:
        fixture = _group_fixture_path(label)
        standing = _group_standing_path(label)
        _rmtree_if_exists(fixture)
        _rmtree_if_exists(standing)
        os.makedirs(fixture, exist_ok=True)
        os.makedirs(standing, exist_ok=True)


def _copy_member_to_standing(member, standing_dir):
    src = os.path.join(CHARACTER_GOLD_MASTER, member)
    dst = os.path.join(standing_dir, member)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    elif os.path.isfile(src):
        copy2(src, dst)
    else:
        # Keep behavior resilient if roster entries are odd/non-directory names.
        os.makedirs(dst, exist_ok=True)


def _build_group_fixture(group_label, members):
    fixture_root = _group_fixture_path(group_label)
    standing_root = _group_standing_path(group_label)

    for member in members:
        _copy_member_to_standing(member, standing_root)

    name_count = {name: 0 for name in members}
    name_random = {
        name: random.sample(range(1, 51), 50) + random.sample(range(1, 51), 8)
        for name in members
    }

    league = list(round_robin(members, sets=len(members) - 1))
    week = 1
    for week_pairings in league:
        week_text = f"week {week}"
        week_path = os.path.join(fixture_root, week_text)
        os.makedirs(week_path)

        pairs = list(week_pairings)
        random.shuffle(pairs)  # keep same pair set, randomize queue order 1..5 each week

        for idx, b in enumerate(pairs):
            match = ""
            m1 = ""
            m2 = ""
            m1_name = ""
            m2_name = ""

            for c in b:
                if match:
                    match += " VS "
                    m2 = "LeaguePIC_" + str(name_random[c][name_count[c]])
                    m2_name = c
                else:
                    m1 = "LeaguePIC_" + str(name_random[c][name_count[c]])
                    m1_name = c
                name_count[c] += 1
                match += c

            # Match number is 1..5, but queue order is randomized every week.
            full_match_name = str(idx + 1) + ". " + match
            match_dir = os.path.join(week_path, full_match_name)
            os.makedirs(match_dir)

            file_type_1 = _detect_pic_ext(m1_name, m1)
            file_type_2 = _detect_pic_ext(m2_name, m2)
            src1 = os.path.join(PIC_SELECTION, m1_name, m1 + file_type_1)
            src2 = os.path.join(PIC_SELECTION, m2_name, m2 + file_type_2)
            dst1 = os.path.join(match_dir, m1 + file_type_1)
            dst2 = os.path.join(match_dir, m2 + "(A)" + file_type_2)
            copyfile(src1, dst1)
            copyfile(src2, dst2)

        week += 1


def create_gold_group_state(force=False):
    """
    Create Gold Group Stage (A-H, 10 teams each).

    - Reads roster from Character/Character Gold
    - Rebuilds League Gold/Character Gold
    - Rebuilds Group A-H Fixture and Group A-H Standing
    - Knockout state is NOT touched
    """
    if not os.path.isdir(CHARACTER_GOLD_MASTER):
        raise FileNotFoundError(f"Missing master roster folder: {CHARACTER_GOLD_MASTER}")

    roster = list_gold_characters()
    if len(roster) != GOLD_GROUP_TEAMS_TOTAL:
        raise ValueError(
            f"Gold Group Stage needs exactly {GOLD_GROUP_TEAMS_TOTAL} teams; found {len(roster)} in "
            f"{CHARACTER_GOLD_MASTER}"
        )

    _confirm_replace_gold_group(force=force)

    random.shuffle(roster)
    grouped = {}
    for i, label in enumerate(GOLD_GROUP_LABELS):
        start = i * GOLD_GROUP_SIZE
        grouped[label] = roster[start : start + GOLD_GROUP_SIZE]

    _copytree_master(LEAGUE_GOLD_CHARACTER)
    _prepare_group_folders()

    for label in GOLD_GROUP_LABELS:
        members = grouped[label]
        print(f"Group {label}: {', '.join(members)}")
        _build_group_fixture(label, members)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Create Gold Group Stage (A-H, 10 teams per group)"
    )
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when Gold Group Stage already has data",
    )
    ns = ap.parse_args()
    try:
        create_gold_group_state(force=ns.yes)
    except CreateGoldGroupCancelled as e:
        print(e)
        sys.exit(1)
