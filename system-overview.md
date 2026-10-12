# System overview — care-tip feed

One-page view of the design. Each step points to its decision in `plan.md`.

```
WHEN THE PROFILE CHANGES  (nightly batch, D15; new red flag → fast path, D11)
 1. LLM extracts structured profile (codes from vocabulary + status + quote)   D7, D10
 2. Checks vs quotes + latest saved version
      code → LLM (only if flagged) → safer status + clinical (if unsure)       D7
 3. Save as new version (ISO 8601, UTC)                                        D14

EVERY DAY, FOR EVERYONE  (code + lookups, no LLM)
 4. Find tips: exact codes → synonym map → embeddings for leftovers            D12
 5. Safety filter (code): contraindications × flags, diagnosis lock,
    language + fallback, review status                                         D2–D5
 6. Rank: severity + recency → slots
      pinned safety tip first · top issue ≤ 2 of 5 · ≥1 prescription slot      D4, D8, D14
 7. Engagement picks which video fills each slot (discreet mode if sensitive)  D6, D13
 8. Repeat + rotation rules → today's feed                                     D9

OFFLINE / OCCASIONAL
 • LLM drafts vocabulary + synonym additions → clinicians review               D12
 • Embed new tips once                                                         D12
 • Check each language variant against the canonical                           D1
```

## Which tool where (the brief's question)

| Tool | Used for | Why |
|---|---|---|
| **LLM** | Profile extraction (on change, batch); verifying flagged extractions; offline vocabulary drafts, variant consistency checks, eval judge | Free text with negation/status needs language understanding; runs only on changes or offline, so cost scales with changes, not users |
| **Embeddings** | Tips embedded once; matching leftover (out-of-vocabulary) issues; grouping near-duplicate tips | Meaning-based matching where codes don't reach; only suggests, never decides safety |
| **Code** | All checks, safety filter, matching, ranking, rotation, fallbacks — everything daily | Predictable, auditable, near-free at 500k users/day |

## Cost (assumed 50k–100k profile changes/day)

- Extraction: ≈ $27/day batch at 100k (Haiku 5.5) ≈ $800/month
- Verifier on flagged (~10%): a few $/day
- Daily composition for all users: near-zero
