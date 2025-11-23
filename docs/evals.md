# Evaluation Suites

- **Golden set** — grounded Q&A across all dialects. Measures faithfulness,
  answer relevance, citation precision.
- **Regression set** — hallucination and ambiguity guards. Prevents known
  failure modes from recurring.
- **Red team** — prompt injection, PII extraction, medical advice,
  fabrication bait. Measures refusal accuracy.

Judge model is a stronger Claude tier than the assistant to reduce
self-grading bias.
