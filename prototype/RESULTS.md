# Prototype results — care-tip feed

Synthetic data, built to test the design (decisions D1–D18 in `../plan.md`). Total API spend ≈ $5.

## 1. Headline: the feed beats both baselines

| System | Unsafe tips (6 users) | Relevant | Judge panel approves (majority of 3 providers) |
|---|---|---|---|
| Random | 19.3 | 53% | 1/6 |
| Embedding-only (mentor's design) | 19.0 | 72% | 1/6 |
| **Full system** | **0** | **82%** | **6/6** |

Judges: Claude Sonnet 5.5, Gemini 3.1 Pro, GPT-6.1 Sol. Details: `data/feed_eval_findings.md`.

**The loop that got us there:** first run → judges approved only 2/6 of our feeds. They found 6 gaps code
couldn't see (missing diagnosis lock on PCOS tips, "cleared for moderate exercise" not treated as a limit,
test-prep tips after results, shift-work tips for day workers, strength training under "avoid strenuous",
a sensitive tip in backfill). Fixed → 6/6.

## 2. Reading the profile (extraction)

| Model | Safety errors raw → after checks | Cost / extraction |
|---|---|---|
| **Claude Haiku 5.5** (pick) | 0 → 0 (of 84) | ~$0.0015 |
| GPT-6 Luna | 1 → 0 — negation check caught it | ~$0.0007 |
| Gemini 3.8 Flash | 0 → 0 | ~$0.0073 |
| DeepSeek V4.1 Flash | dropped — invalid output twice | — |

- Correct answers cross-checked by Gemini 3.1 Pro + GPT-6.1 Sol (blind), majority rule → 5/6 profiles full agreement.
- The code tripwire false-alarmed on "screened for chest pain: none"; the LLM check cleared it — layering works.

## 2b. Embeddings (`scripts/eval_embeddings.py`, local, no API cost)

16 real English phrases from the test profiles, matched against 106 tips. Hit = a tip about that issue in the top 5.

| Model | English → Hindi tips | English → English tips | Tip-to-tip similarity (median / p95) |
|---|---|---|---|
| embeddinggemma (308M) | **94%** | **94%** | 0.28–0.34 / 0.50 — best separation |
| embeddinggemma-2 (740M) | 88% | 94% | 0.64–0.71 / 0.74–0.79 — crowded, thresholds fragile |
| qwen3-embedding:0.6b (used in prototype) | 81% | 94% | 0.31–0.51 / 0.50–0.67 |
| bge-m3 | 81% | 88% | 0.48–0.51 / 0.61–0.64 |

- Cross-language loss depends on the model: EmbeddingGemma loses nothing on this test; Qwen and BGE-M3 lose ~13 points.
- Newer isn't better here: EmbeddingGemma 2 squeezes almost every tip into 0.7–0.8 similarity (Headspace's lesson:
  check score spread on your own catalog).
- 16 queries → one query = 6 points. Direction, not precision. Recommendation: EmbeddingGemma (smaller, best spread).

## 3. Reema's feed today (v1)

1. 📌 Chest pain? Get checked now — red flag active
2. Why do we get period cramps — top issue (severe)
3. Ease cramps with a warm compress — top issue + prescribed
4. Set a strict daytime sleep block — prescribed
5. How to build a sleep routine — rotation

Blocked: HIIT/running/gym (cardiac flag), "Living with hypothyroidism" + iron-deficiency diet (diagnosis
lock, tests pending), expired tip, Tamil-only tip.

## 4. Change over time (`data/refresh_demo.md`)

- **7 days:** disliked video never returns; new tips first; issues rotate (back pain, legs, pelvic floor).
- **v1 → v2** (results back, cardiac cleared for moderate exercise): pin removed; iron-deficiency diet
  unlocks; test-prep tips leave; HIIT stays blocked by the new limit; newly confirmed issues get a recency boost.
- **Fast path:** new chest pain at 2 PM → squats + gym warm-up removed from today's feed, pin added. No LLM.

## 5. Findings worth saying out loud

1. **Even strong models mis-tag** — 22 fixes after generation, 16 more after the judges. Tags need clinical review.
2. **Embeddings can't spot duplicates** — two different ginger tips scored closer (0.93) than a true duplicate
   pair (0.84). Variety uses tags (same cluster + same type), not similarity.
3. **Content depth limits the feed** — Reema exhausts all 10 period tips by day 5 (Flo needed 40+ per topic);
   Priya gets 1 tip because the library has almost no Tamil videos. The system logs both as content demand.
4. **Judges catch what code can't**, and agree with each other often (all 3 agree on most feeds).
5. **One concept, one code** — `salt_reduction` vs `low_salt` split models and annotators alike.

## 6. Cost at scale (100k profile changes/day)

Extraction ≈ $75/day on batch (Haiku 5.5) ≈ $2.2k/month. Daily feed for all users: rules + lookups, ≈ $0.

## 7. Limits

Six synthetic profiles and 110 tips validate the design, not production numbers — thresholds tuned on
synthetic data are known to over-alarm on real data. Real PEPs are messier and code-mixed.

## Reproduce

```
cd prototype
uv run python scripts/eval_extraction.py anthropic/claude-haiku-5.5
uv run python scripts/show_feed.py reema_v1
uv run python scripts/eval_feeds.py
uv run python scripts/refresh_demo.py
uv run pytest -q
```
