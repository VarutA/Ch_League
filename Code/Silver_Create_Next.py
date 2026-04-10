"""
Silver Swiss next-round creator (single-file auto detect).

Behavior:
- Detect current highest existing round under League Silver/Swiss Fixture
- Require latest round to be complete before creating next one
- Auto-create next round from Swiss standings of completed rounds
- Max round = ceil(log2(N)), where N = number of Character Silver teams
- If next round would exceed max, do nothing
"""
from __future__ import annotations

import math
import os
import random
import re
import sys
from shutil import copyfile

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from match_folder_parse import parse_scored_match_folder_name
from Silver_paths import (
    CHARACTER_SILVER_MASTER,
    LEAGUE_SILVER_SWISS_FIXTURE,
    PIC_SELECTION,
)

_ROUND_RE = re.compile(r"^Round\s+(\d+)$")


def _listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in (".DS_Store", "Thumbs.db"):
            continue
        out.append(name)
    return out


def _list_silver_characters() -> list[str]:
    names = []
    for n in _listdir_skip_junk(CHARACTER_SILVER_MASTER):
        p = os.path.join(CHARACTER_SILVER_MASTER, n)
        if os.path.isdir(p):
            names.append(n)
    return names


def _detect_pic_ext(char_name: str, league_pic_base: str) -> str:
    root = os.path.join(PIC_SELECTION, char_name)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        fp = os.path.join(root, league_pic_base + ext)
        if os.path.isfile(fp):
            return ext
    raise FileNotFoundError(
        f"No LeaguePIC file for {league_pic_base!r} under {root} "
        f"(tried .jpg, .gif, .png, .jpeg, .bmp)"
    )


def _round_folder(round_no: int) -> str:
    return os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, f"Round {round_no}")


def _existing_round_numbers() -> list[int]:
    nums: list[int] = []
    for name in _listdir_skip_junk(LEAGUE_SILVER_SWISS_FIXTURE):
        m = _ROUND_RE.match(name)
        if not m:
            continue
        p = os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, name)
        if os.path.isdir(p):
            nums.append(int(m.group(1)))
    nums.sort()
    return nums


def _round_is_complete(round_no: int) -> bool:
    path = _round_folder(round_no)
    if not os.path.isdir(path):
        return False
    match_dirs = [
        x
        for x in _listdir_skip_junk(path)
        if os.path.isdir(os.path.join(path, x))
    ]
    if not match_dirs:
        return False
    for name in match_dirs:
        if " VS " in name:
            return False
    return True


def _latest_contiguous_round() -> int:
    """
    Return largest k such that Round 1..k all exist.
    """
    nums = set(_existing_round_numbers())
    k = 0
    while (k + 1) in nums:
        k += 1
    return k


