"""
Silver Swiss standings calculator.

Reads:
- League Silver/Swiss Fixture/Round N

Writes:
- League Silver/Silver League Standing

Behavior:
- Auto-detect last complete contiguous round from Round 1 upward
- Stop at first missing/incomplete round (never skip ahead)
- Rank by points, goal difference, goals for, name
"""
from __future__ import annotations

import math
import os
import re
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from match_folder_parse import parse_scored_match_folder_name
from Silver_paths import (
    CHARACTER_SILVER_MASTER,
    LEAGUE_SILVER_STANDING,
    LEAGUE_SILVER_SWISS_FIXTURE,
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


def list_silver_characters() -> list[str]:
    out = []
    for name in _listdir_skip_junk(CHARACTER_SILVER_MASTER):
        p = os.path.join(CHARACTER_SILVER_MASTER, name)
        if os.path.isdir(p):
            out.append(name)
    return out


def _round_is_complete(round_no: int) -> bool:
    r_path = os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, f"Round {round_no}")
    if not os.path.isdir(r_path):
        return False
    matches = [
        n for n in _listdir_skip_junk(r_path) if os.path.isdir(os.path.join(r_path, n))
    ]
    if not matches:
        return False
    for m in matches:
        if " VS " in m:
            return False
    return True


def _max_round_from_team_count(n: int) -> int:
    return int(math.ceil(math.log2(n)))


def last_complete_silver_round(max_scan: int | None = None) -> int:
    teams = list_silver_characters()
    if not teams:
        return 0
    if max_scan is None:
        max_scan = _max_round_from_team_count(len(teams))

    last = 0
    for r in range(1, max_scan + 1):
        if not _round_is_complete(r):
            break
        last = r
    return last


def _init_table(names: list[str]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for name in names:
        table[name] = {
            "point": 0,
            "gf": 0,
            "ga": 0,
            "W": 0,
            "T": 0,
            "L": 0,
        }
    return table


def _parse_scored_match_folder(folder_name: str) -> tuple[str, int, int, str]:
    try:
        _idx, t1, s1, s2, t2 = parse_scored_match_folder_name(folder_name)
    except ValueError as e:
        raise ValueError(
            f"Invalid scored match folder format: {folder_name!r}. "
            "Expected '<idx>. TeamA x-y TeamB' (spaces around score)."
        ) from e
    return t1, s1, s2, t2


def _clear_and_seed_standing() -> None:
    if os.path.isdir(LEAGUE_SILVER_STANDING):
        shutil.rmtree(LEAGUE_SILVER_STANDING)
    os.makedirs(LEAGUE_SILVER_STANDING, exist_ok=True)
    for name in list_silver_characters():
        os.makedirs(os.path.join(LEAGUE_SILVER_STANDING, name), exist_ok=True)


def silver_cal(round_cap: int | None = None) -> dict[str, dict[str, int]]:
    teams = list_silver_characters()
    n = len(teams)
    if n < 2:
        raise ValueError("Need at least 2 Silver teams.")

    max_round = _max_round_from_team_count(n)
    if round_cap is None:
        scan_limit = max_round
    else:
        scan_limit = min(int(round_cap), max_round)

    last_round = last_complete_silver_round(max_scan=scan_limit)
    if last_round < 1:
        raise ValueError(
            "No complete Silver round found: Round 1 must exist and be fully scored."
        )

    table = _init_table(teams)
    for r in range(1, last_round + 1):
        r_path = os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, f"Round {r}")
        for folder_name in _listdir_skip_junk(r_path):
            mdir = os.path.join(r_path, folder_name)
            if not os.path.isdir(mdir):
                continue
            t1, s1, s2, t2 = _parse_scored_match_folder(folder_name)
            if t1 not in table or t2 not in table:
                raise ValueError(
                    f"Unknown team in Round {r}: {folder_name!r}. "
                    "Team names must match Character Silver."
                )

            table[t1]["gf"] += s1
            table[t1]["ga"] += s2
            table[t2]["gf"] += s2
            table[t2]["ga"] += s1

            if s1 > s2:
                table[t1]["point"] += 3
                table[t1]["W"] += 1
                table[t2]["L"] += 1
            elif s1 < s2:
                table[t2]["point"] += 3
                table[t2]["W"] += 1
                table[t1]["L"] += 1
            else:
                table[t1]["point"] += 1
                table[t2]["point"] += 1
                table[t1]["T"] += 1
                table[t2]["T"] += 1

    def _sort_key(name: str) -> tuple[int, int, int, str]:
        d = table[name]
        gd = d["gf"] - d["ga"]
        return (-d["point"], -gd, -d["gf"], name)

    ranked = sorted(teams, key=_sort_key)

    _clear_and_seed_standing()
    for pos, name in enumerate(ranked, start=1):
        d = table[name]
        gd = d["gf"] - d["ga"]
        if gd > 0:
            gd_txt = f"+{gd}"
        else:
            gd_txt = str(gd)
        stat = f"[{d['W']}W-{d['T']}T-{d['L']}L]"
        title = (
            f"{pos}. {name} [{d['point']}pt] "
            f"[{d['gf']}-{d['ga']}={gd_txt}] {stat}"
        )
        os.rename(
            os.path.join(LEAGUE_SILVER_STANDING, name),
            os.path.join(LEAGUE_SILVER_STANDING, title),
        )

    print(
        f"silver_cal: counted Round 1..{last_round} "
        f"(max_round={max_round}, scan_limit={scan_limit})"
    )
    return table


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Silver Swiss standings.")
    ap.add_argument(
        "round_cap",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max round to scan (default: auto until first incomplete).",
    )
    ns = ap.parse_args()
    try:
        silver_cal(ns.round_cap)
    except ValueError as e:
        print(e)
        sys.exit(1)
