# Disha Care-Tip Feed — System Design

**Problem:** every day, pick which short health videos ("care tips") each Disha user sees, and in what order —
from a library of thousands, using the user's Patient Executive Profile (PEP), an LLM-maintained free-text
health profile. Hundreds of thousands of users, many Indian languages, a health product where a wrong tip can hurt.

**Answer in one line:** an LLM reads the profile only when it changes; everything that runs daily is plain code
and lookups — a hard safety filter, then ranking by severity — and a prototype shows it shows **0 unsafe tips vs
~19 for random or embedding-only feeds**, at 82% relevance.

---

## 1. What a good feed does (running example: Reema, 27)

Reema has irregular, painful periods, night-shift sleep problems, back pain, leg swelling, a weight-loss goal —
and **unexplained chest pain with left-arm numbness**, urgent evaluation pending. Thyroid/iron/vitamin D tests
are scheduled, not done. She's staying at her parents' home. Her language is Hindi.

A good feed for her today:

1. 📌 *Chest pain? Get checked now* — pinned while the concern is unresolved
2. *Why period cramps happen* — her most severe issue
3. *Warm compress for cramps* — severe issue + something Disha prescribed
4. *Set a daytime sleep block* — prescribed
5. *Build a sleep routine* — another issue, rotating

…and it **never** shows her intense workouts (cardiac concern), "Living with hypothyroidism" (not diagnosed),
or a Tamil-only video. A Kegel tip is shown discreetly (tap to play, neutral title).

## 2. Architecture

```
WHEN THE PROFILE CHANGES  (nightly batch; a new red flag takes a fast path)
 1. LLM extracts a structured profile: coded issues + status + severity, red flags, tests, prescriptions,
    restrictions — each fact with a verbatim quote from the PEP
 2. Checks: code first (quote exists? words fit status? proof for "results received"? danger words missed?
    old-vs-new: did a red flag vanish, a status go backwards?) → LLM verifier only if flagged
    → if still unsure: keep the safer status + send to clinical review
 3. Save as a new timestamped version

EVERY DAY, FOR EVERYONE  (no LLM)
 4. Find tips: exact codes → clinician-reviewed synonym map → embeddings only for leftovers
 5. Safety filter (code): contraindications × red flags, diagnosis lock, clinician restrictions, review status,
    sex/age/pregnancy, diet, language
 6. Rank: severity + recency → slots (pinned safety tip, top issue ≤ 2 of 5, ≥ 1 prescription slot, rotation)
 7. Engagement picks which video fills a slot (never what issue)
 8. Repeat rules → today's feed

OFFLINE: embed new tips once · LLM drafts vocabulary additions → clinicians review · check each language version
```

**LLM vs embeddings vs rules**

| Tool | Where | Why |
|---|---|---|
| LLM | Profile extraction on change (batch); verifying flagged facts; offline vocabulary + judging | Free text with negation and status ("no tests done", "to be completed") needs language understanding |
| Embeddings | Tips once; matching out-of-vocabulary issues; nothing safety-related | Meaning-based fallback; they can't handle negation, so they only *suggest* |
| Code | Checks, safety filter, matching, ranking — everything daily | Predictable, auditable, near-free at 500k users |

## 3. Key decisions (18 logged; the important ones)

| # | Decision | Why |
|---|---|---|
| D1 | A tip = one concept with an English description + tags; each language version is a separate variant with its own title/hook/video | Pipeline reasons in one language; language filter is exact; same tip isn't duplicated across languages |
| D2 | Language fallback: user's language → close language (Hindi ↔ Hinglish) → else skip and log as content demand | Never show a video she can't follow; critical messages never depend on the feed — chat/calls escalate |
| D3 | Tags: relevance, safety (contraindications, exertion, diagnosis lock, sensitive), governance, prescription link, variety | Every filter or ranking rule needs a tag that makes it possible |
| D4 | Red flags block conflicting tips + pin a "get checked" tip — not the whole feed | Keeps reinforcing the escalation; harmless tips still help |
| D5 | Tips assuming a diagnosis stay locked until confirmed; show test-prep tips meanwhile | Don't imply a diagnosis she doesn't have |
| D6 | Sensitive tips always discreet (tap to play, neutral title, user setting) | No need to guess where she's watching from |
| D7 | Every fact carries a status + verbatim quote; layered checks; when unsure, pick the earlier/safer status | "Planned recorded as done" and negation are top documented extraction failures; make errors rare, visible, cheap |
| D8 | Top issue ≤ 2 of 5 slots; ≥ 1 prescription slot; other issues rotate across days | Users watch ~3–5 a day; pure priority would give 5 period tips |
| D11 | LLM extraction only when the profile changes; feed recomposed daily; new red flag → immediate filter | LLM cost scales with changes, not users |
| D13 | Severity decides what she sees; engagement decides how it's shown | Engagement ≠ benefit (weak-evidence health videos get more views) |
| D18 | No personalized feed until basic screening; before that, only universally safe tips | A new user may carry an undisclosed red flag |

## 4. Cost (assumed 100k profile changes/day of ~500k monthly users)

- Extraction: measured ~$0.0015 each (Claude Haiku 5.5) → ~$75/day on batch pricing (~$2.2k/month)
- Verifier on flagged cases: a few dollars/day
- Daily feed for all users: rules + lookups ≈ $0

## 5. Evaluation

**Before launch** — prototype on synthetic data (110 tips with planted traps, 6 test users incl. Reema):

| System | Unsafe tips | Relevant | 3-provider judge panel approves |
|---|---|---|---|
| Random | 19.3 | 53% | 1/6 |
| Embedding-only | 19.0 | 72% | 1/6 |
| **This design** | **0** | **82%** | **6/6** |

- Code metrics are scored against hand-labeled truth, cross-checked blind by two non-Claude models (majority rule).
- Judges (Claude, Gemini, GPT) answer narrow questions: any unsafe tip? would a clinician send this feed?
- **First run, the judges approved only 2/6** — they caught gaps code couldn't (PCOS tips without a diagnosis,
  "cleared for moderate exercise" not treated as a limit, shift-work tips for day workers…). Fixed → 6/6.

**Extraction models** (84 safety-critical checks): Haiku 5.5 0 errors; GPT-6 Luna 1 error, caught by the
negation check; Gemini 3.8 Flash 0 errors at 5× the cost; DeepSeek dropped for invalid output.

**After launch:** system health (flag rates, review queue), weekly clinician audit of sampled feeds, user
response normalized per user (completion, dislikes), and the real outcome — do users follow their care plan?
A/B test against the current feed with a small randomized slice. Never optimize watch time alone.

## 6. What the prototype taught

1. Even strong models mis-tag content → tags need clinical review (38 fixes found).
2. Embeddings can't spot duplicates in a health library (everything "sounds alike") → variety uses tags.
3. Content depth limits the feed: Reema exhausts all 10 period tips by day 5; a Tamil user gets 1 tip.
   The system logs both as content demand.
4. Independent judges catch what code can't — worth running on every change.
5. One concept, one code: overlapping vocabulary codes split models and annotators.

## 7. Limits and open questions

- Synthetic data validates the design, not production thresholds; real PEPs are messier and code-mixed.
- Open questions for Disha: how is the library produced across languages? Fixed daily feed size or endless
  scroll? When is the feed first shown to a new user?

---
*Repo: `plan.md` (full decision log D1–D18), `research.md` (sources), `prototype/` (code, data, `RESULTS.md`).*
