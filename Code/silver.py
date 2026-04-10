#!/usr/bin/env python3
"""
Silver league helper (Swiss fixture + group-style awards).

Run from repo root (GHL2):
  python Code/silver.py create
  python Code/silver.py create -y
  python Code/silver.py cal
  python Code/silver.py cal N
  python Code/silver.py group-summary
  python Code/silver.py group-summary -y
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
        prog="silver",
        description="Silver league helper (create / cal / group-summary).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    cr = sub.add_parser(
        "create",
        help="Create Swiss Round 1 from Character Silver",
    )
    cr.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if League Silver already has data",
    )

    cal = sub.add_parser(
        "cal",
        help="Calculate Silver Swiss standings from Swiss Fixture",
    )
    cal.add_argument(
        "round_cap",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max round to scan (default: auto until first incomplete).",
    )

    gs = sub.add_parser(
        "group-summary",
        help="Golden Boots/Gloves/Record from Silver League Standing (Swiss only, no UCL/UEL/streak)",
    )
    gs.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if League Silver award folders already have data",
    )

    args = p.parse_args()
    if args.cmd == "create":
        return _run("Silver_Create.py", ["-y"] if args.yes else [])
    if args.cmd == "cal":
        a = [] if args.round_cap is None else [str(args.round_cap)]
        return _run("Silver_Cal.py", a)
    if args.cmd == "group-summary":
        return _run("Silver_Group_Summary.py", ["-y"] if args.yes else [])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
