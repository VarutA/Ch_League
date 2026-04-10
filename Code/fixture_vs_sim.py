"""
Score all pending ``N. Home VS Away`` match folders under one directory (in place rename).

Used by Diamond week folders, Gold group weeks, Swiss rounds, knockout rounds, World Cup rounds.
"""
from __future__ import annotations

import os
import random


def simulate_vs_in_folder(folder_path: str, seed: int | None = None) -> int:
    if seed is not None:
        random.seed(seed)
    if not os.path.isdir(folder_path):
        return 0
    n = 0
    for name in sorted(os.listdir(folder_path)):
        if name in ("Thumbs.db", ".DS_Store"):
            continue
        if " VS " not in name or ". " not in name:
            continue
        match_num, rest = name.split(". ", 1)
        parts = rest.split(" VS ", 1)
        if len(parts) != 2:
            continue
        a, b = parts[0], parts[1]
        s0, s1 = random.randint(0, 9), random.randint(0, 9)
        while s0 == s1:
            s1 = random.randint(0, 9)
        new_name = f"{match_num}. {a} {s0}-{s1} {b}"
        old_path = os.path.join(folder_path, name)
        new_path = os.path.join(folder_path, new_name)
        if not os.path.isdir(old_path):
            continue
        if os.path.exists(new_path):
            raise FileExistsError(f"Target exists: {new_path}")
        os.rename(old_path, new_path)
        n += 1
    return n