def _init_table(teams: list[str]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for t in teams:
        table[t] = {
            "point": 0,
            "gf": 0,
            "ga": 0,
            "W": 0,
            "T": 0,
            "L": 0,
        }
    return table


def _parse_scored_match_name(name: str) -> tuple[str, int, int, str]:
    """Parse: '<idx>. TeamA x-y TeamB'"""
    try:
        _idx, left, g1, g2, right = parse_scored_match_folder_name(name)
    except ValueError as e:
        raise ValueError(f"Invalid scored match folder: {name!r}") from e
    return left, g1, g2, right


def _build_table_and_opponents(
    teams: list[str],
    upto_round: int,
) -> tuple[dict[str, dict[str, int]], dict[str, set[str]]]:
    table = _init_table(teams)
    opponents: dict[str, set[str]] = {t: set() for t in teams}

    for r in range(1, upto_round + 1):
        r_path = _round_folder(r)
        for entry in _listdir_skip_junk(r_path):
            mdir = os.path.join(r_path, entry)
            if not os.path.isdir(mdir):
                continue
            t1, g1, g2, t2 = _parse_scored_match_name(entry)
            if t1 not in table or t2 not in table:
                raise ValueError(
                    f"Unknown team in Round {r}: {entry!r}. "
                    "Ensure match names use canonical Character Silver names."
                )

            opponents[t1].add(t2)
            opponents[t2].add(t1)

            table[t1]["gf"] += g1
            table[t1]["ga"] += g2
            table[t2]["gf"] += g2
            table[t2]["ga"] += g1

            if g1 > g2:
                table[t1]["point"] += 3
                table[t1]["W"] += 1
                table[t2]["L"] += 1
            elif g1 < g2:
                table[t2]["point"] += 3
                table[t2]["W"] += 1
                table[t1]["L"] += 1
            else:
                table[t1]["point"] += 1
                table[t2]["point"] += 1
                table[t1]["T"] += 1
                table[t2]["T"] += 1

    return table, opponents


def _standing_sort_key(table: dict[str, dict[str, int]], name: str) -> tuple[int, int, int, str]:
    d = table[name]
    gd = d["gf"] - d["ga"]
    return (-d["point"], -gd, -d["gf"], name)


def _pair_next_round(
    ranked: list[str],
    table: dict[str, dict[str, int]],
    opponents: dict[str, set[str]],
) -> list[tuple[str, str]]:
    """
    Swiss greedy pairing:
    1) same points and not played
    2) any points and not played
    3) same points (allow rematch)
    4) anyone (last fallback)
    """
    unpaired = ranked[:]
    pairs: list[tuple[str, str]] = []

    while unpaired:
        t1 = unpaired.pop(0)
        t1_point = table[t1]["point"]

        idx = None
        for i, t2 in enumerate(unpaired):
            if table[t2]["point"] == t1_point and t2 not in opponents[t1]:
                idx = i
                break
        if idx is None:
            for i, t2 in enumerate(unpaired):
                if t2 not in opponents[t1]:
                    idx = i
                    break
        if idx is None:
            for i, t2 in enumerate(unpaired):
                if table[t2]["point"] == t1_point:
                    idx = i
                    break
        if idx is None:
            idx = 0

        t2 = unpaired.pop(idx)
        pairs.append((t1, t2))
    return pairs


def create_silver_next_round() -> int:
    if not os.path.isdir(CHARACTER_SILVER_MASTER):
        raise FileNotFoundError(
            f"Missing master roster folder: {CHARACTER_SILVER_MASTER}"
        )

    teams = _list_silver_characters()
    n = len(teams)
    if n < 2:
        raise ValueError("Need at least 2 Silver teams.")
    if n % 2 != 0:
        raise ValueError(
            f"Character Silver count must be even for Swiss pairing; got {n}."
        )

    max_round = int(math.ceil(math.log2(n)))
    os.makedirs(LEAGUE_SILVER_SWISS_FIXTURE, exist_ok=True)

    latest = _latest_contiguous_round()
    if latest < 1:
        raise ValueError(
            "Round 1 not found. Run Silver_Create.py first to create Round 1."
        )

    if not _round_is_complete(latest):
        raise ValueError(
            f"Round {latest} is not complete yet (still has pending ' VS ' matches)."
        )

    next_round = latest + 1
    if next_round > max_round:
        print(
            f"Swiss already reached max rounds: latest={latest}, max={max_round}. "
            "No new round created."
        )
        return 0

    table, opponents = _build_table_and_opponents(teams, upto_round=latest)
    ranked = sorted(teams, key=lambda t: _standing_sort_key(table, t))

    # Slight shuffle in exact tie buckets to avoid fixed same-order pairing forever.
    grouped: dict[tuple[int, int, int], list[str]] = {}
    for t in ranked:
        d = table[t]
        key = (d["point"], d["gf"] - d["ga"], d["gf"])
        grouped.setdefault(key, []).append(t)
    ranked2: list[str] = []
    seen_keys = sorted(grouped.keys(), reverse=True)
    for k in seen_keys:
        bucket = grouped[k]
        random.shuffle(bucket)
        ranked2.extend(bucket)

    pairs = _pair_next_round(ranked2, table, opponents)

    r_path = _round_folder(next_round)
    if os.path.isdir(r_path) and _listdir_skip_junk(r_path):
        raise ValueError(
            f"Round {next_round} already has data. "
            "Please clear it manually if you want to recreate."
        )
    os.makedirs(r_path, exist_ok=True)

    pic_index = {t: random.randint(1, 50) for t in teams}
    for i, (t1, t2) in enumerate(pairs, start=1):
        match_name = f"{i}. {t1} VS {t2}"
        mdir = os.path.join(r_path, match_name)
        os.makedirs(mdir, exist_ok=True)

        p1 = f"LeaguePIC_{pic_index[t1]}"
        p2 = f"LeaguePIC_{pic_index[t2]}"
        ext1 = _detect_pic_ext(t1, p1)
        ext2 = _detect_pic_ext(t2, p2)

        src1 = os.path.join(PIC_SELECTION, t1, p1 + ext1)
        src2 = os.path.join(PIC_SELECTION, t2, p2 + ext2)
        dst1 = os.path.join(mdir, p1 + ext1)
        dst2 = os.path.join(mdir, p2 + "(A)" + ext2)
        copyfile(src1, dst1)
        copyfile(src2, dst2)

    print(
        f"Created Silver Swiss Round {next_round} "
        f"(from completed Round {latest}; max_round={max_round})."
    )
    return next_round


if __name__ == "__main__":
    try:
        create_silver_next_round()
    except ValueError as e:
        print(e)
        sys.exit(1)
