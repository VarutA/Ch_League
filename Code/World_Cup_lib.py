"""Shared helpers for World Cup knockout (256 teams)."""
from __future__ import annotations

import os
import re
import shutil
import sys
from shutil import copyfile

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Diamond_paths import CHARACTER_DIAMOND_MASTER, LEAGUE_DIAMOND_STANDING
from Gold_paths import CHARACTER_GOLD_MASTER, GOLD_RANK_SUMMARY
from Silver_paths import CHARACTER_SILVER_MASTER, LEAGUE_SILVER_STANDING
from match_folder_parse import parse_scored_match_folder_name
from World_paths import (
    DIAMOND_PICK,
    GOLD_PICK,
    PIC_SELECTION,
    SILVER_PICK,
    WORLD_CUP_CHARACTER,
    WORLD_CUP_FIXTURE,
    WORLD_CUP_ROUND_FOLDERS,
    WORLD_CUP_SOURCE,
    WORLD_CUP_TEAM_TOTAL,
    WORLD_RANKING,
    WORLD_SOURCE_DIAMOND_STANDING,
    WORLD_SOURCE_GOLD_SUMMARY,
    WORLD_SOURCE_RANKING_PRE_TOURNAMENT,
    WORLD_SOURCE_SILVER_STANDING,
)


class CreateWorldCupCancelled(Exception):
    """User declined replacing existing World Cup data."""

_DS_STANDING_RE = re.compile(r"^(\d+)\.\s+(.+?)\s+\[")
_GOLD_SUMMARY_RE = re.compile(r"^(\d+)\.\s+\([^)]+\)\s+(.+)$")
_PIC_INDEX_RE = re.compile(r"LeaguePIC_(\d+)")


def listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        out.append(name)
    return out


def match_dirs(fixture_root: str) -> list[str]:
    if not os.path.isdir(fixture_root):
        return []
    return [
        x
        for x in listdir_skip_junk(fixture_root)
        if os.path.isdir(os.path.join(fixture_root, x))
    ]


def round_has_matches(fixture_root: str) -> bool:
    return len(match_dirs(fixture_root)) > 0


def round_is_complete(fixture_root: str) -> bool:
    subs = match_dirs(fixture_root)
    if not subs:
        return False
    for name in subs:
        if " VS " in name:
            return False
    return True


def world_round_path(round_index: int) -> str:
    """round_index: 1..8"""
    if round_index < 1 or round_index > len(WORLD_CUP_ROUND_FOLDERS):
        raise ValueError(f"Invalid world round index: {round_index}")
    return os.path.join(WORLD_CUP_FIXTURE, WORLD_CUP_ROUND_FOLDERS[round_index - 1])


def parse_diamond_standing_teams(standing_root: str, limit: int) -> list[str]:
    entries: list[tuple[int, str]] = []
    for name in listdir_skip_junk(standing_root):
        m = _DS_STANDING_RE.match(name)
        if not m:
            continue
        entries.append((int(m.group(1)), m.group(2).strip()))
    if entries:
        entries.sort(key=lambda x: (x[0], x[1]))
        teams = [t for _, t in entries]
        if len(teams) < limit:
            raise ValueError(
                f"Need at least {limit} ranked Diamond standing folders "
                f"(format like '1. D_xxx [3pt]...') under {standing_root!r}; "
                f"found {len(teams)} parseable."
            )
        return teams[:limit]

    master = set(listdir_skip_junk(CHARACTER_DIAMOND_MASTER))
    plain = sorted(
        n
        for n in listdir_skip_junk(standing_root)
        if os.path.isdir(os.path.join(standing_root, n)) and n in master
    )
    if len(plain) < limit:
        raise ValueError(
            f"Need at least {limit} Diamond teams under {standing_root!r} "
            f"(ranked folders from Diamond_League_Cal, or plain team folders "
            f"that exist in Character/Character Diamond); found {len(plain)}."
        )
    print(
        "WARNING: Diamond League Standing has no ranked folder names; "
        f"using alphabetical order of {limit} teams from that folder. "
        "Run Diamond_League_Cal for true ranks 1-30.",
        file=sys.stderr,
    )
    return plain[:limit]


def parse_silver_standing_teams(standing_root: str, limit: int) -> list[str]:
    entries: list[tuple[int, str]] = []
    for name in listdir_skip_junk(standing_root):
        m = _DS_STANDING_RE.match(name)
        if not m:
            continue
        entries.append((int(m.group(1)), m.group(2).strip()))
    if entries:
        entries.sort(key=lambda x: (x[0], x[1]))
        teams = [t for _, t in entries]
        if len(teams) < limit:
            raise ValueError(
                f"Need at least {limit} ranked Silver standing folders "
                f"(format like '1. S_xxx [3pt]...') under {standing_root!r}; "
                f"found {len(teams)} parseable."
            )
        return teams[:limit]

    master = set(listdir_skip_junk(CHARACTER_SILVER_MASTER))
    plain = sorted(
        n
        for n in listdir_skip_junk(standing_root)
        if os.path.isdir(os.path.join(standing_root, n)) and n in master
    )
    if len(plain) < limit:
        raise ValueError(
            f"Need at least {limit} Silver teams under {standing_root!r} "
            f"(ranked folders from Silver_Cal, or plain team folders in Character Silver); "
            f"found {len(plain)}."
        )
    print(
        "WARNING: Silver League Standing has no ranked folder names; "
        f"using alphabetical order of {limit} teams. Run Silver_Cal for ranks 1-{limit}.",
        file=sys.stderr,
    )
    return plain[:limit]


