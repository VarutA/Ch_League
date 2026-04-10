"""Random-score every Gold group-stage week A–H (for testing)."""
from __future__ import annotations

import argparse
import os
import sys

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from fixture_vs_sim import simulate_vs_in_folder
from Gold_paths import (
    GOLD_GROUP_FIXTURE_MAX_WEEK,
    GOLD_GROUP_LABELS,
    GOLD_GROUP_STATE_ROOT,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=4242, help="Base RNG seed (offset per group/week)")
    ns = p.parse_args()
    base = ns.seed
    total = 0
    for label in GOLD_GROUP_LABELS:
        for w in range(1, GOLD_GROUP_FIXTURE_MAX_WEEK + 1):
            path = os.path.join(
                GOLD_GROUP_STATE_ROOT, f"Group {label} Fixture", f"week {w}"
            )
            if not os.path.isdir(path):
                print(f"skip missing {path}")
                continue
            n = simulate_vs_in_folder(path, seed=base + hash(label) % 10000 + w * 17)
            total += n
            print(f"Group {label} week {w}: scored {n} match(es)")
    print(f"Total scored: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
