"""
Build final Gold summary ranking folders.

Output:
- League Gold/Gold Rank Summary

Folder format:
1. (Winner) Character
2. (Runner-Up) Character
3. (Semi-Final) Character
3. (Semi-Final) Character
5. (Quarter-Final) Character
...
9. (Round 16) Character
...
17. (Group-State) Character
"""
import os
import re
import shutil
import sys
from shutil import copy2

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Gold_Knockout_Create_4 import CreateGoldKnockoutCancelled, _listdir_skip_junk
from match_folder_parse import parse_scored_match_folder_name
from standing_folder_parse import parse_gold_overall_standing_team
from Gold_paths import (
    GOLD_RANK_SUMMARY,
    GOLD_ROUND1_FIXTURE,
    GOLD_ROUND2_FIXTURE,
    GOLD_ROUND3_FIXTURE,
    GOLD_ROUND4_FIXTURE,
    LEAGUE_GOLD_CHARACTER,
    LEAGUE_GOLD_OVERALL_STANDING,
)

_RANK_RE = re.compile(r"^(\d+)\.\s+")


class CreateGoldSummaryCancelled(Exception):
    """User declined replacing existing Gold Rank Summary."""


def _match_dirs(path):
    return [
        x for x in _listdir_skip_junk(path) if os.path.isdir(os.path.join(path, x))
    ]


def _assert_complete_scored_round(path, round_name):
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Missing {round_name} folder: {path}")
    dirs = _match_dirs(path)
    if not dirs:
        raise ValueError(f"{round_name} has no match folders.")
    for d in dirs:
        if " VS " in d:
            raise ValueError(f"{round_name} not complete: pending folder {d!r}")


def _parse_scored_match(folder_name, round_name):
    try:
        _idx, left, s1, s2, right = parse_scored_match_folder_name(folder_name)
    except ValueError as e:
        raise ValueError(
            f"{round_name} invalid scored folder format: {folder_name!r}"
        ) from e
    if s1 == s2:
        raise ValueError(
            f"{round_name} has draw score {s1}-{s2}; summary requires a winner: {folder_name!r}"
        )
    winner = left if s1 > s2 else right
    loser = right if s1 > s2 else left
    return left, right, winner, loser


def _round_outcomes(path, round_name):
    outcomes = []
    for d in sorted(_match_dirs(path)):
        left, right, winner, loser = _parse_scored_match(d, round_name)
        outcomes.append(
            {
                "folder": d,
                "left": left,
                "right": right,
                "winner": winner,
                "loser": loser,
            }
        )
    return outcomes


def _canonical_team_names():
    return _listdir_skip_junk(LEAGUE_GOLD_CHARACTER)


def _extract_team_from_overall_folder(fname: str, team_set: set[str]) -> str | None:
    t = parse_gold_overall_standing_team(fname)
    if t is not None and t in team_set:
        return t
    if fname in team_set:
        return fname
    return None


def _group_state_ordered_non_qualifiers(qualified_set):
    if not os.path.isdir(LEAGUE_GOLD_OVERALL_STANDING):
        raise FileNotFoundError(
            f"Missing overall standing folder: {LEAGUE_GOLD_OVERALL_STANDING}. "
            "Run group-cal first."
        )
    team_set = set(_canonical_team_names())
    entries = []
    for name in _listdir_skip_junk(LEAGUE_GOLD_OVERALL_STANDING):
        m = _RANK_RE.match(name)
        if not m:
            continue
        rank_no = int(m.group(1))
        team = _extract_team_from_overall_folder(name, team_set)
        if not team:
            continue
        entries.append((rank_no, team))
    entries.sort(key=lambda x: x[0])
    out = []
    seen = set()
    for _, team in entries:
        if team in qualified_set:
            continue
        if team in seen:
            continue
        seen.add(team)
        out.append(team)
    return out


def _summary_has_data():
    return bool(_listdir_skip_junk(GOLD_RANK_SUMMARY))


