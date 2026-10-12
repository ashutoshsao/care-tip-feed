# Plan — Disha Round 2: Care-Tip Feed

Source of truth for how we're preparing. Design decisions live in the **Decision log** at the bottom and get filled during grilling — nothing here is a design answer yet.

## Goal

Walk into the 45-min session (15 min present + 30 min pushback) with a design I own and can defend, backed by a prototype + numbers.

**Deliverables**
| Piece | Role |
|---|---|
| ~8–10 slides | The presentation — one decision + its trade-off per slide (~12 min) |
| One architecture diagram (Excalidraw) | Lives inside the slides as the anchor slide |
| Prototype on synthetic data | Results shown in 2–3 slides (~3 min): Reema's feed, safety vs baselines, refresh before/after; code ready if asked, no live demo |
| Decision log (bottom of this file) | Backup for the 30-min pushback, not presented; optionally turned into a short write-up at the end |

## Fixed facts (from brief + JD)

- Library: thousands of short vertical videos; title, hook, description + **whatever tags we require** (assume tagged).
- Engagement logged: **viewed, liked, disliked** — no explicit skip signal.
- Daily refresh, **hundreds of thousands of users** (JD: 500k+ MAU, growing fast).
- PEP: LLM-maintained XML with free-text fields; updated after chats/calls; written in English even when user language isn't.
- Disha serves many Indian languages.
- JD signals: "start from the user problem, not a fashionable technique"; "decide what an LLM should handle and what code should enforce"; "let the numbers — not the demo — tell you"; healthcare/safety is a bonus area; prototype → evaluate → hand off is the job.

## How we work

- I answer first, Claude's recommendation revealed after; we discuss the delta.
- Claude evaluates on merit — agrees when right, pushes back when not.
- Facts (costs, techniques, docs) are Claude's job to look up; decisions are mine.
- High effort for design, cost math, eval design, final review; medium for routine work.

## Phases

### Phase 0 — Baseline ✅
- [x] `v0-my-take.md` written without AI
- [x] Gap review (below)

### Phase 0.5 — Landscape research ✅
- [x] `research.md` — options menu per branch, with sources and evidence quality

### Phase 1 — Grill the design tree (in dependency order)
- [x] **1. Tip schema / tags** (D1–D3) — what every tip must carry; concept + language variants
- [x] **2. Filtering & safety** (D4–D6) — irrelevant vs harmful vs premature vs sensitive; hard rules
- [x] **3. User state** (D7, D10) — PEP → structured state (issues, severity, status, flags, pending tests)
- [x] **4. Retrieval** (D12) — embeddings: what's embedded, cross-lingual matching
- [x] **5. Ranking** (D8, D9, D13, D14) — signals, how they combine, feed size, variety vs depth, repeats, engagement normalization, cold start
- [x] **6. Daily refresh** (D11) — event-driven vs nightly; what a PEP diff triggers; latency vs cost
- [x] **7. Scale & cost** (D15, system-overview.md) — LLM vs embeddings vs rules per component; back-of-envelope at 500k users
- [x] **8. Evaluation** (D16, D17) — pre-launch vs random baseline; post-launch metrics; engagement ≠ benefit

### Phase 2 — Prototype ✅ (results: prototype/RESULTS.md)
1. [x] Schemas from Phase 1 (Tip, UserState)
2. [x] Synthetic library ~150–200 tips (text only) incl. deliberate traps: high-intensity workouts, presumed diagnoses, sexual-wellness, wrong-language, near-duplicates — hand-review a sample
3. [x] Synthetic PEPs: Reema + male lifter, pregnant, diabetic, thin profile; **Reema v2** (blood results back)
4. [x] Extraction PEP → UserState + eval vs hand labels (safety-flag recall must be 100%)
5. [x] Safety filter as rules + test per trap
6. [x] Embedding retrieval per issue
7. [x] Ranking + slot quotas + diversity
8. [x] Simulated 7-day engagement logs
9. [x] **Eval harness** — random vs embedding-only (plain semantic search) vs full system; metrics: safety violations, judge score, issue coverage, intervention reinforcement
10. [x] Refresh demo v1 → v2: feed diff + only changed users reprocessed
11. [x] Report (markdown/HTML) → feeds the prototype slides

