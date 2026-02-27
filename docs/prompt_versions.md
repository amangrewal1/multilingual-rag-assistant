# Prompt Versions

Each prompt has a version suffix in the filename:
- `prompts.py` — v1 (current production prompts)
- `prompts_v2.py` — v2 (experimental, retrieval-grounded)

The eval harness loads whichever version is pointed to by the
`PROMPT_MODULE` env var.