def _confirm_replace_summary(force):
    if not _summary_has_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Gold Rank Summary already has data; refusing to replace without confirmation. "
            "Use terminal prompt or pass -y."
        )
    ans = input("Gold Rank Summary already exists. Replace it? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateGoldSummaryCancelled("Cancelled; existing Gold Rank Summary kept.")


def _reset_summary_folder():
    if os.path.isdir(GOLD_RANK_SUMMARY):
        shutil.rmtree(GOLD_RANK_SUMMARY)
    os.makedirs(GOLD_RANK_SUMMARY, exist_ok=True)


def _copy_team_to_summary(team, title):
    src = os.path.join(LEAGUE_GOLD_CHARACTER, team)
    dst = os.path.join(GOLD_RANK_SUMMARY, title)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    elif os.path.isfile(src):
        os.makedirs(dst, exist_ok=True)
        copy2(src, os.path.join(dst, os.path.basename(src)))
    else:
        raise FileNotFoundError(f"Missing team source in League Gold/Character Gold: {team}")


def create_gold_summary(force=False):
    """
    Build ranking summary from completed knockout rounds and group standings.
    """
    _assert_complete_scored_round(GOLD_ROUND4_FIXTURE, "Round 4 (16 Team)")
    _assert_complete_scored_round(GOLD_ROUND3_FIXTURE, "Round 3 (Quarter Final)")
    _assert_complete_scored_round(GOLD_ROUND2_FIXTURE, "Round 2 (Semi Final)")
    _assert_complete_scored_round(GOLD_ROUND1_FIXTURE, "Round 1 (Final)")

    r4 = _round_outcomes(GOLD_ROUND4_FIXTURE, "Round 4 (16 Team)")
    r3 = _round_outcomes(GOLD_ROUND3_FIXTURE, "Round 3 (Quarter Final)")
    r2 = _round_outcomes(GOLD_ROUND2_FIXTURE, "Round 2 (Semi Final)")
    r1 = _round_outcomes(GOLD_ROUND1_FIXTURE, "Round 1 (Final)")

    if len(r4) != 8 or len(r3) != 4 or len(r2) != 2 or len(r1) != 1:
        raise ValueError(
            "Unexpected knockout match counts: "
            f"R4={len(r4)}, R3={len(r3)}, R2={len(r2)}, R1={len(r1)}"
        )

    winner = r1[0]["winner"]
    runner_up = r1[0]["loser"]
    semi_losers = [x["loser"] for x in r2]
    quarter_losers = [x["loser"] for x in r3]
    round16_losers = [x["loser"] for x in r4]
    qualified_16 = set()
    for x in r4:
        qualified_16.add(x["left"])
        qualified_16.add(x["right"])

    group_state = _group_state_ordered_non_qualifiers(qualified_16)
    if len(group_state) != 64:
        raise ValueError(
            f"Expected 64 Group-State teams, got {len(group_state)}. "
            "Check overall standing or knockout participants."
        )

    _confirm_replace_summary(force=force)
    _reset_summary_folder()

    # Build ordered summary rows
    rows = []
    rows.append((1, "Winner", winner))
    rows.append((2, "Runner-Up", runner_up))
    for t in semi_losers:
        rows.append((3, "Semi-Final", t))
    for t in quarter_losers:
        rows.append((5, "Quarter-Final", t))
    for t in round16_losers:
        rows.append((9, "Round 16", t))
    for i, t in enumerate(group_state, start=17):
        rows.append((i, "Group-State", t))

    seen = set()
    for rank_no, tag, team in rows:
        if team in seen:
            raise ValueError(f"Duplicate team in summary ranking: {team}")
        seen.add(team)
        title = f"{rank_no}. ({tag}) {team}"
        _copy_team_to_summary(team, title)
        print(title)

    if len(rows) != 80:
        raise ValueError(f"Summary rows expected 80, got {len(rows)}")

    print(f"Gold summary created at: {GOLD_RANK_SUMMARY}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Create Gold rank summary folders")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Gold Rank Summary already has data",
    )
    ns = ap.parse_args()
    try:
        create_gold_summary(force=ns.yes)
    except (
        CreateGoldSummaryCancelled,
        ValueError,
        RuntimeError,
        FileNotFoundError,
    ) as e:
        print(e)
        sys.exit(1)
