# AI in mathematics — an arXiv index

Daily-updated index of AI use in mathematics research, from arXiv metadata:
monthly submission volume, and the share of papers whose title/abstract/comments
mention AI models (GPT, LLMs, AlphaProof, …) or formalization tools (Lean,
Isabelle, Coq/Rocq, …).

**Live site:** https://nickramsey621.github.io/ai-math-index/

## How it works

- `scripts/harvest.py` — arXiv OAI-PMH harvester (`set=math`, includes
  title/abstract/comments). Datestamp-windowed; polite rate (3.5s/batch).
- `scripts/ingest.py` — assigns papers to months by arXiv ID prefix, dedupes by
  ID, scans phrases (`scripts/phrases.py`), appends to `data/papers/YYMM.csv`;
  matched papers' full text goes to `data/hits/YYMM.jsonl`.
- `scripts/classify.py` — optional Claude (Haiku 4.5) pass over phrase hits:
  was the tool *used* to produce the results, the *subject* of study, or an
  *incidental* match (an author named Claude, "Gemini surfaces")? Skips itself
  when `ANTHROPIC_API_KEY` is unset.
- `scripts/build.py` — aggregates to `docs/data.json`; `docs/index.html` renders it.
- `.github/workflows/update.yml` — daily cron: harvest last 14 days → ingest →
  classify → build → commit. GitHub Pages serves `docs/`.

## Caveats

- **Mentions measure disclosure, not use.** Acknowledgment-section disclosures
  are invisible (no full text), so everything here is a lower bound — and the
  disclosure norm itself is changing over time.
- Papers are bucketed by submission month (arXiv ID prefix); the current month
  is always incomplete. OAI `created` dates are not trusted (revision artifacts).
- Phrase patterns are tool-anchored on purpose; bare "machine learning" /
  "formalize" are ordinary math vocabulary and are not counted.

Data: arXiv metadata via OAI-PMH (CC0). This site is not affiliated with arXiv.
