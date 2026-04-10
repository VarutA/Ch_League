"""
Diamond league awards: fill League Diamond award folders from season stats.

Reads scored matches under Diamond League Fixture (same span as Diamond_League_Cal:
weeks 1..last complete week).

- UCL Champion, UEL Champion, Honorable I–V: clear folder (keep empty).
- The Golden Boots (Highest Score): highest total goals scored (g1).
- The Golden Gloves (Lowest Concede): lowest total goals conceded (g2).
- The Golden Record (Highest Diff): highest goal difference (g1 - g2).
- The Godlike Streak (Winstreak): longest consecutive wins (chronological).
- The Great Invincibles (Unbeatable): longest consecutive unbeaten (W or T).

Copies Character/Character Diamond/<team> into each stat award folder as a single subfolder named
``<team> [<stats>]`` (e.g. ``D_xxx [299 goals]``).
If the award stat is tied, the team with the better league table position wins (same order as
Diamond_League_Cal: points, goal difference, goals for, then name).

Console lines append extra totals (e.g. goals) for that team in the scanned weeks.
"""
from __future__ import annotations

import os
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Diamond_League_Cal import last_complete_diamond_week, list_diamond_characters
from match_folder_parse import try_parse_scored_match_folder_name
from Diamond_paths import (
    CHARACTER_DIAMOND_MASTER,
    DIAMOND_FIXTURE_MAX_WEEK,
    LEAGUE_DIAMOND_FIXTURE,
)

_LEAGUE_DIAMOND_ROOT = os.path.dirname(LEAGUE_DIAMOND_FIXTURE)

# Folder names under League Diamond (must match on-disk folders).
_AWARD_EMPTY = [
    "UCL Champion",
    "UEL Champion",
    "The Honorable I Goddess",
    "The Honorable II Queen",
    "The Honorable III Waife",
    "The Honorable IV Girlfriend",
    "The Honorable V Sister",
]

_AWARD_GOLDEN_BOOTS = "The Golden Boots (Highest Score)"
_AWARD_GOLDEN_GLOVES = "The Golden Gloves (Lowest Concede)"
_AWARD_GOLDEN_RECORD = "The Golden Record (Highest Diff)"
_AWARD_WINSTREAK = "The Godlike Streak (Winstreak)"
_AWARD_INVINCIBLE = "The Great Invincibles (Unbeatable)"


def _listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        out.append(name)
    return out


def _match_sort_key(folder_name: str) -> tuple[int, str]:
    if ". " not in folder_name:
        return (0, folder_name)
    head = folder_name.split(". ", 1)[0]
    try:
        return (int(head), folder_name)
    except ValueError:
        return (0, folder_name)


def _parse_scored_match(name: str) -> tuple[str, int, int, str] | None:
    parsed = try_parse_scored_match_folder_name(name)
    if not parsed:
        return None
    _i, left, s1, s2, right = parsed
    return left, s1, s2, right


def _iter_matches_chronological(last_week: int):
    for w in range(1, last_week + 1):
        week_path = os.path.join(LEAGUE_DIAMOND_FIXTURE, f"week {w}")
        if not os.path.isdir(week_path):
            continue
        subs = [
            x
            for x in _listdir_skip_junk(week_path)
            if os.path.isdir(os.path.join(week_path, x))
        ]
        for folder in sorted(subs, key=_match_sort_key):
            if " VS " in folder:
                continue
            p = _parse_scored_match(folder)
            if p is None:
                continue
            yield w, p[0], p[1], p[2], p[3]


def _clear_award_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    for name in _listdir_skip_junk(path):
        fp = os.path.join(path, name)
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)


