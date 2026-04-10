"""Shared paths for Diamond league.

Roster & pics: project `Character/`. League outputs: `League Diamond/` (project root).
"""
import os

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)

CHARACTER_DIAMOND_MASTER = os.path.join(_PROJECT_ROOT, "Character", "Character Diamond")
PIC_SELECTION = os.path.join(_PROJECT_ROOT, "Character", "Pic Selection")
_LEAGUE_DIAMOND_ROOT = os.path.join(_PROJECT_ROOT, "League Diamond")
LEAGUE_DIAMOND_CHARACTER = os.path.join(_LEAGUE_DIAMOND_ROOT, "Character Diamond")
LEAGUE_DIAMOND_FIXTURE = os.path.join(_LEAGUE_DIAMOND_ROOT, "Diamond League Fixture")
LEAGUE_DIAMOND_STANDING = os.path.join(_LEAGUE_DIAMOND_ROOT, "Diamond League Standing")

# Scan fixture weeks 1..N; stop at first incomplete (used by Diamond_League_Cal).
DIAMOND_FIXTURE_MAX_WEEK = 58
