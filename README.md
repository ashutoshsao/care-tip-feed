# Care-tip feed

Every day, pick which short health videos ("care tips") each user sees, and in what order. The tips come from a library of thousands. The input is each user's free-text health profile. The feed has to work for hundreds of thousands of users across many Indian languages, in a product where a wrong tip can hurt someone.

**The idea in one line:** an LLM reads the profile only when it changes. Everything that runs daily is plain code and lookups: a hard safety filter, then ranking by severity. LLM cost scales with profile changes, not with users.

Built as a system-design exercise for Disha. It has a written design, a working Python prototype, and evals with planted traps.

## Results

On 6 synthetic profiles and a library of 110 tips with planted traps, judged by a panel of three LLM providers:

| System | Unsafe tips | Relevant | Judge panel approves |
|---|---|---|---|
| Random | 19.3 | 53% | 1/6 |
| Embedding-only (plain semantic search) | 12.0 | 72% | 1/6 |
| **This design** | **0** | **82%** | **6/6** |

The first run passed only 2/6 with the judges. They found six gaps the code couldn't see, such as "cleared for moderate exercise" not being treated as a limit, or strength training slipping past "avoid strenuous". All six were fixed, and the rerun passed 6/6. Total API spend for the whole prototype was about $5.

Full numbers: [`prototype/RESULTS.md`](prototype/RESULTS.md).

## How it works

```
WHEN THE PROFILE CHANGES  (nightly batch; a new red flag takes a fast path)
 1. LLM extracts a structured profile: coded issues + status + severity, red flags,
    tests, prescriptions, restrictions, each with a verbatim quote from the source
 2. Checks: code first (quote exists? status fits? red flag vanished?) → LLM
    verifier only if flagged → still unsure: keep the safer status + clinical review
 3. Save as a new timestamped version

EVERY DAY, FOR EVERYONE  (no LLM)
 4. Find tips: exact codes → synonym map → embeddings only for leftovers
 5. Safety filter: contraindications × red flags, diagnosis lock, restrictions,
    language, review status
 6. Rank: severity + recency → 5 slots (pinned safety tip first, top issue ≤ 2 of 5)
 7. Engagement picks which video fills a slot, never which issue
 8. Repeat and rotation rules → today's feed
```

| Tool | Used for | Why |
|---|---|---|
| **LLM** | Profile extraction on change; verifying flagged facts; offline vocabulary drafts and judging | Free text with negation and status ("no tests done", "to be completed") needs language understanding |
| **Embeddings** | Matching issues the vocabulary doesn't cover; nothing safety-related | They can't handle negation, so they only *suggest* |
| **Code** | Checks, safety filter, matching, ranking, every daily run | Predictable, auditable, near-free at 500k users |

**Models:**
- **Extraction:** Claude Haiku 5.5. It made 0 safety errors in 84 checks, at about $0.0015 per extraction.
- **Verifier:** Gemini 3.8 Flash. It comes from a different model family, so it catches different mistakes.
- **Embeddings:** EmbeddingGemma, run locally through Ollama. It was the best of 4 models tested: 94% top-5 hit rate on both English and Hindi tips, with the clearest score spread.

**Cost at scale:** at 100k profile changes a day, extraction comes to about $75/day, or $2.2k/month. The daily feed for every user costs about $0.

## Findings

- **Even strong models mis-tag.** The generated library needed 22 tag fixes, plus 16 more after the judges reviewed it. Tags need clinical review.
- **Embeddings can't spot duplicates.** Two *different* ginger tips scored closer (0.93) than a true duplicate pair (0.84). Variety comes from tags instead.
- **Newer isn't better.** EmbeddingGemma 2 crowds almost every tip into the 0.7–0.8 similarity band, which makes thresholds fragile.
- **Content depth limits the feed.** One user runs out of all 10 period tips by day 5, and another gets one tip because almost no Tamil videos exist. Both gaps are logged as content demand.

**Limits:** six synthetic profiles validate the design, not production numbers. Real profiles are messier and code-mixed.

## Repo

| Path | What's there |
|---|---|
| [`DESIGN.md`](DESIGN.md) | The full design, with a worked example |
| [`system-overview.md`](system-overview.md) | One-page view of the pipeline |
| [`plan.md`](plan.md) | The decision log (D1–D18) |
| [`prototype/`](prototype/) | The pipeline (`feed/`), eval scripts (`scripts/`), safety tests (`tests/`) and data |
| [`presentation/`](presentation/) | Slides with speaker notes |

## Run it

Requires [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) with `embeddinggemma` pulled, and an `OPENROUTER_API_KEY` in `.env` for the scripts that call an LLM.

```sh
cd prototype
uv run python scripts/show_feed.py reema_v1    # today's feed for one user, with what was blocked and why
uv run python scripts/refresh_demo.py          # 7 days, a profile update, and the fast path
uv run python scripts/eval_feeds.py            # random vs embedding-only vs full system, judged
uv run python scripts/eval_extraction.py anthropic/claude-haiku-5.5
uv run pytest -q                               # safety tests
```
