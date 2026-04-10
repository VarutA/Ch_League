"""
Silver Swiss creator (first file): create Round 1 only.

Rules:
- N = number of Character Silver entries
- N must be even, otherwise raise error
- Swiss total rounds = ceil(log2(N)) (printed for reference)
- Round 1 pairings are random across all teams
"""
import math
import os
import random
import shutil
import sys
from shutil import copyfile

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Silver_paths import (
    CHARACTER_SILVER_MASTER,
    LEAGUE_SILVER_CHARACTER,
    LEAGUE_SILVER_STANDING,
    LEAGUE_SILVER_SWISS_FIXTURE,
    PIC_SELECTION,
)


class CreateSilverCancelled(Exception):
    """User declined replacing existing Silver Swiss data."""


def _listdir_skip_junk(path):
    names = []
    if not os.path.isdir(path):
        return names
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        names.append(name)
    return names


def list_silver_characters():
    return _listdir_skip_junk(CHARACTER_SILVER_MASTER)


def _rmtree_if_exists(path):
    if os.path.isdir(path):
        shutil.rmtree(path)


def _copytree_master(dst):
    _rmtree_if_exists(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(CHARACTER_SILVER_MASTER, dst)


def _detect_pic_ext(char_name, league_pic_base):
    root = os.path.join(PIC_SELECTION, char_name)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        path = os.path.join(root, league_pic_base + ext)
        if os.path.isfile(path):
            return ext
    raise FileNotFoundError(
        f"No LeaguePIC file for {league_pic_base!r} under {root} "
        f"(tried .jpg, .gif, .png, .jpeg, .bmp)"
    )


def _silver_has_existing_data():
    for base in (
        LEAGUE_SILVER_SWISS_FIXTURE,
        LEAGUE_SILVER_CHARACTER,
        LEAGUE_SILVER_STANDING,
    ):
        if _listdir_skip_junk(base):
            return True
    return False


def _confirm_replace_silver(force):
    if not _silver_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "League Silver already has data; refusing to replace without confirmation. "
            "Use terminal prompt or pass -y."
        )
    print(
        "League Silver already has data:\n"
        "  - Swiss Fixture\n"
        "  - Character Silver (league copy)\n"
        "  - Silver League Standing\n"
        "This will DELETE those and rebuild Round 1."
    )
    ans = input("Replace Silver Swiss data? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateSilverCancelled("Cancelled; existing Silver data kept.")


def _clear_fixture_root():
    _rmtree_if_exists(LEAGUE_SILVER_SWISS_FIXTURE)
    os.makedirs(LEAGUE_SILVER_SWISS_FIXTURE, exist_ok=True)


def create_silver_round1(force=False):
    """
    Create only Swiss Round 1 at:
    League Silver/Swiss Fixture/Round 1
    """
    if not os.path.isdir(CHARACTER_SILVER_MASTER):
        raise FileNotFoundError(
            f"Missing master roster folder: {CHARACTER_SILVER_MASTER}"
        )

    teams = list_silver_characters()
    n = len(teams)
    if n < 2:
        raise ValueError("Need at least 2 Silver teams.")
    if n % 2 != 0:
        raise ValueError(
            f"Character Silver count must be even for Swiss pairing; got {n}."
        )

    rounds = int(math.ceil(math.log2(n)))
    print(f"Silver Swiss: N={n}, total_rounds=ceil(log2(N))={rounds}")

    _confirm_replace_silver(force=force)
    _copytree_master(LEAGUE_SILVER_CHARACTER)
    _copytree_master(LEAGUE_SILVER_STANDING)
    _clear_fixture_root()

    random.shuffle(teams)
    round1_path = os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, "Round 1")
    os.makedirs(round1_path, exist_ok=True)

    # Pick one random LeaguePIC index per team for round 1.
    pic_index = {t: random.randint(1, 50) for t in teams}

    match_no = 1
    for i in range(0, n, 2):
        t1 = teams[i]
        t2 = teams[i + 1]
        match_name = f"{match_no}. {t1} VS {t2}"
        match_dir = os.path.join(round1_path, match_name)
        os.makedirs(match_dir, exist_ok=True)

        p1 = f"LeaguePIC_{pic_index[t1]}"
        p2 = f"LeaguePIC_{pic_index[t2]}"
        ext1 = _detect_pic_ext(t1, p1)
        ext2 = _detect_pic_ext(t2, p2)

        src1 = os.path.join(PIC_SELECTION, t1, p1 + ext1)
        src2 = os.path.join(PIC_SELECTION, t2, p2 + ext2)
        dst1 = os.path.join(match_dir, p1 + ext1)
        dst2 = os.path.join(match_dir, p2 + "(A)" + ext2)
        copyfile(src1, dst1)
        copyfile(src2, dst2)
        match_no += 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Create Silver Swiss Round 1")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if League Silver already has data",
    )
    ns = ap.parse_args()
    try:
        create_silver_round1(force=ns.yes)
    except CreateSilverCancelled as e:
        print(e)
        sys.exit(1)
