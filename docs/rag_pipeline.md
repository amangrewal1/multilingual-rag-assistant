# RAG Pipeline

```
user query
   │
   ▼ detect dialect
   ▼ safety gate
   ▼ normalize query (optional translation)
   ▼ top-k retrieval from multilingual vector index
   ▼ grounded generation with [#n] citations
   ▼ translate refusal (if applicable)
   ▼
response
```

Each step logs timing and intermediate state to the eval harness for
debugging failed cases.
