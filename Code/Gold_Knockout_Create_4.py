"""
Create Gold knockout Round 4 (16 Team) fixture.

Rules implemented:
1) Group stage must be fully complete (all groups A-H, weeks 1..9 scored; no ' VS ' remains)
2) Qualifiers are rank 1 and 2 from each group
3) Draw random pairings: rank-1 teams vs rank-2 teams
4) Prevent image reuse by team (group + knockout history) and enforce capacity for max 13 matches
"""
import os
import random
import re
import shutil
import sys
from shutil import copyfile

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Gold_Group_Cal import gold_group_cal
from match_folder_parse import parse_scored_match_folder_name
from Gold_paths import (
    GOLD_GROUP_FIXTURE_MAX_WEEK,
    GOLD_GROUP_LABELS,
    GOLD_GROUP_STATE_ROOT,
    GOLD_KNOCKOUT_STATE_ROOT,
    GOLD_ROUND4_FIXTURE,
    LEAGUE_GOLD_CHARACTER,
    PIC_SELECTION,
)

_PIC_INDEX_RE = re.compile(r"LeaguePIC_(\d+)")


class CreateGoldKnockoutCancelled(Exception):
    """User declined replacing existing Round 4 fixture."""


def _listdir_skip_junk(path):
    names = []
    if not os.path.isdir(path):
        return names
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        names.append(name)
    return names


def _group_fixture_root(label):
    return os.path.join(GOLD_GROUP_STATE_ROOT, f"Group {label} Fixture")


def _week_is_complete(week_path):
    if not os.path.isdir(week_path):
        return False
    subs = [
        x
        for x in _listdir_skip_junk(week_path)
        if os.path.isdir(os.path.join(week_path, x))
    ]
    if not subs:
        return False
    for name in subs:
        if " VS " in name:
            return False
    return True


def _assert_group_stage_complete():
    for w in range(1, GOLD_GROUP_FIXTURE_MAX_WEEK + 1):
        for label in GOLD_GROUP_LABELS:
            week_path = os.path.join(_group_fixture_root(label), f"week {w}")
            if not _week_is_complete(week_path):
                raise ValueError(
                    "Group stage not complete: Group {} week {} still pending. "
                    "Finish all matches before creating knockout.".format(label, w)
                )


def _rank_names(name_data):
    return sorted(
        name_data.keys(),
        key=lambda n: (
            -name_data[n]["point"],
            -(name_data[n]["g1"] - name_data[n]["g2"]),
            -name_data[n]["g1"],
            n,
        ),
    )


def _qualifiers_from_group_data(result_by_group):
    winners = []
    runners = []
    for label in GOLD_GROUP_LABELS:
        ranking = _rank_names(result_by_group[label])
        if len(ranking) < 2:
            raise ValueError(f"Group {label} has fewer than 2 teams in standings data.")
        winners.append((label, ranking[0]))
        runners.append((label, ranking[1]))
    return winners, runners


def _draw_pairs_1v2(winners, runners):
    """
    Draw 8 pairs: winner vs runner-up.
    Strict rule: never allow same-group pair (1A cannot face 2A, etc.).
    """
    winners = winners[:]
    random.shuffle(winners)

    def backtrack(i, available_runners):
        if i == len(winners):
            return []
        g1, t1 = winners[i]
        random.shuffle(available_runners)
        for j, (g2, t2) in enumerate(available_runners):
            if g1 == g2:
                continue
            nxt = backtrack(i + 1, available_runners[:j] + available_runners[j + 1 :])
            if nxt is not None:
                return [((g1, t1), (g2, t2))] + nxt
        return None

    out = backtrack(0, runners[:])
    if out is None:
        raise RuntimeError(
            "Could not generate Round 4 draw with strict cross-group rule "
            "(group winner cannot face same-group runner-up)."
        )
    return out


def _collect_used_pic_indices():
    """
    Return used LeaguePIC indices per team from:
    - all group fixture folders
    - all knockout fixture folders
    """
    used = {}

    def add_file(team, filename):
        m = _PIC_INDEX_RE.search(filename)
        if not m:
            return
        idx = int(m.group(1))
        used.setdefault(team, set()).add(idx)

    # Group fixtures
    for label in GOLD_GROUP_LABELS:
        group_root = _group_fixture_root(label)
        for week in _listdir_skip_junk(group_root):
            week_path = os.path.join(group_root, week)
            if not os.path.isdir(week_path):
                continue
            for match in _listdir_skip_junk(week_path):
                match_path = os.path.join(week_path, match)
                if not os.path.isdir(match_path):
                    continue
                files = _listdir_skip_junk(match_path)
                if ". " in match and (" VS " in match or "-" in match):
                    if " VS " in match:
                        body = match.split(". ", 1)[1]
                        left, right = body.split(" VS ", 1)
                    else:
                        try:
                            _i, left, _s1, _s2, right = parse_scored_match_folder_name(
                                match
                            )
                        except ValueError:
                            continue
                    for f in files:
                        if "(A)" in f:
                            add_file(right, f)
                        else:
                            add_file(left, f)

    # Knockout fixtures
    if os.path.isdir(GOLD_KNOCKOUT_STATE_ROOT):
        for round_name in _listdir_skip_junk(GOLD_KNOCKOUT_STATE_ROOT):
            round_path = os.path.join(GOLD_KNOCKOUT_STATE_ROOT, round_name)
            if not os.path.isdir(round_path):
                continue
            for match in _listdir_skip_junk(round_path):
                match_path = os.path.join(round_path, match)
                if not os.path.isdir(match_path):
                    continue
                if ". " not in match:
                    continue
                body = match.split(". ", 1)[1]
                if " VS " in body:
                    left, right = body.split(" VS ", 1)
                else:
                    try:
                        _i, left, _s1, _s2, right = parse_scored_match_folder_name(match)
                    except ValueError:
                        continue
                for f in _listdir_skip_junk(match_path):
                    if "(A)" in f:
                        add_file(right, f)
                    else:
                        add_file(left, f)

    return used


