# AI Math Index

Daily-updated public index of AI use in math on arXiv (spun out of
`~/arxiv-analysis` — read that repo's CLAUDE.md for the research findings and
arXiv API gotchas; they all apply here). Live at
https://nickramsey621.github.io/ai-math-index/, updated by GitHub Actions
(`update.yml`, 09:00 UTC daily).

## Pipeline

`update.py` = harvest (last 14 days, OAI datestamp) → `ingest.py` (dedupe by ID,
bucket by ID-prefix month, phrase-scan) → `classify.py` (Haiku 4.5 used/subject/
incidental; no-op without `ANTHROPIC_API_KEY`) → `build.py` (docs/data.json).

- `data/papers/YYMM.csv` — one row/paper: id, created, primary cat, n authors, flags.
- `data/hits/YYMM.jsonl` — full title/abstract/comments for phrase hits only,
  plus `cls` (classification). The full corpus with abstracts is NOT in the repo
  (`data/raw/` is gitignored, backfill kept locally) — adding a new phrase
  pattern requires a local re-harvest backfill, then `ingest.py` + rebuild.
- Phrase list: `scripts/phrases.py`. Tool-anchored by design; don't add bare
  "machine learning"/"formalize" — they're ordinary math vocabulary.
- `CLASSIFY_LIMIT` env (default 500/run) caps classifier spend. Live since
  2026-07-08 (`ANTHROPIC_API_KEY` repo secret set); 2024 pattern sanity-checked:
  AI mentions mostly "subject", formalization mostly "used".

## Gotchas

- Months bucketed by arXiv ID prefix, never `created`/datestamp (revisions lie).
- Datestamp harvests include revisions of old papers; ingest skips months < 2401
  and already-seen IDs (first version wins).
- Current month is always partial — site renders it dashed; don't "fix" low counts.
- `noRecordsMatch` from OAI is normal for empty windows, not an error.
- Structured outputs rejects nullable union types (`"type": ["string","null"]`)
  with a 400 — classify.py uses plain enums with a "none" sentinel instead.
- Every daily run commits even with zero new papers (build.py refreshes the
  `updated` timestamp in data.json) — expected, not a bug.
- Consistency check after changes: 2506 = 4,410 papers, 2606 = 6,452 (OAI counts).

## Open follow-ups

- Promote "classified as used" to its own chart series once the classification
  backlog clears (~2026-07-10) — the truest "AI use" line the index can offer.
