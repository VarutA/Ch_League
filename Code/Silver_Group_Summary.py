"""
Silver league Swiss-stage awards (same three as Gold group-summary).

Stats come **only** from overall standing:
  League Silver/Silver League Standing

Does **not** use UCL/UEL, streak, unbeaten, or any knockout.

Awards (under League Silver/):
  - The Golden Boots (Highest Score)   -> most goals scored (g1)
  - The Golden Gloves (Lowest Concede) -> fewest goals conceded (g2)
  - The Golden Record (Highest Diff)   -> best goal difference (g1 - g2)

Ties: better overall rank in Silver League Standing wins (lower rank number = better).

Folder names for winners: ``<team> [<stats>]`` (e.g. ``S_xxx [32 goals]``).

Run:
  python3 Code/Silver_Group_Summary.py
  python3 Code/Silver_Group_Summary.py -y
"""
from __future__ import annotations

import os
import re
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from Silver_paths import CHARACTER_SILVER_MASTER, LEAGUE_SILVER_STANDING

_LEAGUE_SILVER_ROOT = os.path.dirname(LEAGUE_SILVER_STANDING)

_AWARD_GOLDEN_BOOTS = "The Golden Boots (Highest Score)"
_AWARD_GOLDEN_GLOVES = "The Golden Gloves (Lowest Concede)"
_AWARD_GOLDEN_RECORD = "The Golden Record (Highest Diff)"

# 1. Team Name [22pt] [30-13=+17] [7W-1T-0L]
_OVERALL_ROW_RE = re.compile(
    r"^(\d+)\.\s+(.+?)\s+\[(\d+)pt\]\s+"
    r"\[(\d+)-(\d+)=([+-]?\d+)\]\s+\[(\d+)W-(\d+)T-(\d+)L\]"
)


class SilverGroupSummaryCancelled(Exception):
    """User declined replacing existing Silver award folders."""


def _listdir_skip_junk(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    out: list[str] = []
    for name in os.listdir(path):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        out.append(name)
    return out


def _award_paths() -> list[str]:
    return [
        os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_BOOTS),
        os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_GLOVES),
        os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_RECORD),
    ]


def _silver_awards_have_content() -> bool:
    for p in _award_paths():
        if os.path.isdir(p) and _listdir_skip_junk(p):
            return True
    return False


def _confirm_replace(force: bool) -> None:
    if not _silver_awards_have_content():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Silver award folders already have data; refusing without confirmation. "
            "Use a terminal or pass -y."
        )
    print(
        "These folders will be cleared and refilled:\n"
        f"  {_AWARD_GOLDEN_BOOTS}\n"
        f"  {_AWARD_GOLDEN_GLOVES}\n"
        f"  {_AWARD_GOLDEN_RECORD}\n"
        "(under League Silver/)"
    )
    ans = input("Replace? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise SilverGroupSummaryCancelled("Cancelled; Silver award folders kept.")


def _parse_overall_standing_rows(standing_root: str) -> list[dict]:
    if not os.path.isdir(standing_root):
        raise FileNotFoundError(
            f"Missing Silver League Standing (run Silver_Cal first): {standing_root}"
        )
    rows: list[dict] = []
    for folder_name in _listdir_skip_junk(standing_root):
        if not os.path.isdir(os.path.join(standing_root, folder_name)):
            continue
        m = _OVERALL_ROW_RE.match(folder_name)
        if not m:
            continue
        rank = int(m.group(1))
        name = m.group(2).strip()
        g1 = int(m.group(4))
        g2 = int(m.group(5))
        rows.append(
            {
                "rank": rank,
                "name": name,
                "point": int(m.group(3)),
                "g1": g1,
                "g2": g2,
                "gd": g1 - g2,
            }
        )
    if len(rows) < 2:
        raise ValueError(
            f"Need parseable overall standing rows under {standing_root!r} "
            f"(format like '1. S_xxx [22pt] [30-13=+17] [7W-1T-0L]'). "
            f"Found {len(rows)}."
        )
    names = [r["name"] for r in rows]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate team name in Silver League Standing parse.")
    return rows


def _standing_rank_map(rows: list[dict]) -> dict[str, int]:
    """0 = best (overall rank 1)."""
    ordered = sorted(rows, key=lambda r: (r["rank"], r["name"]))
    return {r["name"]: i for i, r in enumerate(ordered)}


def _pick_max_tie_standing(names: list[str], key_fn, rank_map: dict[str, int]) -> str:
    mx = max(key_fn(n) for n in names)
    elig = [n for n in names if key_fn(n) == mx]
    return min(elig, key=lambda t: (rank_map[t], t))


def _pick_min_tie_standing(names: list[str], key_fn, rank_map: dict[str, int]) -> str:
    mn = min(key_fn(n) for n in names)
    elig = [n for n in names if key_fn(n) == mn]
    return min(elig, key=lambda t: (rank_map[t], t))


def _clear_award_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    for name in _listdir_skip_junk(path):
        fp = os.path.join(path, name)
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)


def _copy_character_folder(team: str, award_dir: str, stats_inner: str) -> None:
    src = os.path.join(CHARACTER_SILVER_MASTER, team)
    if not os.path.isdir(src):
        raise FileNotFoundError(f"Missing master character folder for {team!r}: {src}")
    folder_name = f"{team} [{stats_inner}]"
    dst = os.path.join(award_dir, folder_name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def silver_group_summary(force: bool = False) -> None:
    _confirm_replace(force=force)
    rows = _parse_overall_standing_rows(LEAGUE_SILVER_STANDING)
    teams = [r["name"] for r in rows]
    gf = {r["name"]: r["g1"] for r in rows}
    ga = {r["name"]: r["g2"] for r in rows}
    rank_map = _standing_rank_map(rows)

    boots_dir = os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_BOOTS)
    _clear_award_folder(boots_dir)
    boots_w = _pick_max_tie_standing(teams, lambda t: gf[t], rank_map)
    _copy_character_folder(boots_w, boots_dir, f"{gf[boots_w]} goals")
    print(f"{_AWARD_GOLDEN_BOOTS}: {boots_w} — {gf[boots_w]} goals")

    gloves_dir = os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_GLOVES)
    _clear_award_folder(gloves_dir)
    gloves_w = _pick_min_tie_standing(teams, lambda t: ga[t], rank_map)
    _copy_character_folder(gloves_w, gloves_dir, f"{ga[gloves_w]} goals conceded")
    print(f"{_AWARD_GOLDEN_GLOVES}: {gloves_w} — {ga[gloves_w]} goals conceded")

    record_dir = os.path.join(_LEAGUE_SILVER_ROOT, _AWARD_GOLDEN_RECORD)
    _clear_award_folder(record_dir)
    record_w = _pick_max_tie_standing(teams, lambda t: gf[t] - ga[t], rank_map)
    gd = gf[record_w] - ga[record_w]
    _copy_character_folder(record_w, record_dir, f"{gd:+d} goal diff")
    print(f"{_AWARD_GOLDEN_RECORD}: {record_w} — {gd:+d} goal diff")

    print(
        f"silver_group_summary: source={LEAGUE_SILVER_STANDING!r} ({len(rows)} teams)."
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Silver Swiss-stage awards from Silver League Standing only."
    )
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when award folders already have data",
    )
    ns = ap.parse_args()
    try:
        silver_group_summary(force=ns.yes)
    except SilverGroupSummaryCancelled as e:
        print(e)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
