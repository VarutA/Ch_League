"""
Extract canonical team names from standing folder titles (exact match, no substring heuristics).

Formats (must match what Diamond_League_Cal / Gold_Group_Cal write):

- Diamond + Gold group: ``{n}. {team} [{pt}pt] [{gf}-{ga}={gd}] [{W}W-{T}T-{L}L]``
- Gold overall: ``{n}. ({rank}{Group}) {team} [{pt}pt] ...``  e.g. ``1. (1A) Name [12pt] ...``
"""
from __future__ import annotations

import re
from typing import Optional

# Same stats tail as Gold_Group_Summary / Silver_Group_Summary overall rows.
_STANDING_STATS_TAIL = (
    r"\[(\d+)pt\]\s+"
    r"\[(\d+)-(\d+)=([+-]?\d+)\]\s+\[(\d+)W-(\d+)T-(\d+)L\]$"
)

_DIAMOND_OR_GOLD_GROUP_STANDING_RE = re.compile(
    r"^(\d+)\.\s+(.+?)\s+" + _STANDING_STATS_TAIL
)

_GOLD_OVERALL_STANDING_RE = re.compile(
    r"^(\d+)\.\s+\(\d+[A-H]\)\s+(.+?)\s+" + _STANDING_STATS_TAIL
)


def parse_diamond_or_gold_group_standing_team(folder_name: str) -> Optional[str]:
    """Team from Diamond or Gold *group* standing folder name, or None if not that format."""
    m = _DIAMOND_OR_GOLD_GROUP_STANDING_RE.match(folder_name)
    if not m:
        return None
    return m.group(2).strip()


def parse_gold_overall_standing_team(folder_name: str) -> Optional[str]:
    """Team from Gold League Standing (combined) folder name, or None."""
    m = _GOLD_OVERALL_STANDING_RE.match(folder_name)
    if not m:
        return None
    return m.group(2).strip()


def map_standing_filenames_to_teams(
    filenames: list[str],
    team_set: set[str],
    *,
    parser,
) -> dict[str, str]:
    """
    Build ``team_name -> current_filename`` for files under a standing folder.

    A plain folder whose name equals a known team counts as that team.
    ``parser`` should be ``parse_diamond_or_gold_group_standing_team`` or
    ``parse_gold_overall_standing_team``.
    """
    out: dict[str, str] = {}
    for file in filenames:
        if file in ("Thumbs.db", ".DS_Store"):
            continue
        t: Optional[str] = None
        parsed = parser(file)
        if parsed is not None and parsed in team_set:
            t = parsed
        elif file in team_set:
            t = file
        if t is None:
            continue
        if t in out:
            raise ValueError(
                f"Ambiguous standing folders for team {t!r}: {out[t]!r} and {file!r}"
            )
        out[t] = file
    return out
