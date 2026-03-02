# Multilingual Conversational AI for Accessibility

![tests](https://github.com/amangrewal1/multilingual-rag-assistant/actions/workflows/test.yml/badge.svg) ![license](https://img.shields.io/badge/license-MIT-blue)

RAG assistant for code-switched queries. Answers grounded in an indexed knowledge base with inline citations, a safety gate for unsafe or ambiguous inputs, and an eval harness for golden / regression / red-team suites.

## What it does

- **Dialects:** English, Spanish, Hindi (Devanagari), Hinglish, Spanglish, Punjabi (Gurmukhi), Punglish.
- **Pipeline:** detect dialect -> safety gate -> normalize-for-retrieval -> top-k vector retrieval -> grounded generation with `[#n]` citations -> optional refusal with translated message.
- **Evals:** golden set (grounded Q&A across dialects), regression (hallucination / ambiguity guards), red team (prompt injection, PII, medical advice, fabrication bait).
- **Metrics tracked:** faithfulness, answer relevance, citation precision, refusal accuracy, p50/p95 latency.

## Layout

```
src/              pipeline: retriever, translator, safety, rag, assistant, prompts
data/
  knowledge_base/ markdown docs indexed at startup (WCAG, screen readers, captions, etc.)
  evals/          golden_set.json, regression.json, red_team.json
evals/            harness + metrics + runner
cli.py            REPL and one-shot asking
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env           # then fill ANTHROPIC_API_KEY
python cli.py --rebuild-index  # build the vector index
```

## Use

```bash
python cli.py --q "What contrast ratio does WCAG require for normal text?"
python cli.py --q "screen reader ke liye headings kyun important hain?"
python cli.py                  # REPL
```

## Run evals

```bash
python -m evals.run_evals --suite golden
python -m evals.run_evals --suite regression
python -m evals.run_evals --suite red_team
python -m evals.run_evals --suite all
```

Reports land under `data/eval_reports/<suite>.json`.

## Design notes

- Retrieval embeddings use a multilingual MiniLM so Hindi / Spanish queries hit English docs without needing upfront translation, and translation is only used as a fallback when the heuristic detector is unsure.
- Refusal messages are templated in English and translated into the user's dialect at response time, so refusals stay localized without duplicating copy per language.
- Red-team eval treats prompt injection and fabrication separately from out-of-scope refusal: injection must be blocked, fabrication must be hedged, OOS must be declined politely.
- Judge uses a stronger model than the assistant to reduce self-grading bias.
