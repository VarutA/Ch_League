"""Shared paths for Gold league (group stage for now)."""
import os

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CODE_DIR)

CHARACTER_GOLD_MASTER = os.path.join(_PROJECT_ROOT, "Character", "Character Gold")
PIC_SELECTION = os.path.join(_PROJECT_ROOT, "Character", "Pic Selection")

_LEAGUE_GOLD_ROOT = os.path.join(_PROJECT_ROOT, "League Gold")
LEAGUE_GOLD_CHARACTER = os.path.join(_LEAGUE_GOLD_ROOT, "Character Gold")
GOLD_GROUP_STATE_ROOT = os.path.join(_LEAGUE_GOLD_ROOT, "Gold Group State")
LEAGUE_GOLD_OVERALL_STANDING = os.path.join(
    GOLD_GROUP_STATE_ROOT, "Gold League Standing"
)
GOLD_KNOCKOUT_STATE_ROOT = os.path.join(_LEAGUE_GOLD_ROOT, "Gold Knock-Out State")
GOLD_ROUND4_FIXTURE = os.path.join(
    GOLD_KNOCKOUT_STATE_ROOT, "Round 4 (16 Team) Fixture"
)
GOLD_ROUND3_FIXTURE = os.path.join(
    GOLD_KNOCKOUT_STATE_ROOT, "Round 3 (Quarter Final) Fixture"
)
GOLD_ROUND2_FIXTURE = os.path.join(
    GOLD_KNOCKOUT_STATE_ROOT, "Round 2 (Semi Final) Fixture"
)
# Keep trailing space to match existing on-disk folder name in this project.
GOLD_ROUND1_FIXTURE = os.path.join(
    GOLD_KNOCKOUT_STATE_ROOT, "Round 1 (Final) Fixture "
)
GOLD_RANK_SUMMARY = os.path.join(_LEAGUE_GOLD_ROOT, "Gold Rank Summary")

GOLD_GROUP_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H"]
GOLD_GROUP_SIZE = 10
GOLD_GROUP_TEAMS_TOTAL = len(GOLD_GROUP_LABELS) * GOLD_GROUP_SIZE

# Group stage is single round-robin with 10 teams -> 9 matchweeks.
GOLD_GROUP_FIXTURE_MAX_WEEK = 9
