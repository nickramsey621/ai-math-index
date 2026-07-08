#!/usr/bin/env python3
"""Harvest arXiv math set metadata via OAI-PMH to JSONL, including title/abstract/comments.

Usage: harvest.py OUT.jsonl FROM_DATE [UNTIL_DATE]
Datestamp-based (>= FROM_DATE), so it returns every record *touched* since then,
including revisions of old papers — downstream code assigns papers to months by
arXiv ID prefix and dedupes by id.
"""
import json, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

BASE = "https://oaipmh.arxiv.org/oai"
OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARX = "{http://arxiv.org/OAI/arXiv/}"

def fetch(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai-math-index/0.1 (nick.ramsey621@gmail.com)"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 503:
                wait = int(e.headers.get("Retry-After", "10"))
                print(f"503, retry after {wait}s", flush=True)
                time.sleep(min(wait, 60))
            else:
                print(f"HTTP {e.code}, attempt {attempt}", flush=True)
                time.sleep(10)
        except Exception as e:
            print(f"error {e}, attempt {attempt}", flush=True)
            time.sleep(10)
    raise RuntimeError("giving up on " + url)

def clean(s):
    return " ".join((s or "").split())

def main():
    out, from_date = sys.argv[1], sys.argv[2]
    params = {"verb": "ListRecords", "metadataPrefix": "arXiv", "set": "math", "from": from_date}
    if len(sys.argv) > 3:
        params["until"] = sys.argv[3]
    n_batch = n_rec = 0
    with open(out, "w") as f:
        while True:
            data = fetch(params)
            root = ET.fromstring(data)
            err = root.find(OAI + "error")
            if err is not None:
                # noRecordsMatch is normal for an empty window (weekend/holiday)
                print("OAI:", err.get("code"), err.text, flush=True)
                break
            lr = root.find(OAI + "ListRecords")
            for rec in lr.findall(OAI + "record"):
                header = rec.find(OAI + "header")
                if header.get("status") == "deleted":
                    continue
                meta = rec.find(OAI + "metadata")
                if meta is None:
                    continue
                ax = meta.find(ARX + "arXiv")
                authors = []
                au_el = ax.find(ARX + "authors")
                if au_el is not None:
                    for a in au_el.findall(ARX + "author"):
                        kn = a.findtext(ARX + "keyname") or ""
                        fn = a.findtext(ARX + "forenames") or ""
                        authors.append([kn, fn])
                row = {
                    "id": ax.findtext(ARX + "id"),
                    "created": ax.findtext(ARX + "created"),
                    "cats": (ax.findtext(ARX + "categories") or "").split(),
                    "authors": authors,
                    "title": clean(ax.findtext(ARX + "title")),
                    "abstract": clean(ax.findtext(ARX + "abstract")),
                    "comments": clean(ax.findtext(ARX + "comments")),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_rec += 1
            n_batch += 1
            tok = lr.find(OAI + "resumptionToken")
            if n_batch % 10 == 0 or tok is None or not (tok.text or "").strip():
                sz = tok.get("completeListSize") if tok is not None else "?"
                print(f"batch {n_batch}, {n_rec} records, listSize={sz}", flush=True)
            if tok is None or not (tok.text or "").strip():
                break
            params = {"verb": "ListRecords", "resumptionToken": tok.text.strip()}
            time.sleep(3.5)
    print(f"DONE: {n_rec} records in {n_batch} batches", flush=True)

main()
