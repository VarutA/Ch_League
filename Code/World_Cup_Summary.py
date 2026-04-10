"""
World Cup Summary: last-standing by league + Giant Slayer tiers.

Reads:
- World Cup/World Cup Fixture (all scored matches, every round)
- World Cup/World Cup Source/* (pre-tournament ranks: Diamond standing, Gold summary, Silver standing)
- World Cup/World Cup Character (which teams are in this tournament)

Writes:
- World Cup/World Cup Summary/
    Last Standing Silver
    Last Standing Gold
    Giant Slayer XL / L / M / S

League (Silver / Gold / Diamond) is inferred from **which Source snapshot lists the team**,
not from name prefixes like S_/G_/D_.

Giant Slayer uses snapshot ranks (e.g. Diamond 8 = 8th in Source Diamond League Standing).

Run:
  python3 Code/World_Cup_Summary.py
  python3 Code/World_Cup_Summary.py -y
"""
from __future__ import annotations

import os
import re
import shutil
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from World_paths import (
    WORLD_CUP_CHARACTER,
    WORLD_CUP_FIXTURE,
    WORLD_CUP_ROUND_FOLDERS,
    WORLD_CUP_SUMMARY,
    WORLD_SOURCE_DIAMOND_STANDING,
    WORLD_SOURCE_GOLD_SUMMARY,
    WORLD_SOURCE_SILVER_STANDING,
)
from World_Cup_lib import (
    listdir_skip_junk,
    match_dirs,
    parse_scored_world_match,
    world_round_path,
)

# Team name may contain spaces; stop before first " [" (stats block).
_STANDING_RANK_RE = re.compile(r"^(\d+)\.\s+(.+?)\s+\[")
_GOLD_SUMMARY_RE = re.compile(r"^(\d+)\.\s+\([^)]+\)\s+(.+)$")


class WorldCupSummaryCancelled(Exception):
    """User declined replacing existing World Cup Summary."""


def _summary_category_dirs() -> list[str]:
    return [
        os.path.join(WORLD_CUP_SUMMARY, "Last Standing Silver"),
        os.path.join(WORLD_CUP_SUMMARY, "Last Standing Gold"),
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer XL"),
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer L"),
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer M"),
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer S"),
    ]


def _summary_has_content() -> bool:
    for p in _summary_category_dirs():
        if os.path.isdir(p) and listdir_skip_junk(p):
            return True
    return False