def parse_gold_summary_teams(summary_root: str, limit: int) -> list[str]:
    entries: list[tuple[int, str]] = []
    for name in listdir_skip_junk(summary_root):
        m = _GOLD_SUMMARY_RE.match(name)
        if not m:
            continue
        entries.append((int(m.group(1)), m.group(2).strip()))
    entries.sort(key=lambda x: (x[0], x[1]))
    teams = [t for _, t in entries]
    if len(teams) < limit:
        raise ValueError(
            f"Need at least {limit} Gold summary entries under {summary_root!r}; "
            f"found {len(teams)} parseable folders."
        )
    return teams[:limit]


def collect_world_cup_teams(
    diamond_standing: str = LEAGUE_DIAMOND_STANDING,
    gold_summary: str = GOLD_RANK_SUMMARY,
    silver_standing: str = LEAGUE_SILVER_STANDING,
) -> tuple[list[str], list[str], list[str]]:
    if not os.path.isdir(diamond_standing):
        raise FileNotFoundError(f"Missing Diamond standing: {diamond_standing}")
    if not os.path.isdir(gold_summary):
        raise FileNotFoundError(f"Missing Gold rank summary: {gold_summary}")
    if not os.path.isdir(silver_standing):
        raise FileNotFoundError(f"Missing Silver standing: {silver_standing}")

    d = parse_diamond_standing_teams(diamond_standing, DIAMOND_PICK)
    g = parse_gold_summary_teams(gold_summary, GOLD_PICK)
    s = parse_silver_standing_teams(silver_standing, SILVER_PICK)

    all_teams = d + g + s
    if len(all_teams) != WORLD_CUP_TEAM_TOTAL:
        raise ValueError(
            f"Internal error: expected {WORLD_CUP_TEAM_TOTAL} teams, got {len(all_teams)}"
        )
    if len(set(all_teams)) != len(all_teams):
        raise ValueError("Duplicate team name across Diamond/Gold/Silver picks.")
    return d, g, s


def rmtree_if_exists(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)


def copy_source_snapshots() -> None:
    """Copy league outputs + World Ranking snapshot into World Cup/World Cup Source/."""
    os.makedirs(WORLD_CUP_SOURCE, exist_ok=True)
    rmtree_if_exists(WORLD_SOURCE_DIAMOND_STANDING)
    rmtree_if_exists(WORLD_SOURCE_GOLD_SUMMARY)
    rmtree_if_exists(WORLD_SOURCE_SILVER_STANDING)
    rmtree_if_exists(WORLD_SOURCE_RANKING_PRE_TOURNAMENT)
    shutil.copytree(LEAGUE_DIAMOND_STANDING, WORLD_SOURCE_DIAMOND_STANDING)
    shutil.copytree(GOLD_RANK_SUMMARY, WORLD_SOURCE_GOLD_SUMMARY)
    shutil.copytree(LEAGUE_SILVER_STANDING, WORLD_SOURCE_SILVER_STANDING)
    if not os.path.isdir(WORLD_RANKING):
        raise FileNotFoundError(
            f"Missing World Ranking folder: {WORLD_RANKING}. "
            "Run World_Ranking_Simulate.py (or: python3 Code/world.py ranking-sim -y) first."
        )
    shutil.copytree(WORLD_RANKING, WORLD_SOURCE_RANKING_PRE_TOURNAMENT)


def _find_master_team_dir(team: str) -> str:
    for base in (CHARACTER_DIAMOND_MASTER, CHARACTER_GOLD_MASTER, CHARACTER_SILVER_MASTER):
        p = os.path.join(base, team)
        if os.path.isdir(p):
            return p
    raise FileNotFoundError(
        f"Team {team!r} not found under Character Diamond / Gold / Silver masters."
    )


def copy_world_cup_characters(teams: list[str]) -> None:
    rmtree_if_exists(WORLD_CUP_CHARACTER)
    os.makedirs(WORLD_CUP_CHARACTER, exist_ok=True)
    for t in teams:
        src = _find_master_team_dir(t)
        dst = os.path.join(WORLD_CUP_CHARACTER, t)
        shutil.copytree(src, dst)


def collect_used_world_pic_indices() -> dict[str, set[int]]:
    used: dict[str, set[int]] = {}

    def add_file(team: str, filename: str) -> None:
        m = _PIC_INDEX_RE.search(filename)
        if not m:
            return
        idx = int(m.group(1))
        used.setdefault(team, set()).add(idx)

    if not os.path.isdir(WORLD_CUP_FIXTURE):
        return used
    for rnd in listdir_skip_junk(WORLD_CUP_FIXTURE):
        rnd_path = os.path.join(WORLD_CUP_FIXTURE, rnd)
        if not os.path.isdir(rnd_path):
            continue
        for match in listdir_skip_junk(rnd_path):
            mdir = os.path.join(rnd_path, match)
            if not os.path.isdir(mdir):
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
            for f in listdir_skip_junk(mdir):
                if "(A)" in f:
                    add_file(right, f)
                else:
                    add_file(left, f)
    return used


