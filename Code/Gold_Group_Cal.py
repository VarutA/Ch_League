"""
Gold league group-stage standings calculator (A-H).

Reads:
- League Gold/Gold Group State/Group X Fixture

Renames standings entries in:
- League Gold/Gold Group State/Group X Standing
"""
import os
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from match_folder_parse import parse_scored_match_folder_name
from standing_folder_parse import (
    map_standing_filenames_to_teams,
    parse_diamond_or_gold_group_standing_team,
    parse_gold_overall_standing_team,
)
from Gold_paths import (
    GOLD_GROUP_FIXTURE_MAX_WEEK,
    GOLD_GROUP_LABELS,
    GOLD_GROUP_STATE_ROOT,
    LEAGUE_GOLD_CHARACTER,
    LEAGUE_GOLD_OVERALL_STANDING,
)


def _listdir_skip_junk(path):
    names = []
    if not os.path.isdir(path):
        return names
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        names.append(name)
    return names


def _fixture_root(group_label):
    return os.path.join(GOLD_GROUP_STATE_ROOT, f"Group {group_label} Fixture")


def _standing_root(group_label):
    return os.path.join(GOLD_GROUP_STATE_ROOT, f"Group {group_label} Standing")


def _week_is_complete(week_path):
    """True if folder exists, has match folders, and no pending ' VS ' names."""
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


def _normalize_group_label(group_label):
    if group_label is None:
        return None
    lab = str(group_label).strip().upper()
    if lab.startswith("GROUP "):
        lab = lab.replace("GROUP ", "", 1).strip()
    if lab not in GOLD_GROUP_LABELS:
        raise ValueError(
            f"Invalid group {group_label!r}. Expected one of: {', '.join(GOLD_GROUP_LABELS)}"
        )
    return lab


def _standing_sort_key_from_stats(name, stats):
    gd = stats["g1"] - stats["g2"]
    return (-stats["point"], -gd, -stats["g1"], name)


def _rank_names_from_data(name_data):
    return sorted(
        name_data.keys(),
        key=lambda n: _standing_sort_key_from_stats(n, name_data[n]),
    )


def last_complete_gold_group_week(group_label, max_scan=None):
    """
    Walk week 1..max_scan and stop at first incomplete/missing week.
    Return last complete week index, or 0.
    """
    label = _normalize_group_label(group_label)
    if max_scan is None:
        max_scan = GOLD_GROUP_FIXTURE_MAX_WEEK
    max_scan = min(int(max_scan), GOLD_GROUP_FIXTURE_MAX_WEEK)

    fixture = _fixture_root(label)
    last = 0
    for w in range(1, max_scan + 1):
        week_path = os.path.join(fixture, f"week {w}")
        if not _week_is_complete(week_path):
            break
        last = w
    return last


def last_complete_gold_global_week(max_scan=None):
    """
    Global complete week frontier across ALL groups A-H.

    Week w is considered complete only if Group A..H all have complete `week w`.
    Stops at first week where any group is incomplete/missing.
    """
    if max_scan is None:
        max_scan = GOLD_GROUP_FIXTURE_MAX_WEEK
    max_scan = min(int(max_scan), GOLD_GROUP_FIXTURE_MAX_WEEK)

    last = 0
    for w in range(1, max_scan + 1):
        ok = True
        for label in GOLD_GROUP_LABELS:
            week_path = os.path.join(_fixture_root(label), f"week {w}")
            if not _week_is_complete(week_path):
                ok = False
                break
        if not ok:
            break
        last = w
    return last


def _list_group_members(group_label):
    """
    Resolve canonical member names for one group, even if standing entries were
    already renamed to include stats/rank text.
    """
    label = _normalize_group_label(group_label)
    entries = _listdir_skip_junk(_standing_root(label))
    candidates = _listdir_skip_junk(LEAGUE_GOLD_CHARACTER)
    cand_set = set(candidates)

    members: list[str] = []
    seen: set[str] = set()
    for file in sorted(entries):
        team: str | None = None
        if file in cand_set:
            team = file
        else:
            parsed = parse_diamond_or_gold_group_standing_team(file)
            if parsed is not None and parsed in cand_set:
                team = parsed
        if team is not None and team not in seen:
            seen.add(team)
            members.append(team)
    return members


def _calc_group(group_label, week=None):
    label = _normalize_group_label(group_label)
    max_scan = GOLD_GROUP_FIXTURE_MAX_WEEK if week is None else min(
        int(week), GOLD_GROUP_FIXTURE_MAX_WEEK
    )
    last_week = last_complete_gold_group_week(label, max_scan=max_scan)
    if last_week < 1:
        raise ValueError(
            f"Group {label}: no complete week found within 1..{max_scan} "
            f"under {_fixture_root(label)!r}"
        )

    print(
        f"gold_group_cal[{label}]: counting weeks 1..{last_week} "
        f"(stopped before first incomplete; max_scan={max_scan})"
    )

    fixture_path = _fixture_root(label)
    standing_path = _standing_root(label)
    members = _list_group_members(label)
    if not members:
        raise ValueError(
            f"Group {label}: no standing members found under {standing_path!r}"
        )

    name_data = {}
    for name in members:
        name_data[name] = {
            "point": 0,
            "g1": 0,
            "g2": 0,
            "g3": 0,
            "W": 0,
            "T": 0,
            "L": 0,
        }

    i = 1
    while i <= last_week:
        week_path = os.path.join(fixture_path, f"week {i}")
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
        i += 1

    ranking = _rank_names_from_data(name_data)
    standing_entries = _listdir_skip_junk(standing_path)
    team_set = set(name_data.keys())
    team_file = map_standing_filenames_to_teams(
        standing_entries, team_set, parser=parse_diamond_or_gold_group_standing_team
    )

    for idx, name in enumerate(ranking, start=1):
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
        os.rename(
            os.path.join(standing_path, file),
            os.path.join(standing_path, title),
        )

    return name_data


