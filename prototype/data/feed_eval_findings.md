# Feed evaluation (prototype step 9) — 2026-10-12

6 users (Reema v1/v2, Arjun, Priya, Ramesh, Neha). Code metrics scored against a reference profile built
from the cross-checked gold labels (not the system's own extraction). Random = mean of 20 draws.
Judge panel: claude-sonnet-5.5, gemini-3.1-pro-preview, gpt-6.1-sol — narrow questions (unsafe tips? would a
clinician send this feed?), majority vote.

| System | Unsafe tips (total, 6 users) | Relevant | Judges: clinician OK (majority) |
|---|---|---|---|
| Random | 19.3 | 53% | 1/6 |
| Embedding-only (mentor's design) | 12.0 | 72% | 1/6 |
| **Full system** | **0** | **82%** | **6/6** |

Headline: **0 unsafe tips vs 19 for random and 12 for embedding-only, at 82% relevance; all 3 judges' majority
approves 6/6 of our feeds vs 1/6 for each baseline.**

## How we got here — first run failed the judges (2/6), and that was the useful part
The first run scored 0 unsafe by code but judges approved only 2/6. They found gaps code couldn't see:
- PCOS tips shown without a PCOS diagnosis → tag gap (diagnosis lock missing)
- HIIT after "cleared for moderate exercise" → clearance-with-limit now extracted as a restriction
- Test-prep tip after results came back → `prep_for_test` tag, shown only while pending
- Shift-work tips for day workers → synonym map too broad (insomnia ↔ circadian_rhythm) + my wrong tag fix
- Strength training despite "avoid strenuous exercise" → restriction now blocks moderate + high
- Severe-anxiety tip in backfill → backfill excludes sensitive tips
This is the JD's loop: prototype → evaluate → find where it fails → fix → re-evaluate.

## Remaining dissent (1 judge of 3 each, majority approves)
- Reema v1: GPT flagged a gentle cat-cow stretch while chest pain is unassessed (conservative view).
- Arjun: Gemini flagged a gym warm-up that may include treadmill running with his knee.

## Honest limits
- Priya's feed has 1 tip: the library has almost no Tamil videos — a content gap the system logs, not a ranking bug.
- Ramesh: one of two extraction runs missed `low_salt` (two codes for one concept — vocabulary fix).
- Synthetic data, 6 users: validates the design, not production thresholds.
- Judge calls run in parallel: ~1 min (was ~6 min sequential).
