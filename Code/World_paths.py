"""Paths for World Cup knockout (256 teams)."""
import os

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)

PIC_SELECTION = os.path.join(_PROJECT_ROOT, "Character", "Pic Selection")

_WORLD_CUP_ROOT = os.path.join(_PROJECT_ROOT, "World Cup")
WORLD_CUP_SOURCE = os.path.join(_WORLD_CUP_ROOT, "World Cup Source")
WORLD_CUP_CHARACTER = os.path.join(_WORLD_CUP_ROOT, "World Cup Character")
WORLD_CUP_FIXTURE = os.path.join(_WORLD_CUP_ROOT, "World Cup Fixture")
WORLD_CUP_SUMMARY = os.path.join(_WORLD_CUP_ROOT, "World Cup Summary")
# Sibling of World Cup at project root (not inside World Cup/).
WORLD_RANKING = os.path.join(_PROJECT_ROOT, "World Ranking")

# Copies of standings / summary used for seeding (user-requested snapshot).
WORLD_SOURCE_DIAMOND_STANDING = os.path.join(
    WORLD_CUP_SOURCE, "Diamond League Standing"
)
WORLD_SOURCE_GOLD_SUMMARY = os.path.join(WORLD_CUP_SOURCE, "Gold Rank Summary")
WORLD_SOURCE_SILVER_STANDING = os.path.join(
    WORLD_CUP_SOURCE, "Silver League Standing"
)
WORLD_SOURCE_RANKING_PRE_TOURNAMENT = os.path.join(
    WORLD_CUP_SOURCE, "World Ranking Pre-Tournament"
)

# Round 1 = 256 teams (128 matches) ... Round 8 = Final (1 match).
WORLD_CUP_ROUND_FOLDERS = [
    "Round 1 (256 Team)",
    "Round 2 (128 Team)",
    "Round 3 (64 Team)",
    "Round 4 (32 Team)",
    "Round 5 (16 Team)",
    "Round 6 (8 Team)",
    "Round 7 (Semi Final)",
    "Round 8 (Final)",
]

DIAMOND_PICK = 30
GOLD_PICK = 80
SILVER_PICK = 146
WORLD_CUP_TEAM_TOTAL = DIAMOND_PICK + GOLD_PICK + SILVER_PICK  # 256
