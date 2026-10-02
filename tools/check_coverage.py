#!/usr/bin/env python3
"""Report save files that no manifest entry claims, and files claimed by more than one game.

Usage: ludusavi backup --preview --api </dev/null > preview.json
       check_coverage.py preview.json <root> [<root> ...]
Exits 1 if any non-ignored file is unclaimed.
"""
import json
import os
import re
import sys

IGNORE = re.compile(r"(^|/)(\.DS_Store|\.nomedia|\.stfolder[^/]*|\.stversions|\.stignore|Thumbs\.db)(/|$)")

games = json.load(open(sys.argv[1]))["games"]
claims = {}
for name, game in games.items():
    for path in game["files"]:
        claims.setdefault(path, []).append(name)

shared = {p: n for p, n in claims.items() if len(n) > 1}
unclaimed = []
for root in map(os.path.abspath, sys.argv[2:]):
    for d, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            if p not in claims and not IGNORE.search(p):
                unclaimed.append(p)

for p, n in sorted(shared.items()):
    print(f"SHARED    {p}  <- {', '.join(sorted(n))}")
for p in sorted(unclaimed):
    print(f"UNCLAIMED {p}")
print(f"{len(games)} games, {len(claims)} files claimed, {len(shared)} shared, {len(unclaimed)} unclaimed")
sys.exit(1 if unclaimed else 0)
