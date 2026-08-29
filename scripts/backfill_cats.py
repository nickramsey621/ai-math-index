#!/usr/bin/env python3
"""Add/refresh the `mcats` column on data/papers/*.csv from raw harvest JSONL.

Usage: backfill_cats.py RAW.jsonl[.gz] [RAW2.jsonl.gz ...]

The compact per-month store originally kept only the primary category, but ~24%
of set=math papers have a non-math primary (cs.LG, math-ph, …), so primary alone
cannot support a per-subject breakdown. This script re-reads the raw harvests
(kept locally in data/raw/, gitignored) and fills in every math subject class
each paper lists. OAI `categories` already carries both alias spellings
(math-ph *and* math.MP, cs.IT *and* math.IT), so filtering on the "math." prefix
is enough.

Rows whose id is absent from the given raw files keep whatever mcats they had.
"""
import csv, gzip, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "data", "papers")
FIELDS = ["id", "created", "primary", "mcats", "nauth", "flags"]

def opener(path):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    wanted = set()
    for fn in sorted(os.listdir(PAPERS)):
        if fn.endswith(".csv"):
            with open(os.path.join(PAPERS, fn), newline="") as f:
                for row in csv.DictReader(f):
                    wanted.add(row["id"])
    cats = {}
    for path in sys.argv[1:]:
        n = 0
        with opener(path) as f:
            for line in f:
                r = json.loads(line)
                if r["id"] in wanted:
                    cats[r["id"]] = ";".join(c for c in r["cats"] if c.startswith("math."))
                    n += 1
        print(f"{os.path.basename(path)}: {n} matching records")

    total = filled = missing = 0
    for fn in sorted(os.listdir(PAPERS)):
        if not fn.endswith(".csv"):
            continue
        path = os.path.join(PAPERS, fn)
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            total += 1
            new = cats.get(row["id"])
            if new is not None:
                row["mcats"] = new
            row.setdefault("mcats", "")
            if row["mcats"]:
                filled += 1
            else:
                missing += 1
        buf = io.StringIO()
        w = csv.DictWriter(buf, FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        with open(path, "w", newline="") as f:
            f.write(buf.getvalue())
    print(f"rewrote {total} rows: {filled} with math cats, {missing} without")

main()
