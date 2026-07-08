#!/usr/bin/env python3
"""Classify unclassified phrase hits with Claude Haiku 4.5.

For each hit the model decides whether the matched AI/formalization phrases
reflect the paper *using* the tool to produce its results, the tool being the
*subject* of study, or an *incidental* match (e.g. an author named Claude,
"Gemini surfaces"). Results are written back into data/hits/YYMM.jsonl.

Skips gracefully (exit 0) when ANTHROPIC_API_KEY is not set or the SDK is
missing, so the pipeline still works regex-only.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HITS = os.path.join(ROOT, "data", "hits")

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("classify: ANTHROPIC_API_KEY not set, skipping")
    sys.exit(0)
try:
    import anthropic
except ImportError:
    print("classify: anthropic SDK not installed, skipping")
    sys.exit(0)

SCHEMA = {
    "type": "object",
    "properties": {
        "formal": {"type": ["string", "null"], "enum": ["used", "subject", "incidental", None]},
        "ai": {"type": ["string", "null"], "enum": ["used", "subject", "incidental", None]},
    },
    "required": ["formal", "ai"],
    "additionalProperties": False,
}

PROMPT = """You are auditing arXiv math papers for an index of AI use in mathematics research.
This paper's title/abstract/comments matched these phrase flags: {flags}

For each group present in the flags, classify the match:
- "used": the tool (proof assistant / AI model) was used in producing the paper's results — e.g. proofs formalized in Lean, results found or verified with an LLM, declared AI assistance.
- "subject": the tool is the object of study — e.g. evaluating LLM math ability, ML theory, formal-methods metatheory — but was not claimed as an aid in doing the mathematics.
- "incidental": false positive — the phrase means something else (a person named Claude, Gemini surfaces, GPT as an unrelated acronym, "lean" as an adjective, etc.).

Set a group's value to null if no flag from that group is present.

Title: {title}
Abstract: {abstract}
Comments: {comments}"""

def classify(client, rec):
    flags = ", ".join(rec["flags"])
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": PROMPT.format(
            flags=flags, title=rec["title"], abstract=rec["abstract"][:4000],
            comments=rec["comments"][:1000])}],
    )
    return json.loads(resp.content[0].text)

def main():
    client = anthropic.Anthropic()
    limit = int(os.environ.get("CLASSIFY_LIMIT", "500"))  # cost guard per run
    n = 0
    for fn in sorted(os.listdir(HITS)):
        if not fn.endswith(".jsonl"):
            continue
        path = os.path.join(HITS, fn)
        with open(path) as f:
            recs = [json.loads(line) for line in f]
        changed = False
        for rec in recs:
            if rec.get("cls") is not None or n >= limit:
                continue
            try:
                rec["cls"] = classify(client, rec)
                changed = True
                n += 1
            except anthropic.APIStatusError as e:
                print(f"classify: API error on {rec['id']}: {e.status_code}, stopping")
                break
        if changed:
            with open(path, "w") as f:
                for rec in recs:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"classify: classified {n} papers")

main()