### Phase 3 — Deliverables
- [ ] Architecture diagram (Excalidraw)
- [ ] Slides (diagram + prototype results inside)
- [ ] Optional: short write-up from the decision log

### Phase 4 — One dry run
- [ ] 15-min present + ~15 min pushback + debrief

## Tooling & models (provisional — final picks are a Phase 1/2 decision)

Available: **OpenRouter** (any hosted model) + **Ollama** (local open models). Python + uv, run locally.

| Job | When it runs | Starting choice | Experiment |
|---|---|---|---|
| PEP → structured state | On PEP change only | Small/fast hosted model | Compare vs a local open model on Ollama — accuracy vs cost |
| Synthetic library + PEP generation | Once (prototype only) | Mid-tier hosted model | — |
| Embeddings | Once per tip; per issue on PEP change | Local multilingual model via Ollama (verify availability) | Single combined vs per-field embeddings |
| Feed judge | Offline, sampled | Strong model, **different family from the generator** (reduce self-preference) | Calibrate vs my hand labels |
| Daily feed | Daily, every user | **No LLM** — rules + embeddings + scoring | — |
| Tip transcription (STT) | Once per video at ingestion | Indic-capable batch STT — one line in the doc; skipped in prototype | — |

No agents: every LLM use is a single structured-output call.

## Gap review of v0 (ranked by interview risk)

1. **Safety missing** — filtering treated as relevance only; health needs harm-first
2. **Scale assumption wrong** — wrote 10k users; brief says hundreds of thousands
3. **Tags too thin** — every rule needs a tag that makes it possible
4. **Ranking has signals, no mechanism** — PEP parsing, combining, feed size, variety call
5. **Evaluation blank** — pre-launch vs random; post-launch metrics (raised in priority after reading JD)
6. **Refresh skips "at what cost"**
7. **Reema's hand feed** — too few, too generic; ignores prescribed interventions; empty "won't show" list

Strengths to keep: dual purpose framing, 3-tier relevance (good-to-know backfill), diff-based recompute, engagement-noise skepticism (→ per-user normalization).

## Notes carried forward

- Alternative considered: "recsys, no LLM, multiple vector DBs" — keep the recsys framing and no-LLM daily path; reject "no LLM anywhere" (status/negation in PEP) and "embeddings are enough" (safety must be rules); multiple vector DBs is overkill (~5k tips × few vectors ≈ <200 MB, in memory).
- Transcripts: require them; ~150 tokens each → no chunking; main value is tagging/safety.
- Languages: hard filter; tip = concept + language variants; fallback policy; English PEP vs Hindi transcript = cross-lingual retrieval.
- LiveKit/Pipecat belong to Round 3 (real-time), not batch transcription.
- Round 3 reuses the PEP and the chest-pain case — safety-layer thinking carries over.

## Assumptions (state them on a slide)

- The library is already tagged the way we specify (brief). Safety tags are clinically reviewed; who/how tagging happens is out of scope.

- A tip is a concept with **one or more** language variants; how variants are produced (native shoots, dubbing, single-language) is the content team's call and out of scope — like taxonomy authoring. The pipeline only organizes existing videos. Concept grouping also dedupes cross-language duplicates.

## Questions to send Disha before the session

3. When is the feed first shown to a new user — only after the PEP reaches some completeness, or from day one?
2. Does the feed have a fixed size per day (e.g., a set of N tips) or is it an endless scroll? How many tips does a typical user watch per day?
1. How is the library produced across languages — native shoots per language, dubbing, or one language per video? Roughly what share of tips exist in Hindi / English / other languages?

## Decision log

