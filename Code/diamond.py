#!/usr/bin/env python3
"""
Diamond league — one entrypoint for common commands.

Run from repo root (GHL2):
  python Code/diamond.py create
  python Code/diamond.py create -y
  python Code/diamond.py cal
  python Code/diamond.py cal 10
  python Code/diamond.py sim 3
  python Code/diamond.py sim 3 --seed 42
  python Code/diamond.py seed
  python Code/diamond.py seed --keep-templates
  python Code/diamond.py summary

Windows (cmd, from GHL2):  python Code\\diamond.py cal
Or:                        Code\\diamond.bat cal
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
    cmd = [sys.executable, path] + argv
    return subprocess.call(cmd, cwd=_REPO)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="diamond",
        description="Diamond league helper (create / cal / sim / seed / summary).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Build fixture from Character/Character Diamond")
    c.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip replace confirmation if League Diamond already has data",
    )

    cal = sub.add_parser("cal", help="Recalculate standings (Diamond League Standing)")
    cal.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max scan week (omit = auto)",
    )
    cal.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose cal output (per-match debug, each rename)",
    )

    s = sub.add_parser("sim", help="Random-score all VS matches in one week (testing)")
    s.add_argument("week", type=int)
    s.add_argument("--seed", type=int, default=None)

    sd = sub.add_parser("seed", help="Create 30 test characters + LeaguePIC images")
    sd.add_argument("--keep-templates", action="store_true")

    sm = sub.add_parser(
        "summary",
        help="Fill League Diamond award folders from season stats (Golden awards + clear UCL/UEL/Honorable)",
    )
    sm.add_argument(
        "week",
        nargs="?",
        type=int,
        default=None,
        metavar="N",
        help="Optional max scan week (default: auto)",
    )

    args = p.parse_args()

    if args.cmd == "create":
        return _run("Diamond_League_Create.py", ["-y"] if args.yes else [])
    if args.cmd == "cal":
        a: list[str] = []
        if args.week is not None:
            a.append(str(args.week))
        if args.verbose:
            a.append("--verbose")
        return _run("Diamond_League_Cal.py", a)
    if args.cmd == "sim":
        a = [str(args.week)]
        if args.seed is not None:
            a.extend(["--seed", str(args.seed)])
        return _run("simulate_diamond_scores.py", a)
    if args.cmd == "seed":
        return _run(
            "seed_diamond_characters.py",
            ["--keep-templates"] if args.keep_templates else [],
        )
    if args.cmd == "summary":
        return _run(
            "Diamond_Summary.py",
            [str(args.week)] if args.week is not None else [],
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