def _copy_character_folder(team: str, award_dir: str, stats_inner: str) -> None:
    """
    Copy master character folder to award_dir/<team> [<stats_inner>].
    stats_inner is the text inside the brackets (no outer [ ]).
    """
    src = os.path.join(CHARACTER_DIAMOND_MASTER, team)
    if not os.path.isdir(src):
        raise FileNotFoundError(f"Missing master character folder for {team!r}: {src}")
    folder_name = f"{team} [{stats_inner}]"
    dst = os.path.join(award_dir, folder_name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _league_points_from_outcomes(seq: list[str]) -> int:
    w = sum(1 for o in seq if o == "W")
    t = sum(1 for o in seq if o == "T")
    return 3 * w + t


def _standing_sort_key_team(
    t: str, gf: dict[str, int], ga: dict[str, int], outcomes: dict[str, list[str]]
) -> tuple[int, int, int, str]:
    """Same tie-break order as Diamond_League_Cal (best = sort smallest)."""
    p = _league_points_from_outcomes(outcomes[t])
    gdd = gf[t] - ga[t]
    return (-p, -gdd, -gf[t], t)


def _standing_rank_map(
    teams: list[str], gf: dict[str, int], ga: dict[str, int], outcomes: dict[str, list[str]]
) -> dict[str, int]:
    """0 = league leader (best rank)."""
    ordered = sorted(teams, key=lambda t: _standing_sort_key_team(t, gf, ga, outcomes))
    return {team: i for i, team in enumerate(ordered)}


def _pick_max_tie_standing(names: list[str], key_fn, rank_map: dict[str, int]) -> str:
    mx = max(key_fn(n) for n in names)
    elig = [n for n in names if key_fn(n) == mx]
    return min(elig, key=lambda t: (rank_map[t], t))


def _pick_min_tie_standing(names: list[str], key_fn, rank_map: dict[str, int]) -> str:
    mn = min(key_fn(n) for n in names)
    elig = [n for n in names if key_fn(n) == mn]
    return min(elig, key=lambda t: (rank_map[t], t))


def _max_win_streak(outcomes: list[str]) -> int:
    cur = mx = 0
    for o in outcomes:
        if o == "W":
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def _max_unbeaten_streak(outcomes: list[str]) -> int:
    cur = mx = 0
    for o in outcomes:
        if o in ("W", "T"):
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def diamond_summary(week_cap: int | None = None) -> None:
    max_scan = DIAMOND_FIXTURE_MAX_WEEK if week_cap is None else min(int(week_cap), DIAMOND_FIXTURE_MAX_WEEK)
    last_week = last_complete_diamond_week(max_scan=max_scan)
    if last_week < 1:
        raise ValueError(
            "No complete Diamond week found; cannot build summary. "
            "Score all matches through at least week 1 first."
        )

    teams = list_diamond_characters()
    team_set = set(teams)
    gf = {t: 0 for t in teams}
    ga = {t: 0 for t in teams}
    outcomes: dict[str, list[str]] = {t: [] for t in teams}

    for w, left, s1, s2, right in _iter_matches_chronological(last_week):
        if left not in team_set or right not in team_set:
            continue
        gf[left] += s1
        ga[left] += s2
        gf[right] += s2
        ga[right] += s1
        if s1 > s2:
            outcomes[left].append("W")
            outcomes[right].append("L")
        elif s1 < s2:
            outcomes[left].append("L")
            outcomes[right].append("W")
        else:
            outcomes[left].append("T")
            outcomes[right].append("T")

    rank_map = _standing_rank_map(teams, gf, ga, outcomes)

    for name in _AWARD_EMPTY:
        p = os.path.join(_LEAGUE_DIAMOND_ROOT, name)
        _clear_award_folder(p)
        print(f"{name}: cleared (empty).")

    boots_dir = os.path.join(_LEAGUE_DIAMOND_ROOT, _AWARD_GOLDEN_BOOTS)
    _clear_award_folder(boots_dir)
    boots_winner = _pick_max_tie_standing(teams, lambda t: gf[t], rank_map)
    _copy_character_folder(boots_winner, boots_dir, f"{gf[boots_winner]} goals")
    print(
        f"{_AWARD_GOLDEN_BOOTS}: {boots_winner} — {gf[boots_winner]} goals"
    )

    gloves_dir = os.path.join(_LEAGUE_DIAMOND_ROOT, _AWARD_GOLDEN_GLOVES)
    _clear_award_folder(gloves_dir)
    gloves_winner = _pick_min_tie_standing(teams, lambda t: ga[t], rank_map)
    _copy_character_folder(
        gloves_winner, gloves_dir, f"{ga[gloves_winner]} goals conceded"
    )
    print(
        f"{_AWARD_GOLDEN_GLOVES}: {gloves_winner} — {ga[gloves_winner]} goals conceded"
    )

    record_dir = os.path.join(_LEAGUE_DIAMOND_ROOT, _AWARD_GOLDEN_RECORD)
    _clear_award_folder(record_dir)
    record_winner = _pick_max_tie_standing(teams, lambda t: gf[t] - ga[t], rank_map)
    gd = gf[record_winner] - ga[record_winner]
    _copy_character_folder(
        record_winner,
        record_dir,
        f"{gd:+d} goal diff",
    )
    print(
        f"{_AWARD_GOLDEN_RECORD}: {record_winner} — {gd:+d} goal diff"
    )

    streak_dir = os.path.join(_LEAGUE_DIAMOND_ROOT, _AWARD_WINSTREAK)
    _clear_award_folder(streak_dir)
    win_lengths = {t: _max_win_streak(outcomes[t]) for t in teams}
    streak_winner = _pick_max_tie_standing(teams, lambda t: win_lengths[t], rank_map)
    _copy_character_folder(
        streak_winner,
        streak_dir,
        f"{win_lengths[streak_winner]} win streak",
    )
    print(
        f"{_AWARD_WINSTREAK}: {streak_winner} — "
        f"{win_lengths[streak_winner]} win streak"
    )

    inv_dir = os.path.join(_LEAGUE_DIAMOND_ROOT, _AWARD_INVINCIBLE)
    _clear_award_folder(inv_dir)
    unb_lengths = {t: _max_unbeaten_streak(outcomes[t]) for t in teams}
    inv_winner = _pick_max_tie_standing(teams, lambda t: unb_lengths[t], rank_map)
    _copy_character_folder(
        inv_winner,
        inv_dir,
        f"{unb_lengths[inv_winner]} unbeaten run",
    )
    print(
        f"{_AWARD_INVINCIBLE}: {inv_winner} — "
        f"{unb_lengths[inv_winner]} unbeaten run"
    )

    print(
        f"diamond_summary: used weeks 1..{last_week} (max_scan={max_scan})."
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Diamond league award folders from season stats.")
    ap.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max week to scan (default: auto like Diamond_League_Cal)",
    )
    ns = ap.parse_args()
    try:
        diamond_summary(ns.week)
    except ValueError as e:
        print(e)
        sys.exit(1)
