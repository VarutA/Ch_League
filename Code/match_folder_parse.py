"""
Parse scored match folder names: ``<n>. <team_a> <s1>-<s2> <team_b>``.

Supports team names with ``.``, spaces, ``-``, digits (e.g. ``Ms. Valentine``,
``Moe-Kamiji``, ``Miyuki2``, ``Sumeragi Lee Noriega``).

The match index is separated by the *first* ``". "`` only (so ``Dr. Who`` in the
body is fine). The score is the first `` <int>-<int> `` substring in the remainder
(spaces required around the score token).
"""
from __future__ import annotations

import re
from typing import Optional

_SCORE_TOKEN_RE = re.compile(r"\s+(\d+)-(\d+)\s+")


def parse_scored_match_folder_name(folder_name: str) -> tuple[str, str, int, int, str]:
    """
    Returns ``(index_str, team_left, s1, s2, team_right)``.
    """
    if ". " not in folder_name:
        raise ValueError(
            f"Expected match folder with index prefix 'N. ': {folder_name!r}"
        )
    idx_str, body = folder_name.split(". ", 1)
    if not idx_str.isdigit():
        raise ValueError(f"Invalid match index in folder name: {folder_name!r}")
    m = _SCORE_TOKEN_RE.search(body)
    if not m:
        raise ValueError(f"Expected score '… N-N …' (spaces around score) in: {folder_name!r}")
    left = body[: m.start()].strip()
    right = body[m.end() :].strip()
    if not left or not right:
        raise ValueError(f"Empty team name after parsing: {folder_name!r}")
    s1, s2 = int(m.group(1)), int(m.group(2))
    return idx_str, left, s1, s2, right


def try_parse_scored_match_folder_name(
    folder_name: str,
) -> Optional[tuple[str, str, int, int, str]]:
    try:
        return parse_scored_match_folder_name(folder_name)
    except ValueError:
        return None
