#!/usr/bin/env python3
"""Merge a raw harvest JSONL into the compact per-month store.

Usage: ingest.py RAW.jsonl [RAW2.jsonl ...]

- Papers are assigned to months by arXiv ID prefix (YYMM); old-style IDs and
  months before MIN_YM are skipped (datestamp harvests include revisions of
  arbitrarily old papers).
- data/papers/YYMM.csv gets one row per paper: id, created, primary category,
  author count, phrase flags.
- Papers with any flag also get their full text appended to
  data/hits/YYMM.jsonl for auditing and classification.
- Already-recorded IDs are skipped (first version wins).
"""
import csv, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phrases import scan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "data", "papers")
HITS = os.path.join(ROOT, "data", "hits")
MIN_YM = "2401"
FIELDS = ["id", "created", "primary", "nauth", "flags"]

def load_existing():
    seen = set()
    for fn in os.listdir(PAPERS):
        if fn.endswith(".csv"):
            with open(os.path.join(PAPERS, fn), newline="") as f:
                for row in csv.DictReader(f):
                    seen.add(row["id"])
    return seen

def main():
    seen = load_existing()
    new_rows = {}   # ym -> [row dict]
    new_hits = {}   # ym -> [record]
    n_new = n_hit = 0
    for path in sys.argv[1:]:
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                pid = r["id"]
                if "." not in pid:
                    continue
                ym = pid[:4]
                if not (MIN_YM <= ym <= "9912") or pid in seen:
                    continue
                seen.add(pid)
                text = " ".join([r.get("title", ""), r.get("abstract", ""), r.get("comments", "")])
                flags = scan(text)
                new_rows.setdefault(ym, []).append({
                    "id": pid, "created": r.get("created") or "",
                    "primary": r["cats"][0] if r["cats"] else "",
                    "nauth": len(r.get("authors", [])), "flags": ";".join(flags),
                })
                n_new += 1
                if flags:
                    n_hit += 1
                    new_hits.setdefault(ym, []).append({
                        "id": pid, "ym": ym, "flags": flags, "title": r.get("title", ""),
                        "abstract": r.get("abstract", ""), "comments": r.get("comments", ""),
                        "cls": None,
                    })
    for ym, rows in sorted(new_rows.items()):
        path = os.path.join(PAPERS, ym + ".csv")
        fresh = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, FIELDS)
            if fresh:
                w.writeheader()
            w.writerows(sorted(rows, key=lambda r: r["id"]))
    for ym, recs in sorted(new_hits.items()):
        with open(os.path.join(HITS, ym + ".jsonl"), "a") as f:
            for rec in sorted(recs, key=lambda r: r["id"]):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"ingested {n_new} new papers ({n_hit} phrase hits)")

main()
