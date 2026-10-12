# Research — options menu for the care-tip feed

Researched 2026-10-12. Purpose: a menu of what's actually used, per design branch, so grilling picks between real options. **Nothing here is a decision.** Evidence quality is flagged; preprints and blogs are marked as such.

---

## 1. Overall pipeline shape

**Industry standard: multi-stage funnel.** Candidate generation (narrow thousands → hundreds) → scoring/ranking → re-ranking (diversity, freshness, business rules). [Google recsys overview]
- Re-ranking in short-video systems handles tens–hundreds of candidates and is where **rule-based business logic** (filtering, diversity) lives. [short-video personalization paper, 2409.11281]
- Hard filters (blocked, duplicates, geo) and soft filters (quality, min engagement) applied **before** ranking. [system-design walkthrough — blog quality]
- Caution from sources: diversity applied only at re-ranking can be too late if retrieval already made the pool homogeneous.

**Relevance to Disha:** the funnel maps cleanly — but Disha's library is only thousands, so "candidate generation" can be near-exhaustive (score every eligible tip). The funnel's real job here is ordering filters → scoring → re-ranking, not cutting compute.

**Options:** (a) classic 3-stage funnel; (b) collapsed 2-stage (filter → score+rerank) given small library.

---

## 2. Where LLMs sit in production recsys

**Dominant production pattern: LLM offline, classic model online.** Batch jobs extract attributes, normalize descriptions, tag items, summarize users → become features for the ranker. No added serving latency. Most practical value = offline enrichment + semantic retrieval + hybrid ranking. [Eugene Yan, recsys-llm; LF AI & Data 2025]
- **LLM-written user profiles** are an active direction: PURE (LLM-maintained profiles from history/reviews) [2502.14541]; YouTube-scale personas distilled from a large model to small students, generated async in background — tiny but significant A/B gains (+0.04% watch time). [2606.12198 — via AI review site, verify]
- **LLM rerankers** shine on cold/sparse users but are slow/expensive per request. [practitioner talk via Eugene Yan]

**Relevance to Disha:** Disha *already* has an LLM-maintained profile (the PEP) — it's ahead of most recsys here. The industry pattern (LLM offline → structured features → cheap online scoring) is exactly "extract structured state on PEP change, no LLM in daily path."

**Options:** (a) LLM extracts structured state on PEP change (offline-ish); (b) piggyback extraction onto the existing PEP-update call; (c) LLM reranker on top-N (rejected by cost at 500k daily unless only for cold users).

---

## 3. Extracting structured state from the PEP (negation, status, temporality)

- Small open models reached **human-level clinical extraction** on desktop hardware with ≤100 training examples. [Scientific Reports 2025]
- Instruction-tuned LLMs beat BERT on clinical IE across datasets; study covered modifiers incl. **negation and certainty**. [JAMIA 2026]
- Real-world field accuracy varies widely (74–90%); **dates/temporality are the weakest** (one field at 17%). Hallucination rare (0.16%). [oncology validation studies]
- Rule-based approaches struggle with negation, uncertainty, temporal reasoning. [2026 review]

**Relevance to Disha:** "no thyroid tests done", "tests pending", "urgent evaluation advised" are exactly negation/status/temporality — the known weak spots. Implies: (1) measure extraction per field, (2) **safety flags need their own recall target and fallback** (e.g., keyword tripwire as backstop), (3) small model is plausible but must be proven.

**Options:** small hosted model / local open model / mid-tier model — compare on a hand-labeled set (prototype step 4).

---

## 4. Embeddings & multilingual retrieval

