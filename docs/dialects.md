# Dialect Handling

Seven dialects are supported: English, Spanish, Hindi (Devanagari), Hinglish,
Spanglish, Punjabi (Gurmukhi), Punglish.

The detector is a lightweight script-based heuristic. For ambiguous cases
(e.g. Romanized South Asian) it falls back to an LLM-based classifier.

Translation is used only as a retrieval fallback when the detector is
unsure — embeddings are multilingual MiniLM so Hindi/Spanish queries can
retrieve English docs directly.
