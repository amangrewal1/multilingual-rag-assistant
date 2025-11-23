# Safety Gate

The safety gate runs before retrieval and classifies queries into:
- **clean** — proceed to retrieval and generation
- **ambiguous** — defer; ask a disambiguating question
- **unsafe** — decline with a translated refusal message

Refusal messages are templated in English and translated into the user's
dialect at response time. This keeps refusals localized without duplicating
copy per language.