- **Qwen3-Embedding** (0.6B/4B/8B, 100+ languages; 8B was #1 MTEB multilingual mid-2025) — available on Ollama. [model card, Ollama registry]
- **BGE-M3** (568M, 100+ languages, 8k context, dense + sparse + multi-vector) — available on Ollama. Strong on Indic monolingual retrieval; **not best on cross-lingual transfer** (E5-Large-Instruct led there) in a 2026 Indic benchmark. [secondary summary — verify]
- Hindi-specific: Hindi-BEIR benchmark; NLLB-E5 beat BGE-M3 on several Hindi tasks. [2408.09437, 2409.05401]
- No 2026 head-to-head on Hindi cross-lingual found → **we should test it ourselves** in the prototype (English PEP issue ↔ Hindi transcript).

**Options:** qwen3-embedding (0.6B for speed / 4B for quality), bge-m3, multilingual-e5. Single combined vector vs per-field vectors.

---

## 5. Safety / contraindication filtering in health content

- **Little published on contraindication filtering in health content feeds** — a genuine gap. Closest analog: profile-based drug-interaction alerting that matches content to the patient's record and explains the trigger. [USPTO patent]
- Flo (closest consumer analog): content co-created with 120+ doctors, **each piece reviewed by two experts**; mechanism of personalization not public. [Flo official]
- Ginger (mental health, 14k users): recommendations framed as reducing choice overload; no safety filtering discussed. [PMC9896352]
- Content quality risk is real: 62.5% of claims in clinician-made YouTube health videos had very low/no evidence, and those got ~35% more views. [JAMA Netw Open 2026] Generic video-quality scores correlate poorly with evidence.
- YouTube's medical policy anchors to health-authority guidance and public-health risk. [YouTube policy]

**Relevance to Disha:** no off-the-shelf pattern → designing the safety layer from first principles is where we can stand out. Also: **engagement-optimized ranking would actively favor weaker-evidence content** (the JAMA finding) — a strong argument for not ranking on engagement alone.

**Options for the layer:** hard exclusion rules on tags × user flags; "hold until condition cleared" states; mandatory/pinned tips; clinical review tier on the tip itself (evidence grade, reviewer sign-off) as a tag.

---

## 6. Ranking objective: engagement vs benefit

- Engagement-maximizing designs linked to low-quality info spread, reduced satisfaction, overuse; alternative = surveys, stated preferences, long-term value. [Knight-Georgetown Institute 2025; Stray & Hadfield / WIRED]
- Adding wellbeing objectives makes optimization harder; novelty vs relevance tension. [Positive AI, 2304.12241]
- No empirical study found measuring *health outcomes* from engagement vs wellbeing ranking.

**Relevance to Disha:** supports engagement as a *secondary, normalized* signal, with clinical relevance/priority primary. Post-launch metrics should include stated feedback and downstream behavior (e.g., adherence mentioned in chat), not just watch time.

---

## 7. Diversity / variety vs depth

- **MMR and DPP**: greedy selection balancing relevance and diversity; quadratic cost → used at re-ranking (fine for tens–hundreds of items). Kuaishou distilled MMR into a model for scale. [2406.09021]
- Short-video platforms model perceived diversity with a **sliding window** over recent items. [WWW 2024]
- Slot quotas per category: common in practice, **no source found** — would be our own design choice.

**Options:** MMR over issue-tagged candidates; hard per-issue slot quotas; sliding-window "don't repeat issue within k slots"; or a hybrid (quota for priority issue + MMR for the rest).

---

## 8. Cold start & exploration

- Meta used **Thompson sampling** (via epinets) for content cold start in Reels retrieval — gains in like rate and completion. [2412.04484]
- Framed as a non-stationary contextual bandit since the pool keeps changing.

**Relevance to Disha:** two cold starts — new tips (no engagement) and new users (thin PEP). A full bandit is likely overkill for a v1 with thousands of tips; a simple exploration slot or optimistic prior may do. Decision for grilling.

---

## 9. Evaluation

**Offline with LLM-as-judge**
- Recsys-specific LLM-judge frameworks exist (2026 preprints). Key check: does the judge **preserve the ranking of systems** that human labels give (Kendall's τ), not just per-item agreement. [2606.22961, 2607.11354]
- Calibrate against a small human-labeled gold set (~30–200 examples), report agreement (Cohen's κ, correlation), correct for judge bias. [2511.21140; Langfuse, Galtea — vendor]
- Known judge biases: position/order, length, **self-preference** → use a different model family from the generator. [2608.15877]

**Offline from logs (after some traffic exists)**
- Off-policy evaluation: IPS (unbiased but high variance), SNIPS, doubly robust; diagnostics like effective sample size and clipping sensitivity. Slates complicate IPS. [2509.00333, ICML 2019 CAB, 2007.12986]
- Practical note: needs logged propensities — so **log the probability each tip was shown from day one**, even if we don't use OPE yet.

**Online**
- A/B vs current/random; guardrail metrics; beyond-engagement measures (section 6).

**Relevance to Disha:** pre-launch story = clinician-labeled gold feeds + calibrated LLM judge + safety-violation count vs random and vs embedding-only. Post-launch = A/B with safety guardrails, normalized engagement, dislikes, stated feedback, downstream behavior.

---

## 10. Model candidates & prices (OpenRouter API, pulled 2026-10-12)

| Model | In $/M tok | Out $/M tok | Batch in/out |
|---|---|---|---|
| anthropic/claude-haiku-5.5 | 0.10 | 0.50 | 0.05 / 0.25 |
| deepseek/deepseek-v4.1-flash | 0.30 | 1.20 | 0.112 / 0.336 |
| google/gemini-3.8-flash | 0.75 | 3.75 | 0.375 / 1.875 |
| anthropic/claude-sonnet-5.5 | 2.00 | 10.00 | 1.00 / 5.00 |

Per PEP extraction (assume ~2.5k in, ~600 out): Haiku 5.5 ≈ $0.00055 · DeepSeek v4.1 Flash ≈ $0.0015 · Gemini 3.8 Flash ≈ $0.0041 (batch ≈ half or less).
At an *assumed* 100k PEP changes/day: ≈ $55 / $147 / $410 per day real-time. Quality unknown → prototype step 4 decides.
Batch fits a next-day refresh. Privacy: PEP is health data — provider data handling/residency (India DPDP Act) is a selection criterion, not just price.

**Embedding candidate added:** EmbeddingGemma 2 (Google, ~Oct 2026, Apache 2.0) — 740M, **multimodal** (text/image/video/audio in one 768-d space), 100+ languages, Matryoshka 128–768d, 8K context. Very new → little independent Hindi benchmarking. Could embed videos directly, but safety still needs tags/transcripts. [model card](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2)

---

## 11. Indic voice/language vendors (relevance: Round 2 = transcripts only; mostly Round 3)

- **Sarvam** — STT Saaras v3 (default since Jun 2026) with **`mode="translate"`: Hindi/Indic speech → English text directly**; realtime variant saaras:v3-realtime (Aug 2026). Translation: Mayura (11 langs), Sarvam Translate (23). LLMs: sarvam-30b / sarvam-105b. TTS: Bulbul v3. No embedding model found. Claims ~19.3% WER avg on IndicVoices top-10, beating Scribe v2 / GPT-4o Transcribe / Gemini 3 Pro / Nova-3 — vendor claim via press. [docs](https://docs.sarvam.ai/api/getting-started/models)
- **Smallest.ai** — Pulse STT (32 langs, auto-detect, South Indic streaming India-region only) and Lightning v3.1 TTS (~200ms TTFB). Real-time/voice-agent focus. Docs conflict on language counts. [docs](https://docs.smallest.ai/models)
- **ElevenLabs** — Scribe v2 STT; self-reported Hindi WER 5.5% FLEURS (inconsistent across its own pages); one Aug 2026 report: 5.9% Hindi → 19.6% Telugu on unscripted phone speech. [Hindi page](https://elevenlabs.io/speech-to-text/hindi)
- All head-to-heads are vendor or competitor published → **test on own audio**.

**Round 2 use:** transcribe tip videos once, offline. Sarvam's speech→English translate mode is a candidate fix for cross-lingual matching: store native transcript (for display/QA) + English translation (for tagging/embedding). TTS and realtime latency → Round 3.

---

## 12. Practitioner pass (Reddit blocked for search tool; used HN + practitioner sources)

**Changes our eval design:**
- **"Preferred, Not Safer" (2608.02617):** pairwise preference is a poor proxy for clinical safety → safety must stay a separate, code-checked hard metric; never inferred from "which feed is better." [arXiv](https://arxiv.org/pdf/2608.02617)
- **Hamel Husain's evals practice (via secondary summaries):** binary pass/fail per specific failure mode, not composite scores; exhaust code checks before any LLM judge; do error analysis first; ≥20 pass + 20 fail labeled examples per failure mode; measure judges by TPR/TNR, not accuracy (an always-"pass" judge looks accurate on imbalanced data). [ChatPRD recap](https://chatprd.ai/how-i-ai/hamel-husains-guide-to-ai-evals-with-error-analysis), [evals-skills](https://www.skills.sh/hamelsmu/evals-skills/write-judge-prompt)
  → Use LLM judges as **narrow binary checks** for semantic failures code can't catch (e.g., "does this tip presume a diagnosis the user doesn't have?"), with pairwise holistic comparison only as a secondary signal.
- Position bias varies by judge model and dataset; order-swapping reduces but doesn't remove it. [2602.02219](https://arxiv.org/pdf/2602.02219), [2603.29403](https://arxiv.org/pdf/2603.29403)

**Health recommender reviews:**
- 69% of personalized interventions used only one personalization dimension; evidence of personalization's impact is weak/mixed. [T&F scoping review](https://www.tandfonline.com/doi/full/10.1080/0144929X.2024.2356630)
- Abandonment linked to low perceived personal relevance. Users trust recommendations more when they have some control / self-reported preferences. [weight-mgmt review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11791383/), [Athletech](https://athletechnews.com/when-it-comes-to-personalization-health-fitness-consumers-want-privacy/)

**Infra pattern:** Pinterest ItemSage recomputes embeddings in a daily batch and shares one embedding set across surfaces (3× lower infra cost). [2205.11728](https://arxiv.org/pdf/2205.11728)

HN signal on small-catalog recsys was thin/anecdotal ("academic recsys often don't transfer to real data"). [HN](https://news.ycombinator.com/item?id=30496322)

---

## 13. Claude web practitioner research — merged (2026-10-12)

Full doc: https://claude.ai/code/artifact/79f30b9f-fadc-4d75-bdfa-8db5322a0dec — strongest practitioner evidence we have. Key items by branch:

**Safety / filtering (branch 2)**
- Eligibility = hard pre-filter owned by clinicians; never let the ranker learn safety. Ada: knowledge base stays the guardrail; doctors review content pre-publish + 5,000 reference cases per release (vendor).
- **Failure stories for the interview:** NEDA's Tessa pulled for giving dieting advice to people with eating disorders — the harmful text was *pre-scripted*, not generative (NPR 2023). Noom's ED question only showed a warning and could be changed (Business Insider). Lesson: soft gates fail → **fail closed**.
- Open question for grilling: fail closed = suppress whole feed (doc §3) vs safe default set + pinned escalation (doc §1). The doc is inconsistent on this.

**User state extraction (branch 3)**
- Ambient-scribe evidence (same job as PEP): negation ≈ 30% of hallucinations; omissions most common and hardest to detect; **"planned written as done"** and **relative time → fake date** are named failure classes. Reema-relevant: "blood tests to be completed this week", "returning next week".
- Store facts as (entity, assertion status enum, time, source span); no span → can't unlock/block content alone.
- Rule-based negation checker beside the LLM (rule F1 ≈ LLM, 1000× faster); route disagreements to review.
- Urgency flags = separate high-recall classifier, not a side effect of summarization.
- Expect worse errors in Indic/code-mixed text (GP survey: 31% vs English).

**Retrieval (branch 4)**
- Deployed Indian pattern = **translate-to-English pivot** (Jugalbandi), not native cross-lingual embeddings.
- **Code-space matching** (profile codes ↔ tip codes) as primary; embeddings only as soft layer on English canonical descriptions → cross-lingual mostly moot at serve time.
- Hindi-BEIR cross-lingual: BGE-M3 34.4, mE5-large 35.0; LaBSE 5.6 and BM25 ≈ 0 → avoid those.
- Headspace picked its embedding model by **spread of cosine scores on its own catalog** (wellness items all look similar) → add to our embedding eval.

**Ranking (branch 5)**
- Headspace (~1,000 items, near our scale): nightly batch; removes recently completed; first learned model (LightFM) had offline wins, **no online lift**; semantic-sampling diversity re-rank +2.26% starts, coverage +13–27%.
- Duolingo recovering bandit: penalize recently used arms; "sleeping arms" = items ineligible for some users → maps to cooldowns + eligibility.
- **Flo: each personalized topic needed 40+ pieces for a daily cadence** → library-depth check per topic before promising daily coverage.
- Intercom LLM reranker: +5 s → +0.9 s after optimization, then distilled. Listwise LLM rerank viable only for 5–10 items.

**Evaluation (branch 8)**
- Offline metrics are screens, not verdicts (Headspace).
- LLM judges catch **commission** (wrong/unsafe content) well but **omission** near chance → give the judge an explicit expected-topics checklist per profile.
- Per-criterion rubric grading (HealthBench style). Physician–physician disagreement ≈ 22.5% → the ceiling for any judge; measure labeler agreement first.
- ⚠ Judge instruction wording swung error detection 9.3% → 79%; written severity rubric lifted κ 0.18 → 0.66 (vendor preprint via secondary summary — cite cautiously).
- ⚠ **Thresholds tuned on synthetic data raised false alarms 7–8× on real data** → our synthetic prototype proves the design, not production thresholds. Say this in the interview.
- Keep a small randomized slice + log propensities from launch (Duolingo random arm, Eugene Yan).

**Open decision raised in the doc's comment thread** (for branch 1): one canonical English description per tip with per-language video variants, vs tips authored natively per language? Changes the cross-lingual design.

---

## Gaps (honest)

- No public description of how health apps (Flo etc.) match content to user state.
- No published contraindication-filtering pattern for content feeds.
- No 2026 Hindi cross-lingual embedding head-to-head → test in prototype.
- Not yet pulled: current OpenRouter prices for cost math (do during branch 7).

---

## Sources

- Google — Recommendation systems overview: https://developers.google.com/machine-learning/recommendation/overview/types
- Beyond Relevance: Personalization for Short-Video Search (2409.11281): https://arxiv.org/pdf/2409.11281
- Design a Short-Video Recommender (blog): https://buildml.substack.com/p/data-science-case-study-design-a
- Contextual Distillation Model for Diversified Recommendation (2406.09021): https://arxiv.org/pdf/2406.09021
- WWW 2024 Diversity (Tsinghua): https://fi.ee.tsinghua.edu.cn/~gaochen/papers/WWW2024-Diversity.pdf
- Eugene Yan — Recsys & search in the age of LLMs: https://eugeneyan.com/writing/recsys-llm/
- LF AI & Data — LLM-enhanced recommender architectures: https://lfaidata.foundation/communityblog/2025/08/25/leverage-llm-for-next-gen-recommender-systems-technical-deep-dive-into-llm-enhanced-recommender-architectures/
- LLM-based User Profile Management (PURE, 2502.14541): https://arxiv.org/html/2502.14541
- LLM-Based User Personas at Scale (review): https://pith.science/paper/2606.12198
- Human-level IE from clinical reports (Sci Reports): https://www.nature.com/articles/s41598-025-28767-z
- IE from clinical notes: switch to LLMs? (JAMIA): https://www.researchgate.net/publication/399796087_Information_extraction_from_clinical_notes_are_we_ready_to_switch_to_large_language_models
- Operationalizing LLMs for clinical data extraction: https://pmc.ncbi.nlm.nih.gov/articles/PMC12932350/
- Radiation oncology case report forms: https://pmc.ncbi.nlm.nih.gov/articles/PMC12996807/
- Qwen3 Embedding paper: https://arxiv.org/pdf/2506.05176
- Ollama qwen3-embedding: https://registry.ollama.ai/library/qwen3-embedding
- Ollama embedding models comparison: https://www.morphllm.com/ollama-embedding-models
- BGE-M3 overview: https://www.emergentmind.com/topics/bge-m3-embeddings
- BGE-M3 model card: https://huggingface.co/BAAI/bge-m3
- Hindi-BEIR: https://arxiv.org/pdf/2408.09437
- NLLB-E5 Hindi retrieval: https://arxiv.org/pdf/2409.05401
- Personalized medical content recommendation (patent): https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8543422
- Flo — About: https://med.flo.health/about-flo
- Ginger content recommendation study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9896352/
- Clinician health videos lack evidence (JAMA Netw Open summary): https://www.healthday.com/health-news/general-health/most-doctor-made-youtube-health-videos-lack-strong-proof-study-finds
- YouTube medical misinformation policy: https://www.techtarget.com/patientengagement/news/366584471/YouTube-Revamps-Medical-Misinformation-Guidelines-for-Video-Content
- Knight-Georgetown Institute — beyond engagement: https://kgi.georgetown.edu/wp-content/uploads/2025/02/Global-Policy-Two-Pager.pdf
- Metrics beyond engagement (WIRED via SSRC): https://mediawell.ssrc.org/news-items/platforms-can-optimize-for-metrics-beyond-engagement-wired/?pdf=77574
- Positive AI (2304.12241): https://arxiv.org/pdf/2304.12241
- Epinet for Content Cold Start (Meta, 2412.04484): https://arxiv.org/html/2412.04484v1
- LLM-as-a-Judge for Top-K Recommendation (2606.22961): https://arxiv.org/abs/2606.22961
- User Preference Induction for Offline Top-N Eval (2607.11354): https://arxiv.org/abs/2607.11354
- How to Correctly Report LLM-as-a-Judge Evaluations (2511.21140): https://arxiv.org/pdf/2511.21140
- Dear Algo (judge biases, 2608.15877): https://arxiv.org/pdf/2608.15877
- Langfuse — LLM-as-a-Judge: https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge
- IPS-weighted BPR & SNIPS (2509.00333): https://arxiv.org/pdf/2509.00333
- Off-policy evaluation tutorial: https://towardsdatascience.com/a-complete-tutorial-on-off-policy-evaluation-for-recommender-systems-e92085018afe/
- CAB estimators (ICML 2019): https://icml.cc/virtual/2019/poster/4208
- Slate counterfactual evaluation (2007.12986): https://arxiv.org/pdf/2007.12986