def _rebuild_overall_standing_base():
    """
    Reset Gold League Standing from League Gold/Character Gold so names are clean
    before applying formatted rank titles.
    """
    if os.path.isdir(LEAGUE_GOLD_OVERALL_STANDING):
        shutil.rmtree(LEAGUE_GOLD_OVERALL_STANDING)
    os.makedirs(os.path.dirname(LEAGUE_GOLD_OVERALL_STANDING), exist_ok=True)
    if not os.path.isdir(LEAGUE_GOLD_CHARACTER):
        raise ValueError(
            f"Missing League Gold character copy: {LEAGUE_GOLD_CHARACTER!r}. "
            "Run group-create first."
        )
    shutil.copytree(LEAGUE_GOLD_CHARACTER, LEAGUE_GOLD_OVERALL_STANDING)


def _build_overall_entries(result_by_group):
    """
    Build combined table rows from each group's stats and group ranking.
    """
    entries = []
    for label in GOLD_GROUP_LABELS:
        name_data = result_by_group[label]
        group_ranking = _rank_names_from_data(name_data)
        for idx, name in enumerate(group_ranking, start=1):
            d = name_data[name]
            entries.append(
                {
                    "name": name,
                    "group": label,
                    "group_rank": idx,
                    "point": d["point"],
                    "g1": d["g1"],
                    "g2": d["g2"],
                    "W": d["W"],
                    "T": d["T"],
                    "L": d["L"],
                }
            )

    entries.sort(
        key=lambda e: (
            -e["point"],
            -(e["g1"] - e["g2"]),
            -e["g1"],
            e["group_rank"],
            e["group"],
            e["name"],
        )
    )
    return entries


def _write_overall_standing(entries):
    """
    Rename entries in Gold League Standing using combined ranking format:
    1. (1A) Name [12pt] [32-14=+18] [4W-0T-1L]
    """
    standing_path = LEAGUE_GOLD_OVERALL_STANDING
    listing = _listdir_skip_junk(standing_path)
    team_set = {e["name"] for e in entries}
    team_file = map_standing_filenames_to_teams(
        listing, team_set, parser=parse_gold_overall_standing_team
    )
    rank_no = 1
    for e in entries:
        name = e["name"]
        old_name = team_file.pop(name, None)
        if old_name is None:
            continue

        sc = e["g1"] - e["g2"]
        if sc > 0:
            sc_str = "+" + str(sc)
        elif sc < 0:
            sc_str = "-" + str(abs(sc))
        else:
            sc_str = "0"

        stat = f"[{e['W']}W-{e['T']}T-{e['L']}L]"
        group_pos = f"({e['group_rank']}{e['group']})"
        title = (
            f"{rank_no}. {group_pos} {name} "
            f"[{e['point']}pt] [{e['g1']}-{e['g2']}={sc_str}] {stat}"
        )
        os.rename(
            os.path.join(standing_path, old_name),
            os.path.join(standing_path, title),
        )
        rank_no += 1


def gold_group_cal(group=None, week=None):
    """
    Calculate standings for one group or all groups.

    - group=None -> run A..H with a shared week frontier:
      A w1 -> B w1 -> ... -> H w1 -> A w2 ... and stop when any group has pending VS
    - group='A'  -> run one group
    - week=None  -> auto stop at first incomplete week (up to max 9)
    """
    if group is None:
        max_scan = GOLD_GROUP_FIXTURE_MAX_WEEK if week is None else min(
            int(week), GOLD_GROUP_FIXTURE_MAX_WEEK
        )
        shared_last = last_complete_gold_global_week(max_scan=max_scan)
        if shared_last < 1:
            raise ValueError(
                "No globally complete week found across groups A-H within 1..{} "
                "(a week must be complete in every group).".format(max_scan)
            )
        print(
            "gold_group_cal[ALL]: shared weeks 1..{} across A-H "
            "(stop at first group with pending VS; max_scan={})".format(
                shared_last, max_scan
            )
        )
        result = {}
        for label in GOLD_GROUP_LABELS:
            result[label] = _calc_group(label, week=shared_last)
        _rebuild_overall_standing_base()
        overall_entries = _build_overall_entries(result)
        _write_overall_standing(overall_entries)
        print(
            f"gold_group_cal[ALL]: updated overall standing at "
            f"{LEAGUE_GOLD_OVERALL_STANDING}"
        )
        return result
    label = _normalize_group_label(group)
    return {label: _calc_group(label, week=week)}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Gold Group Stage standings (A-H)")
    ap.add_argument(
        "--group",
        default=None,
        help="Group label A-H. Omit to run all groups.",
    )
    ap.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max scan week (default: auto 1..9 until first incomplete)",
    )
    ns = ap.parse_args()
    try:
        gold_group_cal(group=ns.group, week=ns.week)
    except ValueError as e:
        print(e)
        sys.exit(1)
