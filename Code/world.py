#!/usr/bin/env python3
"""
World Cup knockout helper (256 teams).

From repo root (GHL2):
  python3 Code/world.py create
  python3 Code/world.py create -y
  python3 Code/world.py next
  python3 Code/world.py ranking-sim
  python3 Code/world.py ranking-sim -y
  python3 Code/world.py summary
  python3 Code/world.py summary -y
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
        prog="world",
        description="World Cup (create / next / summary) and World Ranking simulate.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    cr = sub.add_parser("create", help="Create World Cup Round 1 (256 teams)")
    cr.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if World Cup folder already has data",
    )

    nx = sub.add_parser("next", help="Create next World Cup round through Final")

    wr = sub.add_parser(
        "ranking-sim",
        help="Build World Ranking from all Diamond/Gold/Silver characters (random rank & points)",
    )
    wr.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if World Ranking folder already has data",
    )
    wr.add_argument("--seed", type=int, default=None, help="Optional RNG seed")

    sm = sub.add_parser(
        "summary",
        help="Last Standing (Silver/Gold) + Giant Slayer XL/L/M/S from fixtures + Source snapshot",
    )
    sm.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation if World Cup Summary already has data",
    )

    args = p.parse_args()
    if args.cmd == "create":
        return _run("World_Cup_Create.py", ["-y"] if args.yes else [])
    if args.cmd == "next":
        return _run("World_Cup_Next.py", [])
    if args.cmd == "ranking-sim":
        a = ["-y"] if args.yes else []
        if args.seed is not None:
            a.extend(["--seed", str(args.seed)])
        return _run("World_Ranking_Simulate.py", a)
    if args.cmd == "summary":
        return _run("World_Cup_Summary.py", ["-y"] if args.yes else [])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
