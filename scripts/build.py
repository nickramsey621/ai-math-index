#!/usr/bin/env python3
"""Aggregate the per-month store into docs/data.json for the site."""
import csv, json, os
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "data", "papers")
HITS = os.path.join(ROOT, "data", "hits")
OUT = os.path.join(ROOT, "docs", "data.json")

# arXiv math subject classes. math.MP / math.IT / math.NA are the alias spellings
# of math-ph / cs.IT / cs.NA; OAI lists both, so they land here like any other.
AREA_NAMES = {
    "math.AC": "Commutative Algebra", "math.AG": "Algebraic Geometry",
    "math.AP": "Analysis of PDEs", "math.AT": "Algebraic Topology",
    "math.CA": "Classical Analysis and ODEs", "math.CO": "Combinatorics",
    "math.CT": "Category Theory", "math.CV": "Complex Variables",
    "math.DG": "Differential Geometry", "math.DS": "Dynamical Systems",
    "math.FA": "Functional Analysis", "math.GM": "General Mathematics",
    "math.GN": "General Topology", "math.GR": "Group Theory",
    "math.GT": "Geometric Topology", "math.HO": "History and Overview",
    "math.IT": "Information Theory", "math.KT": "K-Theory and Homology",
    "math.LO": "Logic", "math.MG": "Metric Geometry",
    "math.MP": "Mathematical Physics", "math.NA": "Numerical Analysis",
    "math.NT": "Number Theory", "math.OA": "Operator Algebras",
    "math.OC": "Optimization and Control", "math.PR": "Probability",
    "math.QA": "Quantum Algebra", "math.RA": "Rings and Algebras",
    "math.RT": "Representation Theory", "math.SG": "Symplectic Geometry",
    "math.SP": "Spectral Theory", "math.ST": "Statistics Theory",
}
GROUPS = ("ai", "formal")

def new_area():
    # [papers, ai, formal, ai used, formal used]
    return [0, 0, 0, 0, 0]

def main():
    months = {}
    hit_cats = {}       # id -> [math cats], phrase hits only (for the cls split)
    for fn in sorted(os.listdir(PAPERS)):
        if not fn.endswith(".csv"):
            continue
        ym = fn[:-4]
        m = {"ym": ym, "papers": 0, "formal": 0, "ai": 0, "patterns": Counter()}
        areas = defaultdict(new_area)
        with open(os.path.join(PAPERS, fn), newline="") as f:
            for row in csv.DictReader(f):
                m["papers"] += 1
                flags = row["flags"].split(";") if row["flags"] else []
                groups = {fl.split(":")[0] for fl in flags}
                for g in groups:
                    m[g] += 1
                for fl in flags:
                    m["patterns"][fl] += 1
                cats = row.get("mcats", "").split(";") if row.get("mcats") else []
                for c in cats:
                    a = areas[c]
                    a[0] += 1
                    for i, g in enumerate(GROUPS, start=1):
                        if g in groups:
                            a[i] += 1
                if flags and cats:
                    hit_cats[row["id"]] = cats
        m["areas"] = areas
        months[ym] = m

    # classification splits from hits files (overall and per area)
    for fn in sorted(os.listdir(HITS)):
        if not fn.endswith(".jsonl"):
            continue
        ym = fn[:-6]
        if ym not in months:
            continue
        cls = {g: Counter() for g in GROUPS}
        areas = months[ym]["areas"]
        with open(os.path.join(HITS, fn)) as f:
            for line in f:
                rec = json.loads(line)
                groups = {fl.split(":")[0] for fl in rec["flags"]}
                for g in groups:
                    if rec.get("cls") is None:
                        cls[g]["unclassified"] += 1
                        continue
                    verdict = rec["cls"].get(g) or "unclassified"
                    cls[g][verdict] += 1
                    if verdict == "used":
                        for c in hit_cats.get(rec["id"], ()):
                            areas[c][3 + GROUPS.index(g)] += 1
        months[ym]["cls"] = {g: dict(c) for g, c in cls.items() if c}

    totals = Counter()
    for m in months.values():
        for c, a in m["areas"].items():
            totals[c] += a[0]

    out = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        # areas ordered by total volume; name falls back to the bare code
        "areas": [
            {"cat": c, "name": AREA_NAMES.get(c, c), "papers": n}
            for c, n in totals.most_common()
        ],
        "areaFields": ["papers", "ai", "formal", "aiUsed", "formalUsed"],
        "months": [
            {**m, "patterns": dict(m["patterns"]), "areas": dict(sorted(m["areas"].items()))}
            for ym, m in sorted(months.items())
        ],
    }
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(m["papers"] for m in months.values())
    print(f"build: {len(months)} months, {n} papers, {len(totals)} areas -> docs/data.json")

main()
