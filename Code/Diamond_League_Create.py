"""
Diamond league: build fixture (same layout as legacy create_league).
Master roster: Character/Character Diamond (project root)
Pics: Character/Pic Selection/<character>/LeaguePIC_*.{ext}
Copies master -> League Diamond/Character Diamond and Diamond League Standing (project root).
Fixture -> League Diamond/Diamond League Fixture/week N/...
"""
import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

import random
import shutil
from shutil import copyfile

from Diamond_paths import (
    CHARACTER_DIAMOND_MASTER,
    LEAGUE_DIAMOND_CHARACTER,
    LEAGUE_DIAMOND_FIXTURE,
    LEAGUE_DIAMOND_STANDING,
    PIC_SELECTION,
)


class CreateDiamondLeagueCancelled(Exception):
    """User declined the replace confirmation (interactive runs only)."""


def round_robin(units, sets=None):
    """Generates a schedule of pairings from a list of units (legacy behavior)."""
    count = len(units)
    sets = sets or (count - 1)
    half = int(count / 2)
    print(half)
    print("------")
    print(units)
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
        if name == "Thumbs.db" or name == ".DS_Store":
            continue
        names.append(name)
    return names


def list_diamond_characters():
    """Character names = entries under Character/Character Diamond (legacy list_cha)."""
    return _listdir_skip_junk(CHARACTER_DIAMOND_MASTER)


def _league_diamond_has_existing_data():
    """True if fixture, league character copy, or standing already has any non-junk content."""
    for base in (
        LEAGUE_DIAMOND_FIXTURE,
        LEAGUE_DIAMOND_CHARACTER,
        LEAGUE_DIAMOND_STANDING,
    ):
        if not os.path.isdir(base):
            continue
        if _listdir_skip_junk(base):
            return True
    return False


def _confirm_replace_league_diamond(force):
    if not _league_diamond_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "League Diamond already has data; refusing to replace without confirmation. "
            "Run in a terminal to answer the prompt, pass create_diamond_league(force=True), "
            "or run: python3 Diamond_League_Create.py -y"
        )
    print(
        "League Diamond already has data:\n"
        "  - Diamond League Fixture (all week folders)\n"
        "  - Character Diamond (league copy)\n"
        "  - Diamond League Standing\n"
        "This will DELETE those and rebuild from Character/Character Diamond."
    )
    ans = input("Replace everything? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateDiamondLeagueCancelled("Cancelled; existing League Diamond data kept.")


def _rmtree_if_exists(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


def _copytree_master(dst):
    _rmtree_if_exists(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(CHARACTER_DIAMOND_MASTER, dst)


def _detect_pic_ext(char_name, league_pic_base):
    """Return file extension for LeaguePIC file under Pic Selection (legacy order)."""
    root = os.path.join(PIC_SELECTION, char_name)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        path = os.path.join(root, league_pic_base + ext)
        if os.path.isfile(path):
            return ext
    raise FileNotFoundError(
        f"No LeaguePIC file for {league_pic_base!r} under {root} "
        f"(tried .jpg, .gif, .png, .jpeg, .bmp)"
    )


def _clear_fixture_folder():
    _rmtree_if_exists(LEAGUE_DIAMOND_FIXTURE)
    os.makedirs(LEAGUE_DIAMOND_FIXTURE, exist_ok=True)


def create_diamond_league(force=False):
    """
    Replace legacy create_league: same fixture naming and pic copy rules,
    restructured paths for Diamond.

    If League Diamond already has fixture / copies / standing, prompts for confirmation
    unless ``force=True`` (or use ``python3 Diamond_League_Create.py -y``).
    """
    if not os.path.isdir(CHARACTER_DIAMOND_MASTER):
        raise FileNotFoundError(
            f"Missing master roster folder: {CHARACTER_DIAMOND_MASTER}"
        )

    _confirm_replace_league_diamond(force=force)

    _copytree_master(LEAGUE_DIAMOND_CHARACTER)
    _copytree_master(LEAGUE_DIAMOND_STANDING)

    name_count = {}
    name_random = {}
    list_character = list_diamond_characters()
    if len(list_character) < 2:
        raise ValueError("Need at least two entries in Character Diamond.")

    random.shuffle(list_character)

    for name in list_character:
        print(name)
        name_count[name] = 0
        name_random[name] = random.sample(range(1, 51), 50) + random.sample(
            range(1, 51), 8
        )
    print(name_random)
    print(name_count)

    _clear_fixture_folder()

    league = list(
        round_robin(list_character, sets=len(list_character) * 2 - 2)
    )
    week = 1
    for a in league:
        week_text = "week {}".format(week)
        week_path = os.path.join(LEAGUE_DIAMOND_FIXTURE, week_text)
        os.makedirs(week_path)

        week_pairings = list(a)
        random.shuffle(week_pairings)  # keep pair set, randomize queue order each week
        for idx, b in enumerate(week_pairings):
            match = ""

            m1 = ""
            m2 = ""
            m1_name = ""
            m2_name = ""

            for c in b:
                if match != "":
                    match = match + " VS "
                    m2 = "LeaguePIC_" + str(name_random[c][name_count[c]])
                    m2_name = c
                else:
                    print(c)
                    print(name_count[c])
                    m1 = "LeaguePIC_" + str(name_random[c][name_count[c]])
                    m1_name = c

                name_count[c] = name_count[c] + 1
                match = match + c

            # Match number is 1..N, queue order is randomized every week.
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

        week = week + 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Create Diamond league fixture from master roster.")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when League Diamond already has data",
    )
    args = ap.parse_args()
    try:
        create_diamond_league(force=args.yes)
    except CreateDiamondLeagueCancelled as e:
        print(e)
        sys.exit(1)
