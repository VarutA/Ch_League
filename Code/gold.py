#!/usr/bin/env python3
"""
Gold league helper (group stage for now).

Run from repo root (GHL2):
  python Code/gold.py group-create
  python Code/gold.py group-create -y
  python Code/gold.py group-cal
  python Code/gold.py group-cal --group A
  python Code/gold.py group-cal --group A 5
  python Code/gold.py group-sim
  python Code/gold.py group-sim --seed 42
  python Code/gold.py knockout-create
  python Code/gold.py knockout-create -y
  python Code/gold.py knockout3-create
  python Code/gold.py knockout3-create -y
  python Code/gold.py knockout2-create
  python Code/gold.py knockout2-create -y
  python Code/gold.py knockout1-create
  python Code/gold.py knockout1-create -y
  python Code/gold.py knockout-next
  python Code/gold.py knockout-next -y
  python Code/gold.py summary
  python Code/gold.py summary -y
  python Code/gold.py group-summary
  python Code/gold.py group-summary -y
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

_CODE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_CODE)


def _run(script: str, argv: list[str]) -> int:
    path = os.path.join(_CODE, script)
    return subprocess.call([sys.executable, path] + argv, cwd=_REPO)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="gold",
        description="Gold league helper (group-create / group-cal / group-summary / knockout / summary).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    cg = sub.add_parser(
        "group-create",
        help="Create Gold Group Stage (A-H, 10 teams each, single round-robin)",
    )
    cg.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Gold Group Stage already has data",
    )

    gc = sub.add_parser(
        "group-cal",
        help="Calculate Gold group standings (all groups or one group)",
    )
    gc.add_argument(
        "--group",
        default=None,
        help="Group label A-H. Omit to run all groups.",
    )
    gc.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max scan week (default: auto 1..9 until first incomplete)",
    )

    gs = sub.add_parser(
        "group-sim",
        help="Random-score all VS matches in every group week A–H (testing)",
    )
    gs.add_argument("--seed", type=int, default=4242, help="Base RNG seed")

    kc = sub.add_parser(
        "knockout-create",
        help="Create Round 4 (16 Team) from group winners/runners",
    )
    kc.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Round 4 fixture already has data",
    )

    kn = sub.add_parser(
        "knockout-next",
        help="Auto-create next knockout round (R4 then R3 then R2 then R1)",
    )
    kn.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation when the next round folder already has data",
    )

    k3 = sub.add_parser(
        "knockout3-create",
        help="Create Round 3 (Quarter Final) from Round 4 winners",
    )
    k3.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Round 3 fixture already has data",
    )

    k2 = sub.add_parser(
        "knockout2-create",
        help="Create Round 2 (Semi Final) from Round 3 winners",
    )
    k2.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Round 2 fixture already has data",
    )

    k1 = sub.add_parser(
        "knockout1-create",
        help="Create Round 1 (Final) from Round 2 winners",
    )
    k1.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Round 1 fixture already has data",
    )

    sm = sub.add_parser(
        "summary",
        help="Create Gold rank summary folders from completed knockout results",
    )
    sm.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if Gold Rank Summary already has data",
    )

    gs = sub.add_parser(
        "group-summary",
        help="Golden Boots/Gloves/Record from Gold League Standing (group stage only, no knockout)",
    )
    gs.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if League Gold award folders already have data",
    )

    args = p.parse_args()
    if args.cmd == "group-create":
        return _run("Gold_Group_Create.py", ["-y"] if args.yes else [])
    if args.cmd == "group-cal":
        a = []
        if args.group is not None:
            a.extend(["--group", str(args.group)])
        if args.week is not None:
            a.append(str(args.week))
        return _run("Gold_Group_Cal.py", a)
    if args.cmd == "group-sim":
        a = ["--seed", str(args.seed)]
        return _run("simulate_gold_all_group_weeks.py", a)
    if args.cmd == "knockout-create":
        return _run("Gold_Knockout_Create_4.py", ["-y"] if args.yes else [])
    if args.cmd == "knockout-next":
        return _run("Gold_Knockout_Create_Next.py", ["-y"] if args.yes else [])
    if args.cmd == "knockout3-create":
        return _run("Gold_Knockout_Create_3.py", ["-y"] if args.yes else [])
    if args.cmd == "knockout2-create":
        return _run("Gold_Knockout_Create_2.py", ["-y"] if args.yes else [])
    if args.cmd == "knockout1-create":
        return _run("Gold_Knockout_Create_1.py", ["-y"] if args.yes else [])
    if args.cmd == "summary":
        return _run("Gold_Summary.py", ["-y"] if args.yes else [])
    if args.cmd == "group-summary":
        return _run("Gold_Group_Summary.py", ["-y"] if args.yes else [])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
