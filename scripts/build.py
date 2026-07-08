#!/usr/bin/env python3
"""Aggregate the per-month store into docs/data.json for the site."""
import csv, json, os
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "data", "papers")
HITS = os.path.join(ROOT, "data", "hits")
OUT = os.path.join(ROOT, "docs", "data.json")

def main():
    months = {}
    for fn in sorted(os.listdir(PAPERS)):
        if not fn.endswith(".csv"):
            continue
        ym = fn[:-4]
        m = {"ym": ym, "papers": 0, "formal": 0, "ai": 0, "patterns": Counter()}
        with open(os.path.join(PAPERS, fn), newline="") as f:
            for row in csv.DictReader(f):
                m["papers"] += 1
                flags = row["flags"].split(";") if row["flags"] else []
                groups = {fl.split(":")[0] for fl in flags}
                for g in groups:
                    m[g] += 1
                for fl in flags:
                    m["patterns"][fl] += 1
        months[ym] = m

    # classification splits from hits files
    for fn in sorted(os.listdir(HITS)):
        if not fn.endswith(".jsonl"):
            continue
        ym = fn[:-6]
        if ym not in months:
            continue
        cls = {"formal": Counter(), "ai": Counter()}
        with open(os.path.join(HITS, fn)) as f:
            for line in f:
                rec = json.loads(line)
                groups = {fl.split(":")[0] for fl in rec["flags"]}
                for g in groups:
                    if rec.get("cls") is None:
                        cls[g]["unclassified"] += 1
                    else:
                        cls[g][rec["cls"].get(g) or "unclassified"] += 1
        months[ym]["cls"] = {g: dict(c) for g, c in cls.items() if c}

    out = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "months": [
            {**m, "patterns": dict(m["patterns"])}
            for ym, m in sorted(months.items())
        ],
    }
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(m["papers"] for m in months.values())
    print(f"build: {len(months)} months, {n} papers -> docs/data.json")

main()
