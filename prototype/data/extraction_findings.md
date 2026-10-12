# Extraction comparison (prototype step 4) — 2026-10-12

6 profiles × 2 runs per model; 84 safety-critical checks per model (red flags, negation, family history,
planned-vs-done tests, pregnancy, explicit restrictions, language).

| Model | Critical errors (raw → after checks) | Issue recall | Intervention recall | $/extraction | Notes |
|---|---|---|---|---|---|
| anthropic/claude-haiku-5.5 | 0/84 → 0/84 | 100% | 100% | ~$0.0015 | Pick: cheapest, no errors |
| google/gemini-3.8-flash | 0/84 → 0/84 | 100% | 100% | ~$0.0073 | ~5× cost, same quality |
| deepseek/deepseek-v4.1-flash | — | — | — | — | Dropped: invalid output twice (runaway 12k-char JSON, then empty response) |

- The D7 code tripwire fired on Neha ("screened for chest pain ... none") for both models — a false alarm the
  LLM verifier correctly cleared. Shows the layering: cheap high-recall code check, LLM resolves.
- Caveat: 6 clean synthetic profiles is a small, easy set. Real PEPs are messier and code-mixed; the research
  predicts worse error rates there. This validates the design, not production accuracy.
