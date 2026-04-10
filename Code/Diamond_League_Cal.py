"""
Diamond league: standings from completed fixtures (legacy rank_cal logic).
Reads: League Diamond/Diamond League Fixture (project root)
Renames entries in: League Diamond/Diamond League Standing
Character IDs from: Character/Character Diamond (project root)
"""
import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from match_folder_parse import parse_scored_match_folder_name
from standing_folder_parse import (
    map_standing_filenames_to_teams,
    parse_diamond_or_gold_group_standing_team,
)

from Diamond_paths import (
    CHARACTER_DIAMOND_MASTER,
    DIAMOND_FIXTURE_MAX_WEEK,
    LEAGUE_DIAMOND_FIXTURE,
    LEAGUE_DIAMOND_STANDING,
)


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
    return _listdir_skip_junk(CHARACTER_DIAMOND_MASTER)


def _week_is_complete(week_path):
    """True if folder exists, has at least one match dir, and every match is scored (no ' VS ')."""
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


def last_complete_diamond_week(max_scan=None):
    """
    Walk week 1, 2, ... up to `max_scan` (default: DIAMOND_FIXTURE_MAX_WEEK, e.g. 58).
    Stop at the first week that is missing or not fully scored (any match folder still has ' VS ').
    Returns the last fully complete week index, or 0 if week 1 is not complete.
    """
    if max_scan is None:
        max_scan = DIAMOND_FIXTURE_MAX_WEEK
    path_league = LEAGUE_DIAMOND_FIXTURE
    last = 0
    for w in range(1, max_scan + 1):
        week_path = os.path.join(path_league, "week {}".format(w))
        if not _week_is_complete(week_path):
            break
        last = w
    return last


def diamond_league_cal(week=None, verbose=False):
    """
    Replace legacy rank_cal: same parsing and standing renames.
    Order: points desc, goal difference desc, goals for desc, then name (stable).

    Scans from week 1 upward. Stops at the first incomplete week (or missing week folder);
    standings use only weeks 1..W where W is that last complete week (never skips ahead).

    `week`: optional cap on how far to scan (min with DIAMOND_FIXTURE_MAX_WEEK). None = scan up to
    DIAMOND_FIXTURE_MAX_WEEK (58).

    `verbose`: if True, print per-match debug lines and each standing rename (legacy noise).
    """
    max_scan = DIAMOND_FIXTURE_MAX_WEEK if week is None else min(int(week), DIAMOND_FIXTURE_MAX_WEEK)
    last_week = last_complete_diamond_week(max_scan=max_scan)
    if last_week < 1:
        raise ValueError(
            "No complete week found under {!r} within 1..{}: week 1 must exist and every "
            "match subfolder must be scored (no ' VS ' in names).".format(
                LEAGUE_DIAMOND_FIXTURE, max_scan
            )
        )
    path_league = LEAGUE_DIAMOND_FIXTURE
    list_character = list_diamond_characters()

    name_data = {}

    for name in list_character:
        name_data[name] = {}
        name_data[name]["point"] = 0
        name_data[name]["g1"] = 0
        name_data[name]["g2"] = 0
        name_data[name]["g3"] = 0
        name_data[name]["W"] = 0
        name_data[name]["T"] = 0
        name_data[name]["L"] = 0

    i = 1
    while i <= last_week:
        week_text = "week {}".format(i)
        week_path = os.path.join(path_league, week_text)
        dirs = _listdir_skip_junk(week_path)

        for file_full in dirs:
            if " VS " in file_full:
                continue
            if ". " not in file_full:
                continue
            try:
                _idx, t1, s1, s2, t2 = parse_scored_match_folder_name(file_full)
            except ValueError:
                continue
            if t1 not in name_data or t2 not in name_data:
                continue
            if verbose:
                print(file_full, "->", t1, s1, s2, t2)
            if s1 > s2:
                name_data[t1]["g1"] += s1
                name_data[t1]["g2"] += s2
                name_data[t1]["point"] += 3
                name_data[t1]["W"] += 1
                name_data[t2]["g1"] += s2
                name_data[t2]["g2"] += s1
                name_data[t2]["L"] += 1
            elif s1 < s2:
                name_data[t2]["g1"] += s2
                name_data[t2]["g2"] += s1
                name_data[t2]["point"] += 3
                name_data[t2]["W"] += 1
                name_data[t1]["g1"] += s1
                name_data[t1]["g2"] += s2
                name_data[t1]["L"] += 1
            else:
                name_data[t1]["g1"] += s1
                name_data[t1]["g2"] += s2
                name_data[t1]["point"] += 1
                name_data[t1]["T"] += 1
                name_data[t2]["g1"] += s2
                name_data[t2]["g2"] += s1
                name_data[t2]["point"] += 1
                name_data[t2]["T"] += 1

        i = i + 1

    def _standing_sort_key(n):
        d = name_data[n]
        gd = d["g1"] - d["g2"]
        return (-d["point"], -gd, -d["g1"], n)

    data_list = sorted(name_data.keys(), key=_standing_sort_key)

    standing_path = LEAGUE_DIAMOND_STANDING
    if not os.path.isdir(standing_path):
        os.makedirs(standing_path, exist_ok=True)
    dirs = _listdir_skip_junk(standing_path)
    team_set = set(name_data.keys())
    team_file = map_standing_filenames_to_teams(
        dirs, team_set, parser=parse_diamond_or_gold_group_standing_team
    )
    renamed = 0
    for idx, name in enumerate(data_list, start=1):
        file = team_file.pop(name, None)
        if file is None:
            continue
        sc = name_data[name]["g1"] - name_data[name]["g2"]
        if sc > 0:
            sc = "+" + str(sc)
        elif sc < 0:
            sc = "-" + str(abs(sc))
        else:
            sc = str(sc)
        stat = "[{}W-{}T-{}L]".format(
            name_data[name]["W"],
            name_data[name]["T"],
            name_data[name]["L"],
        )
        title = (
            str(idx)
            + ". "
            + name
            + " ["
            + str(name_data[name]["point"])
            + "pt] ["
            + str(name_data[name]["g1"])
            + "-"
            + str(name_data[name]["g2"])
            + "="
            + sc
            + "] "
            + stat
        )
        if verbose:
            print(
                os.path.join(standing_path, file),
                os.path.join(standing_path, title),
            )
        os.rename(
            os.path.join(standing_path, file),
            os.path.join(standing_path, title),
        )
        renamed += 1

    print(
        "diamond_league_cal: weeks 1..{} (max_scan={}); renamed {} standing folder(s).".format(
            last_week, max_scan, renamed
        )
    )

    return name_data


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Diamond league standings.")
    ap.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max scan week (default: auto 1..58 until first incomplete)",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-match debug and each rename (legacy verbose output)",
    )
    ns = ap.parse_args()
    try:
        diamond_league_cal(ns.week, verbose=ns.verbose)
    except ValueError as e:
        print(e)
        sys.exit(1)