def available_pic_indices_for_team(team: str) -> set[int]:
    root = os.path.join(PIC_SELECTION, team)
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Missing pic folder for team {team!r}: {root}")
    out: set[int] = set()
    for f in listdir_skip_junk(root):
        m = _PIC_INDEX_RE.search(f)
        if m:
            out.add(int(m.group(1)))
    return out


def pick_fresh_pic_index(team: str, used_indices: set[int]) -> int:
    available = available_pic_indices_for_team(team)
    if len(available) < 8:
        raise ValueError(
            f"Team {team} has only {len(available)} distinct LeaguePIC files; "
            "need at least 8 for World Cup knockout."
        )
    remaining = sorted(available - used_indices)
    if not remaining:
        raise ValueError(
            f"No unused LeaguePIC left for team {team}. Used={len(used_indices)}."
        )
    return remaining[0]


def detect_pic_ext(team: str, idx: int) -> str:
    base = f"LeaguePIC_{idx}"
    root = os.path.join(PIC_SELECTION, team)
    for ext in (".jpg", ".gif", ".png", ".jpeg", ".bmp"):
        full = os.path.join(root, base + ext)
        if os.path.isfile(full):
            return ext
    raise FileNotFoundError(f"Missing LeaguePIC_{idx} for team {team} in {root}")


def write_pair_match(
    match_index: int,
    t1: str,
    t2: str,
    out_dir: str,
    used: dict[str, set[int]],
) -> None:
    p1 = pick_fresh_pic_index(t1, used.get(t1, set()))
    used.setdefault(t1, set()).add(p1)
    p2 = pick_fresh_pic_index(t2, used.get(t2, set()))
    used.setdefault(t2, set()).add(p2)

    ext1 = detect_pic_ext(t1, p1)
    ext2 = detect_pic_ext(t2, p2)
    match_name = f"{match_index}. {t1} VS {t2}"
    match_dir = os.path.join(out_dir, match_name)
    os.makedirs(match_dir, exist_ok=True)

    src1 = os.path.join(PIC_SELECTION, t1, f"LeaguePIC_{p1}{ext1}")
    src2 = os.path.join(PIC_SELECTION, t2, f"LeaguePIC_{p2}{ext2}")
    dst1 = os.path.join(match_dir, f"LeaguePIC_{p1}{ext1}")
    dst2 = os.path.join(match_dir, f"LeaguePIC_{p2}(A){ext2}")
    copyfile(src1, dst1)
    copyfile(src2, dst2)


def parse_scored_match_winner(folder_name: str) -> str:
    return parse_scored_world_match(folder_name)["winner"]


def parse_scored_world_match(folder_name: str) -> dict[str, str | int]:
    """Parse a scored knockout folder name: ``N. TeamA x-y TeamB`` (multi-digit scores ok)."""
    _idx, left, s1, s2, right = parse_scored_match_folder_name(folder_name)
    if s1 == s2:
        raise ValueError(
            f"Draw score {s1}-{s2} not allowed for knockout winner: {folder_name!r}"
        )
    winner = left if s1 > s2 else right
    loser = right if s1 > s2 else left
    return {
        "left": left,
        "right": right,
        "s1": s1,
        "s2": s2,
        "winner": winner,
        "loser": loser,
    }


def winners_from_completed_round(round_path: str) -> list[str]:
    winners: list[str] = []
    for d in sorted(match_dirs(round_path)):
        if " VS " in d:
            raise ValueError(f"Round not fully scored: {d!r}")
        winners.append(parse_scored_match_winner(d))
    return winners


def world_cup_has_any_data() -> bool:
    if os.path.isdir(WORLD_CUP_FIXTURE) and listdir_skip_junk(WORLD_CUP_FIXTURE):
        return True
    if os.path.isdir(WORLD_CUP_CHARACTER) and listdir_skip_junk(WORLD_CUP_CHARACTER):
        return True
    if os.path.isdir(WORLD_CUP_SOURCE) and listdir_skip_junk(WORLD_CUP_SOURCE):
        return True
    return False


def confirm_replace_world_cup(force: bool) -> None:
    if not world_cup_has_any_data():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "World Cup folder already has data; refusing to replace without confirmation. "
            "Use a terminal prompt or pass -y."
        )
    print(
        "World Cup folder already has data (Source / Character / Fixture).\n"
        "This will DELETE and rebuild from current Diamond/Gold/Silver standings."
    )
    ans = input("Replace World Cup? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise CreateWorldCupCancelled("Cancelled; existing World Cup data kept.")


def prepare_fresh_fixture_root() -> None:
    rmtree_if_exists(WORLD_CUP_FIXTURE)
    os.makedirs(WORLD_CUP_FIXTURE, exist_ok=True)