| # | Decision | Why | Alternatives rejected |
|---|---|---|---|
| D1 | Tip = language-neutral concept with one canonical English description + tags; each language version is a separate **variant** record (tip_id, language, user-facing title/hook/description in that language, video_url, transcript, duration). Pipeline metadata stays English on the concept; everything the user sees lives on the variant. System supports N languages; rollout prioritized by per-language library coverage (track coverage per language as a content-production signal). Language is a structured field on the variant, not text in the description. Each variant's transcript is checked offline against the canonical (LLM consistency check → clinical review if flagged). Native-only tips still get a canonical English description with a single variant. | Pipeline reasons over one English representation; language filter becomes exact; matches deployed Indian pattern (Jugalbandi pivot); consistency check closes the gap where a variant says something the canonical tags don't cover | Each language's video as an independent tip with its **pipeline metadata** (description, tags) in its own language — native-language *videos* are fully supported as variants; what's rejected is native-language *metadata*, which would force cross-lingual matching everywhere and duplicate the same tip across languages; language mentioned inside the description text (fuzzy filtering) |
| D2 | Language fallback ladder: (1) variant in user's language → show; (2) close language (Hindi ↔ Hinglish) → show; (3) none + low priority → skip, log as content demand; (4) none + high priority → show with subtitles in user's language only if they exist, else skip. Critical messages (e.g., urgent evaluation) never depend on the feed — chat/call/care team own escalation; the feed only reinforces. | Keeps feed comprehensible; turns gaps into a content-production signal; safety never hinges on video availability | Subtitles as the default fallback (assumes comfortable reading while watching); showing any-language video; feed as the escalation channel |
| D3 | Tip tags (all required): **Identity** (tip_id, canonical EN description, variants) · **Relevance** (conditions, symptoms, goals, audience/life stage, general_wellness flag) · **Safety** (contraindications, exertion level, requires_confirmed_diagnosis, sensitivity) · **Clinical governance** (review status, reviewed_on, review_due, evidence level) · **Intervention link** (prescribed interventions it reinforces) · **Variety** (tip type why/what/how-to/myth, topic cluster, near-duplicate group computed from embeddings) · **Ops** (duration, published date). Relevance/safety/intervention tags share one coded vocabulary with the structured profile. | Every filter/ranking rule needs a tag that makes it possible; shared codes make matching mostly exact (practitioner research) | Free-text-only metadata matched by embeddings (can't express safety or status) |
| D4 | Red-flag handling is **per tip, not whole feed**: hide tips whose contraindications match the user's flag (e.g., high-exertion workouts while chest pain is unresolved); **pin** a reinforcement tip ("if you feel this, contact a clinician now") with a CTA (talk to Disha / book consult) until the flag is cleared; keep all other safe tips. Whole-feed suppression only for a short explicit list of crisis states (e.g., suicidal ideation). | Keeps the feed reinforcing the escalation chat/calls already own; harmless tips (sleep, periods) still help; fails closed only where the risk is | Suppressing the whole feed for any high-priority condition (loses reinforcement channel); letting the reinforcement tip compete in ranking |
| D5 | Tips tagged `requires_confirmed_diagnosis` stay locked while the condition is only suspected or tests are pending; show test-related tips instead ("what a thyroid test checks", "how to prepare"). Unlock when the profile shows the condition confirmed. | Avoids implying a diagnosis the user doesn't have (fear, misinformation); still useful while waiting | Showing condition-management tips based on suspicion or pending tests |
| D6 | Sensitive tips (sexual/mental health) always shown in **discreet mode**, regardless of context: no autoplay with sound (tap to play), neutral title/thumbnail (e.g., "Pelvic floor strength"), plus a user setting to hide sensitive tips. | Doesn't depend on inferring location from a possibly stale PEP ("returning next week"); keeps reinforcing prescribed interventions (Kegels 3×/day); user keeps control | Hiding sensitive tips while user is at parents' home (stale context, loses reinforcement) |
| D7 | Profile facts carry an **assertion status** (tests: advised → scheduled → sample collected → results received; conditions: suspected / confirmed / resolved / absent) + a **required source quote**. A rule-based cue checker ("to be", "scheduled", "pending", "no … done", Hindi cues) runs beside the LLM; disagreement → flag/re-extract. **Forward moves need proof** (e.g., "results received" only if result values are present). **When unsure, pick the earlier status** — wrong-"scheduled" costs a day of prep tips; wrong-"done" shows results-dependent tips and kills reminders. Residual error measured with planned-vs-done traps in the prototype. **Verification layering:** (1) code on every extraction — quote exists verbatim in PEP, cue words consistent with status, proof present for forward moves; (2) second LLM yes/no check (different model family) only when code flags or a safety field is involved; (3) unresolved → keep safer status + clinical review queue. **Old-vs-new diff checks** (same three layers): red flag removed without a clearance quote, status moving backwards, chronic condition vanishing → flag. | Planned-as-completed and negation are documented top failure classes in clinical extraction; asymmetric error costs justify asymmetric thresholds; goal = errors rare, visible, cheap | Bare yes/no "tested" flag (can't express stages); trusting LLM status alone |
| D8 | Feed composition for the top slots (what users actually watch): slot 1 = pinned safety tip when a flag is active (D4); **highest-priority issue capped at 2 of top 5**; **≥1 slot for a tip reinforcing a prescribed intervention**; lower-priority issues **rotate across days** (variety across the week, not just within a day). Filter → score → compose. | Users watch ~3–5/day, so top slots matter most; pure priority sort would give 5 period tips and starve sleep/weight/back; rotation covers ~10 issues over a week | Endless list sorted purely by priority; equal slots for all issues regardless of severity |
| D9 | Repetition rules: never repeat the **exact video** a user disliked, but keep the **topic** (show a different video on the same issue — different angle/format); weak signals (viewed, not liked) may repeat; show new tips first; bring back prescription-reinforcing tips (e.g., Kegels) after ~a week; pinned safety tip is never removed by a dislike — swap to a different video with the same message. | Dislike is the only explicit negative signal; ignoring it erodes trust; the issue still matters even if one video didn't land; safety outranks preference | Repeating disliked videos ("maybe next time"); repeat only after everything is viewed (too rigid, kills useful reinforcement) |
| D10 | Structured profile (feed-only) holds **only fields some rule uses**: language, sex, age, life_stage; red_flags (code, status, quote); issues (code, severity/chronic, quote) incl. sensitive ones (vaginal laxity) and fatigue/stress; tests (code, status ladder, quote); goals; interventions; explicit clinician `restrictions` (with quote); diet_type; workout_setting. Flag-derived restrictions are NOT inferred per user — they come from tip contraindication tags × flags. Core (red flags + test status) is reusable by chat/call agents — mention as extension, not in scope. | Fewer fields = fewer extraction errors and cheaper; medical "what conflicts with what" lives in clinically reviewed tip tags; agents already get the full free-text PEP, and more context isn't better for them | Extracting everything "for agents" (context dilution, loses nuance, scope creep); LLM inferring restrictions per user |
| D11 | Two-step refresh: **profile extraction only when the PEP changed** (re-extract the whole profile, then diff old vs new structured profile; diff drives unlocks like tests scheduled → results received); **feed composition daily for everyone** (cheap: rules + precomputed scores; needed for novelty, rotation, dislikes, new tips). **Safety fast path:** a new red flag (event from chat/call) immediately removes now-unsafe tips from today's feed and pins the reinforcement tip — no LLM, no full re-rank; everything else waits for tomorrow. | LLM cost scales with profile changes, not users; daily recompose keeps the feed fresh; this morning's feed may hold a now-unsafe tip (e.g., intense workout) — rare event, cheap filter; escalation itself stays with chat/call (D2) | Full rebuild from scratch daily for everyone (wasteful LLM spend); patching only the changed sentence (error-prone); waiting until tomorrow for new red flags (unsafe tip live for hours) |
| D12 | Matching tips to the profile: extraction outputs codes from a **controlled vocabulary** (list given to the LLM); a **synonym/relation map** (e.g., shift_work_sleep ↔ circadian_rhythm) is built **once offline** — LLM drafts, clinical team reviews — then used as a free code lookup daily; **embeddings are a safety net** for anything still unmatched. Embeddings only see issues already marked *present* (negation/status resolved upstream by D7), only **suggest** candidates (every candidate still passes the code safety filter), and use a minimum similarity threshold. Out-of-vocabulary facts → `other` + quote → embeddings for now + logged to grow the vocabulary. | Per-user LLM matching or per-user clinical review doesn't scale to 500k users; clinical review moves to the vocabulary where it scales; embedding errors can only cost relevance, never safety | LLM matching per user per day (cost); clinical review of individual matches (doesn't scale); embeddings as primary or deciding safety (can't handle negation) |
| D13 | **Severity decides what she sees; engagement decides how it's shown.** Likes/dislikes never move an issue's priority or slot count (D8); they choose *which video* fills each slot — style, format, angle (e.g., she likes short how-to → period slots get how-to videos). Engagement normalized against the user's own baseline. | Keeps health priority from drifting toward what feels pleasant (engagement ≠ benefit; JAMA: weak-evidence videos get more views); still uses the only preference signals we log | Likes boosting an issue's priority (engagement-driven drift); ignoring likes entirely (wasted signal) |
| D14 | Issue priority = **severity first**, then a **recency boost** that decays over ~2 weeks; older issues keep rotation slots (D8); confirmed chronic issues keep a floor share. Recency comes from **versioned structured profiles** — every extraction stored append-only with a timestamp (first_seen / last_changed per fact via the D11 diff). Versions also power D7 diff checks, per-tip explanations ("shown because profile v12, issue X"), and replay for evaluation. Retention period + access controls (health data, DPDP Act). | Brief asks for "which issues are most active right now"; a recent mention is evidence it's active, an old one may be resolved-but-stale; PEP has no per-issue dates, the diff gives them for free | Older unsolved issue ranked higher (stale PEP risk); equal rotation ignoring recency (loses the "active now" signal); overwriting the profile in place (no history, no audit, no replay) |
| D15 | Ordinary profile extractions run as a **nightly batch** (provider batch APIs ≈ 50% off: Haiku 5.5 $0.10/$0.50 → $0.05/$0.25 per M tokens). Start late night; **if a user's result isn't back by morning, use their previous profile version** (D14) for one more day. Red flags bypass via the fast path (D11). Cost at 50k–100k profile changes/day (assumed ~10–20% of 500k MAU): **measured** Haiku 5.5 extraction ≈ $0.0015 each (prompt + schema ≈ 3× the earlier estimate) → ≈ $150/day real-time, ≈ $75/day batch (~$2.2k/month) at 100k; verifier on ~10% flagged ≈ a few $; daily composition for all users ≈ near-zero (rules + lookups). | Feed only needs to be ready tomorrow; LLM cost scales with profile changes, not users; batch SLA is "within 24h", so a fallback is needed | Real-time extraction after every chat (2× cost, no benefit for next-day feed) |
| D16 | **Pre-launch eval** = a measured comparison, not an argument: same synthetic users (Reema + 4 contrasting), feeds from **random vs embedding-only (plain semantic search) vs full system**, scored mostly by code (planted ground truth): unsafe tips shown (target 0), share matching real issues, top slot = most urgent issue, issue coverage, prescription reinforced; LLM judge only for what code can't check (narrow pass/fail + expected-topics checklist, calibrated to hand labels, different model family). **Headline: "0 unsafe tips vs X (random) / Y (embedding-only), with 90%+ relevance"** — safety paired with relevance so an all-generic feed can't game it. Caveat stated upfront: synthetic data validates the design, not production thresholds. | JD: "let the numbers, not the demo, tell you"; ablation shows what each layer earns; unsafe-tip count is the most differentiating number for a health product | "It's better because it's designed better" (argument, not evidence); holistic judge score as the main metric (preference ≠ safety) |
| D17 | **Post-launch monitoring, four layers:** (1) system health — extraction flag rate (trend; zero is as suspicious as a spike), clinical queue size, batch done by morning, safety-filter block counts; (2) safety in the wild — weekly clinician audit of a random sample of feeds + user reports; (3) user response — completion, dislike rate, normalized per user; (4) outcome — care-plan adherence (prescriptions followed, tests completed) per later chats/PEP updates. Attribution via **A/B test** vs current feed + a small randomized slice with logged propensities. Never optimize watch time alone. | Health and engagement can diverge (weak-evidence videos get more views); adherence is what the feed is for ("reinforces what Disha tells them"); A/B + random slice enables causal claims and later offline replay | Engagement/watch time as the north star; monitoring only pipeline health |
| D18 | **Cold start:** no personalized feed until a minimum profile exists (red-flag screening, pregnancy status, major conditions covered); before that, only tips tagged `universally_safe` (how Disha works, hydration, sleep basics — no exercise/diet). Assumption to confirm with Disha. Gap is short: new users average 17 min with Disha on day one (JD). | A new user may carry undisclosed red flags; "general" tips like workouts can be unsafe without screening | Generic feed of any general-wellness tips from day zero (unsafe without screening) |
