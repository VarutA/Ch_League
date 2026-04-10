#!/usr/bin/env python3
"""
End-to-end smoke test with complex display names (seed_complex_name_rosters.py).

From repo root (GHL2):
  python3 Code/run_e2e_complex_names.py -y

Runs: Diamond / Gold / Silver / World pipelines (create → sim → cal → summary where applicable).
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_CODE_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from fixture_vs_sim import simulate_vs_in_folder
from Gold_paths import (
    GOLD_KNOCKOUT_STATE_ROOT,
    GOLD_RANK_SUMMARY,
    GOLD_ROUND1_FIXTURE,
    GOLD_ROUND2_FIXTURE,
    GOLD_ROUND3_FIXTURE,
    GOLD_ROUND4_FIXTURE,
)
from Silver_paths import CHARACTER_SILVER_MASTER, LEAGUE_SILVER_SWISS_FIXTURE
from World_Cup_lib import world_round_path


def _run(py: str, argv: list[str]) -> None:
    path = os.path.join(_CODE_DIR, py)
    cmd = [sys.executable, path] + argv
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=_REPO)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def _silver_team_count() -> int:
    if not os.path.isdir(CHARACTER_SILVER_MASTER):
        return 0
    n = 0
    for x in os.listdir(CHARACTER_SILVER_MASTER):
        if x in ("Thumbs.db", ".DS_Store") or x.startswith("."):
            continue
        if os.path.isdir(os.path.join(CHARACTER_SILVER_MASTER, x)):
            n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Confirm wiping rosters (seed) and league replaces (-y on subcommands)",
    )
    ns = p.parse_args()
    if not ns.yes:
        print("Pass -y to run (wipes Character D/G/S and Pic Selection for those leagues).")
        raise SystemExit(1)

    _run("seed_complex_name_rosters.py", ["-y"])

    # ---------- Diamond ----------
    _run("Diamond_League_Create.py", ["-y"])
    for w in range(1, 59):
        _run("simulate_diamond_scores.py", [str(w), "--seed", str(7000 + w)])
    _run("Diamond_League_Cal.py", [])
    _run("Diamond_Summary.py", [])

    # ---------- Gold ----------
    _run("Gold_Group_Create.py", ["-y"])
    _run("simulate_gold_all_group_weeks.py", ["--seed", "9001"])
    _run("Gold_Group_Cal.py", [])
    for pth in (GOLD_KNOCKOUT_STATE_ROOT, GOLD_RANK_SUMMARY):
        if os.path.isdir(pth):
            shutil.rmtree(pth)
    _run("Gold_Knockout_Create_Next.py", ["-y"])
    rounds = [GOLD_ROUND4_FIXTURE, GOLD_ROUND3_FIXTURE, GOLD_ROUND2_FIXTURE, GOLD_ROUND1_FIXTURE]
    for i, fx in enumerate(rounds):
        n = simulate_vs_in_folder(fx, seed=9100 + i)
        print(f"Gold knockout scored in {fx!r}: {n} match(es)")
        if i < len(rounds) - 1:
            _run("Gold_Knockout_Create_Next.py", ["-y"])
    _run("Gold_Summary.py", ["-y"])

    # ---------- Silver ----------
    _run("Silver_Create.py", ["-y"])
    nteams = _silver_team_count()
    max_r = int(math.ceil(math.log2(nteams))) if nteams >= 2 else 0
    for r in range(1, max_r + 1):
        rp = os.path.join(LEAGUE_SILVER_SWISS_FIXTURE, f"Round {r}")
        if os.path.isdir(rp):
            n = simulate_vs_in_folder(rp, seed=9200 + r)
            print(f"Silver Round {r}: scored {n} match(es)")
        if r < max_r:
            _run("Silver_Create_Next.py", [])
    _run("Silver_Cal.py", [])
    _run("Silver_Group_Summary.py", ["-y"])

    # ---------- World Cup ----------
    _run("World_Ranking_Simulate.py", ["-y", "--seed", "9300"])
    _run("World_Cup_Create.py", ["-y"])
    for ri in range(1, 9):
        pth = world_round_path(ri)
        n = simulate_vs_in_folder(pth, seed=9400 + ri)
        print(f"World Cup round {ri}: scored {n} match(es)")
        if ri < 8:
            _run("World_Cup_Next.py", [])
    _run("World_Cup_Summary.py", ["-y"])

    print("e2e_complex_names: OK (all steps exited 0).")


if __name__ == "__main__":
    main()