def _available_pic_indices_for_team(team):
    team_dir = os.path.join(PIC_SELECTION, team)
    if not os.path.isdir(team_dir):
        raise FileNotFoundError(f"Missing pic folder for team {team!r}: {team_dir}")
    available = set()
    for f in _listdir_skip_junk(team_dir):
        m = _PIC_INDEX_RE.search(f)
        if not m:
            continue
        available.add(int(m.group(1)))
    return available


def _pick_fresh_pic_index(team, used_indices):
    available = _available_pic_indices_for_team(team)
    # Requirement 0: team may play up to 13 games -> must have >=13 distinct LeaguePIC
    if len(available) < 13:
        raise ValueError(
            f"Team {team} has only {len(available)} distinct LeaguePIC files; need at least 13."
        )
    remaining = sorted(available - used_indices)
    if not remaining:
        raise ValueError(
            f"No unused LeaguePIC left for team {team}. Used={len(used_indices)}, "
            f"available={len(available)}."
        )
    return remaining[0]


def _detect_pic_ext(team, idx):
    base = f"LeaguePIC_{idx}"
    root = os.path.join(PIC_SELECTION, team)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        full = os.path.join(root, base + ext)
        if os.path.isfile(full):
            return ext
    raise FileNotFoundError(f"Missing LeaguePIC_{idx} file for team {team} in {root}")


def _round4_has_existing_data():
    return bool(_listdir_skip_junk(GOLD_ROUND4_FIXTURE))


def _confirm_replace_round4(force):
    if not _round4_has_existing_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Round 4 fixture already has data; refusing to replace without confirmation. "
            "Use a terminal prompt or pass -y."
        )
    ans = input("Round 4 fixture already exists. Replace it? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateGoldKnockoutCancelled("Cancelled; existing Round 4 fixture kept.")


def _prepare_round4_folder():
    if os.path.isdir(GOLD_ROUND4_FIXTURE):
        shutil.rmtree(GOLD_ROUND4_FIXTURE)
    os.makedirs(GOLD_ROUND4_FIXTURE, exist_ok=True)


def create_gold_knockout_round4(force=False):
    """
    Build Round 4 (16 Team) fixture:
    - verify group stage fully complete
    - take top 1,2 from each group
    - random draw 1 vs 2
    - copy two non-reused images into each match folder
    """
    _assert_group_stage_complete()
    _confirm_replace_round4(force=force)

    # Ensure standings are fresh and deterministic from completed groups.
    all_group_data = gold_group_cal()
    winners, runners = _qualifiers_from_group_data(all_group_data)
    pairs = _draw_pairs_1v2(winners, runners)

    used = _collect_used_pic_indices()
    _prepare_round4_folder()

    for idx, ((g1, t1), (g2, t2)) in enumerate(pairs, start=1):
        p1 = _pick_fresh_pic_index(t1, used.get(t1, set()))
        used.setdefault(t1, set()).add(p1)
        p2 = _pick_fresh_pic_index(t2, used.get(t2, set()))
        used.setdefault(t2, set()).add(p2)

        ext1 = _detect_pic_ext(t1, p1)
        ext2 = _detect_pic_ext(t2, p2)

        match_name = f"{idx}. {t1} VS {t2}"
        match_dir = os.path.join(GOLD_ROUND4_FIXTURE, match_name)
        os.makedirs(match_dir, exist_ok=True)

        src1 = os.path.join(PIC_SELECTION, t1, f"LeaguePIC_{p1}{ext1}")
        src2 = os.path.join(PIC_SELECTION, t2, f"LeaguePIC_{p2}{ext2}")
        dst1 = os.path.join(match_dir, f"LeaguePIC_{p1}{ext1}")
        dst2 = os.path.join(match_dir, f"LeaguePIC_{p2}(A){ext2}")
        copyfile(src1, dst1)
        copyfile(src2, dst2)

        print(f"Round4 #{idx}: ({g1}1) {t1} VS ({g2}2) {t2}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Create Gold Knockout Round 4 (16 Team)")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when Round 4 fixture already has data",
    )
    ns = ap.parse_args()
    try:
        create_gold_knockout_round4(force=ns.yes)
    except (CreateGoldKnockoutCancelled, ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
