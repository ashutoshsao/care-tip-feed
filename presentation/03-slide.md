# Architecture ⏱ 2 min

```
WHEN PROFILE CHANGES (nightly batch)        EVERY DAY, EVERYONE (no LLM)
LLM extracts facts + status + quote   →     find tips → safety filter → rank → feed
code checks → LLM if flagged → clinician    (codes, synonym map, embeddings for leftovers)
```

- **LLM:** reading the profile — only on change · **Embeddings:** fallback matching only · **Code:** everything daily
- New red flag → fast path: unsafe tips removed from today's feed immediately

> Say: "LLM cost scales with profile changes, not with users."
