# Extraction comparison (prototype step 4) — 2026-10-12

6 profiles × 2 runs per model; 84 safety-critical checks per model (red flags, negation, family history,
planned-vs-done tests, pregnancy, explicit restrictions, language).

| Model | Critical errors (raw → after checks) | Issue recall | Intervention recall | $/extraction | Notes |
|---|---|---|---|---|---|
| anthropic/claude-haiku-5.5 | 0/84 → 0/84 | 100% | 100% | ~$0.0015 | Pick: zero raw errors on a safety-critical step |
| google/gemini-3.8-flash | 0/84 → 0/84 | 100% | 100% | ~$0.0073 | ~5× cost, same quality |
| openai/gpt-6-luna | 1/84 → 0/84 | 100% | 100% | ~$0.00074 | Half Haiku's cost; one raw error (Ramesh: "high cholesterol not checked" → confirmed) caught by the negation check + verifier |
| deepseek/deepseek-v4.1-flash | — | — | — | — | Dropped: invalid output twice (runaway 12k-char JSON, then empty response) |

- The D7 code tripwire fired on Neha ("screened for chest pain ... none") for both models — a false alarm the
  LLM verifier correctly cleared. Shows the layering: cheap high-recall code check, LLM resolves.
- Caveat: 6 clean synthetic profiles is a small, easy set. Real PEPs are messier and code-mixed; the research
  predicts worse error rates there. This validates the design, not production accuracy.

- GPT-6 Luna's single error is the clearest demo of D7: a negation the model missed, caught by a free code check, fixed by the verifier. Luna is the cost-saving option at higher volume precisely because the checks catch its mistakes.

## Gold cross-check (evaluation-layer bias)

Gold labels were written by Claude (this session). Two non-Claude annotators (gemini-3.1-pro-preview,
gpt-6.1-sol) answered the same questions blind (`scripts/cross_check_gold.py`, $0.12).
- Full agreement on 5 of 6 profiles.
- Ramesh, majority rule (3 voters, 3 providers): `low_salt` added as a restriction (2 of 3);
  `high_cholesterol` stays not-confirmed (2 of 3) — the source sentence "high cholesterol not checked recently"
  is ambiguous, so Luna's flagged error is a judgment call.
- Effect on extraction scores: all three extractors recorded "reduce salt" as the `salt_reduction` intervention,
  not the `low_salt` restriction → +2 misses each, still a three-way tie. No safety impact (confirmed
  hypertension already blocks salty tips).
- Lesson: the vocabulary had two codes for one concept (`salt_reduction` vs `low_salt`) → one concept, one code
  (vocabulary review, D12).
