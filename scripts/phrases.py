"""Phrase patterns scanned over title + abstract + comments.

Two groups:
  formal — proof assistants / formalization tooling
  ai     — AI model mentions / declared AI assistance

Patterns are deliberately anchored to tool names; bare "formalize"/"machine
learning"/"artificial intelligence" are subject-matter vocabulary in math and
would swamp the signal. Ambiguous names (Claude, Gemini, GPT) are kept and
disambiguated by the classifier pass.
"""
import re

# (group, name, pattern, flags)
_DEFS = [
    ("formal", "lean", r"\bLean\s?[34]\b"
                       r"|\bLean\b(?=[^.]{0,80}(?:formali[sz]|proof assistant|theorem prover|prover\b))"
                       r"|(?:formali[sz]\w*|proof assistant|theorem prover)(?=[^.]{0,80}\bLean\b)", 0),
    ("formal", "mathlib", r"\bmathlib\b", re.I),
    ("formal", "isabelle", r"\bIsabelle(?:/HOL)?\b", re.I),
    ("formal", "coq_rocq", r"\bCoq\b|\bRocq\b", 0),
    ("formal", "proof_assistant", r"\bproof assistants?\b|\binteractive theorem prov(?:er|ers|ing)\b", re.I),
    ("ai", "chatgpt", r"\bChatGPT\b", re.I),
    ("ai", "gpt", r"\bGPT-?\d\w*\b|\bGPT\b", 0),
    ("ai", "llm", r"\bLLMs?\b", 0),
    ("ai", "llm_full", r"\blarge language models?\b", re.I),
    ("ai", "alphaproof", r"\bAlpha(?:Proof|Geometry|Evolve)\b", re.I),
    ("ai", "deepseek", r"\bDeepSeek\b", re.I),
    ("ai", "claude", r"\bClaude\b", 0),
    ("ai", "gemini", r"\bGemini\b", 0),
    ("ai", "copilot", r"\bcopilot\b", re.I),
    ("ai", "ai_assisted", r"\bAI-assisted\b|\bAI assistance\b|\bassisted by AI\b"
                          r"|\bwith the (?:help|aid) of AI\b|\bAI tools?\b", 0),
]

PATTERNS = [(g, n, re.compile(p, f)) for g, n, p, f in _DEFS]

def scan(text):
    """Return sorted list of 'group:name' flags matching text."""
    return sorted({f"{g}:{n}" for g, n, rx in PATTERNS if rx.search(text)})