def _confirm_replace(force: bool) -> None:
    if not _summary_has_content():
        return
    if force:
        return
    if not sys.stdin.isatty():
        raise RuntimeError(
            "World Cup Summary already has data; refusing without confirmation. "
            "Use a terminal or pass -y."
        )
    print("World Cup Summary folders will be cleared and rebuilt.")
    ans = input("Replace? [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        raise WorldCupSummaryCancelled("Cancelled; World Cup Summary kept.")


def _load_diamond_ranks(root: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in listdir_skip_junk(root):
        m = _STANDING_RANK_RE.match(name)
        if m:
            out[m.group(2).strip()] = int(m.group(1))
    return out


def _load_silver_ranks(root: str) -> dict[str, int]:
    return _load_diamond_ranks(root)


def _load_gold_ranks(root: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in listdir_skip_junk(root):
        m = _GOLD_SUMMARY_RE.match(name)
        if m:
            out[m.group(2).strip()] = int(m.group(1))
    return out


def _short_id(team: str) -> str:
    """Display id in Giant Slayer lines; strip legacy S_/G_/D_ prefix if present."""
    if len(team) >= 2 and team[1] == "_" and team[0] in "SGD":
        return team[2:]
    return team


class SourceIndex:
    """Maps team name -> league + seed rank from World Cup Source copies."""

    __slots__ = ("dmap", "gmap", "smap")

    def __init__(
        self,
        dmap: dict[str, int],
        gmap: dict[str, int],
        smap: dict[str, int],
    ) -> None:
        self.dmap = dmap
        self.gmap = gmap
        self.smap = smap

    def league(self, team: str) -> str | None:
        if team in self.dmap:
            return "Diamond"
        if team in self.gmap:
            return "Gold"
        if team in self.smap:
            return "Silver"
        return None

    def rank(self, team: str) -> int | None:
        if team in self.dmap:
            return self.dmap[team]
        if team in self.gmap:
            return self.gmap[team]
        if team in self.smap:
            return self.smap[team]
        return None


def _winner_loser_goals(pm: dict[str, str | int]) -> tuple[int, int]:
    w = str(pm["winner"])
    s1 = int(pm["s1"])
    s2 = int(pm["s2"])
    left = str(pm["left"])
    if w == left:
        return s1, s2
    return s2, s1


def _giant_slayer_category(
    winner: str,
    loser: str,
    idx: SourceIndex,
) -> str | None:
    wl = idx.league(winner)
    ll = idx.league(loser)
    if wl is None or ll is None:
        return None
    lr = idx.rank(loser)
    if lr is None:
        return None

    if wl == "Silver" and ll == "Diamond" and 1 <= lr <= 8:
        return "XL"
    if wl == "Silver" and ll == "Diamond" and 9 <= lr <= 16:
        return "L"
    if wl == "Gold" and ll == "Diamond" and 1 <= lr <= 8:
        return "L"
    if wl == "Silver" and ll == "Diamond" and 17 <= lr <= 30:
        return "M"
    if wl == "Gold" and ll == "Diamond" and 9 <= lr <= 16:
        return "M"
    if wl == "Silver" and ll == "Gold":
        return "S"
    if wl == "Gold" and ll == "Diamond" and 17 <= lr <= 30:
        return "S"
    return None


def _fmt_giant_slayer_line(
    winner: str,
    loser: str,
    idx: SourceIndex,
    pm: dict[str, str | int],
) -> str:
    wr = idx.rank(winner)
    lr = idx.rank(loser)
    wg, lg_goals = _winner_loser_goals(pm)
    w_league = idx.league(winner)
    l_league = idx.league(loser)
    assert wr is not None and lr is not None and w_league and l_league
    return (
        f"{_short_id(winner)} ({w_league} {wr}) [{wg}-{lg_goals}] "
        f"{_short_id(loser)} ({l_league} {lr})"
    )


def _iter_scored_matches():
    for ri in range(1, len(WORLD_CUP_ROUND_FOLDERS) + 1):
        rp = world_round_path(ri)
        if not os.path.isdir(rp):
            continue
        for d in sorted(match_dirs(rp)):
            if " VS " in d:
                continue
            try:
                pm = parse_scored_world_match(d)
            except ValueError:
                continue
            yield ri, d, pm


def _max_round_per_team(wc_teams: set[str]) -> dict[str, int]:
    mx: dict[str, int] = {t: 0 for t in wc_teams}
    for ri, _d, pm in _iter_scored_matches():
        for side in (str(pm["left"]), str(pm["right"])):
            if side in mx:
                mx[side] = max(mx[side], ri)
    return mx


def _last_standing_lines(
    wc_teams: set[str],
    want_league: str,
    idx: SourceIndex,
    max_round: dict[str, int],
) -> list[str]:
    pool = [
        t
        for t in wc_teams
        if idx.league(t) == want_league and max_round.get(t, 0) > 0
    ]
    if not pool:
        return []
    best = max(max_round[t] for t in pool)
    lines = []
    for t in sorted(pool):
        if max_round[t] == best:
            lines.append(f"{t} [round {best}]")
    return lines


def _clear_category(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    for name in listdir_skip_junk(path):
        fp = os.path.join(path, name)
        if os.path.isdir(fp):
            shutil.rmtree(fp)
        else:
            os.remove(fp)


def _write_numbered_folders(category_dir: str, lines: list[str]) -> None:
    _clear_category(category_dir)
    for i, line in enumerate(lines, start=1):
        fp = os.path.join(category_dir, f"{i}. {line}")
        os.makedirs(fp, exist_ok=True)


def world_cup_summary(force: bool = False) -> None:
    _confirm_replace(force=force)

    if not os.path.isdir(WORLD_CUP_CHARACTER):
        raise FileNotFoundError(
            f"Missing World Cup Character: {WORLD_CUP_CHARACTER}. Run World_Cup_Create first."
        )
    for label, src in (
        ("Diamond snapshot", WORLD_SOURCE_DIAMOND_STANDING),
        ("Gold snapshot", WORLD_SOURCE_GOLD_SUMMARY),
        ("Silver snapshot", WORLD_SOURCE_SILVER_STANDING),
    ):
        if not os.path.isdir(src):
            raise FileNotFoundError(
                f"Missing {label} under World Cup Source (need create snapshot): {src}"
            )

    wc_teams = set()
    for name in listdir_skip_junk(WORLD_CUP_CHARACTER):
        p = os.path.join(WORLD_CUP_CHARACTER, name)
        if os.path.isdir(p):
            wc_teams.add(name)

    dmap = _load_diamond_ranks(WORLD_SOURCE_DIAMOND_STANDING)
    gmap = _load_gold_ranks(WORLD_SOURCE_GOLD_SUMMARY)
    smap = _load_silver_ranks(WORLD_SOURCE_SILVER_STANDING)
    idx = SourceIndex(dmap, gmap, smap)

    unmapped = [t for t in wc_teams if idx.league(t) is None]
    if unmapped:
        print(
            "WARNING: these World Cup teams are not in any Source snapshot "
            f"(check names match seeding): {unmapped[:20]}"
            + (" ..." if len(unmapped) > 20 else ""),
            file=sys.stderr,
        )

    max_round = _max_round_per_team(wc_teams)

    silver_lines = _last_standing_lines(wc_teams, "Silver", idx, max_round)
    gold_lines = _last_standing_lines(wc_teams, "Gold", idx, max_round)

    gs: dict[str, list[tuple[int, str, str]]] = {
        "XL": [],
        "L": [],
        "M": [],
        "S": [],
    }
    missing_rank = 0
    for ri, d, pm in _iter_scored_matches():
        w, l = str(pm["winner"]), str(pm["loser"])
        cat = _giant_slayer_category(w, l, idx)
        if cat is None:
            continue
        wr = idx.rank(w)
        lr = idx.rank(l)
        if wr is None or lr is None:
            missing_rank += 1
            continue
        line = _fmt_giant_slayer_line(w, l, idx, pm)
        gs[cat].append((ri, d, line))

    for k in gs:
        gs[k].sort(key=lambda x: (x[0], x[1]))
    if missing_rank:
        print(
            f"WARNING: skipped {missing_rank} giant-slayer candidate(s) with missing seed rank.",
            file=sys.stderr,
        )

    os.makedirs(WORLD_CUP_SUMMARY, exist_ok=True)
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Last Standing Silver"), silver_lines
    )
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Last Standing Gold"), gold_lines
    )
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer XL"),
        [t[2] for t in gs["XL"]],
    )
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer L"), [t[2] for t in gs["L"]]
    )
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer M"), [t[2] for t in gs["M"]]
    )
    _write_numbered_folders(
        os.path.join(WORLD_CUP_SUMMARY, "Giant Slayer S"), [t[2] for t in gs["S"]]
    )

    print("Last Standing Silver:")
    for x in silver_lines:
        print(f"  {x}")
    print("Last Standing Gold:")
    for x in gold_lines:
        print(f"  {x}")
    for label, key in (
        ("Giant Slayer XL", "XL"),
        ("Giant Slayer L", "L"),
        ("Giant Slayer M", "M"),
        ("Giant Slayer S", "S"),
    ):
        print(f"{label} ({len(gs[key])}):")
        for _r, _d, line in gs[key]:
            print(f"  {line}")

    print(f"world_cup_summary: wrote {WORLD_CUP_SUMMARY!r}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="World Cup Summary (last standing + Giant Slayer).")
    ap.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation when World Cup Summary already has data",
    )
    ns = ap.parse_args()
    try:
        world_cup_summary(force=ns.yes)
    except WorldCupSummaryCancelled as e:
        print(e)
        sys.exit(1)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(e)
        sys.exit(1)
