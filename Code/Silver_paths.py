"""Shared paths for Silver league (Swiss format)."""
import os

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)

CHARACTER_SILVER_MASTER = os.path.join(_PROJECT_ROOT, "Character", "Character Silver")
PIC_SELECTION = os.path.join(_PROJECT_ROOT, "Character", "Pic Selection")

_LEAGUE_SILVER_ROOT = os.path.join(_PROJECT_ROOT, "League Silver")
LEAGUE_SILVER_CHARACTER = os.path.join(_LEAGUE_SILVER_ROOT, "Character Silver")
LEAGUE_SILVER_SWISS_FIXTURE = os.path.join(_LEAGUE_SILVER_ROOT, "Swiss Fixture")
LEAGUE_SILVER_STANDING = os.path.join(_LEAGUE_SILVER_ROOT, "Silver League Standing")
