"""Daily feed: find tips → safety filter → rank/compose (D2–D6, D8, D9, D12–D14, D18). No LLM here."""

from dataclasses import dataclass, field
from datetime import date

import numpy as np

from . import vocab
from .embed import embed
from .schemas import Profile, Tip

EMBED_MODEL = "embeddinggemma"         # best of 4 tested (scripts/eval_embeddings.py)
SIM_THRESHOLD = 0.36          # D12: weak matches dropped; set on this model's score scale
TOP_N = 5                     # slots users actually watch (D8)
FEED_LEN = 10
SEVERITY = {"severe": 3, "moderate": 2, "mild": 1}
TEST_TOPIC = {"thyroid_panel": "hypothyroidism", "iron_panel": "iron_deficiency", "vitamin_d": "vitamin_d_deficiency",
              "hba1c": "type2_diabetes", "lipid_panel": "high_cholesterol", "glucose_tolerance": "type2_diabetes"}


@dataclass
class History:
    """Per-user engagement log: tip_id -> day index of last view; likes/dislikes; issue -> last day covered."""
    seen: dict[str, int] = field(default_factory=dict)
    liked: set[str] = field(default_factory=set)
    disliked: set[str] = field(default_factory=set)
    issue_last_shown: dict[str, int] = field(default_factory=dict)


@dataclass
class FeedItem:
    tip_id: str
    language: str
    slot: str          # pinned | priority | prescription | rotation | extra
    issue: str
    reason: str
    discreet: bool     # D6


# ---------- Step 4: find tips (D12) ----------

def find_candidates(prof: Profile, library: list[Tip], tip_vecs: np.ndarray) -> dict[str, list[str]]:
    """Return issue/topic -> candidate tip_ids. Codes first, synonyms second, embeddings for leftovers."""
    topics = {i.code: i.quote for i in prof.issues if i.status != "resolved"}
    for t in prof.tests:                       # pending tests make their topic relevant (test-prep tips)
        topics.setdefault(TEST_TOPIC[t.code], t.quote)
    for g in prof.goals:
        topics.setdefault("goal:" + g.code, g.quote)
    for o in prof.other:
        topics.setdefault("other:" + o.text, o.quote)

    cands: dict[str, list[str]] = {}
    for topic in topics:
        if topic.startswith("goal:"):
            code = topic[5:]
            cands[topic] = [t.tip_id for t in library if code in t.goals]
        elif not topic.startswith("other:"):
            codes = vocab.expand(topic)
            cands[topic] = [t.tip_id for t in library if set(codes) & set(t.conditions)]
    # Embeddings only for topics codes couldn't fill (out-of-vocabulary or too few matches).
    leftovers = [k for k in topics if len(cands.get(k, [])) < 2]
    if leftovers:
        q = embed([topics[k] for k in leftovers], EMBED_MODEL)
        sims = q @ tip_vecs.T
        for k, row in zip(leftovers, sims):
            best = [library[j].tip_id for j in np.argsort(-row)[:3] if row[j] >= SIM_THRESHOLD]
            cands[k] = list(dict.fromkeys(cands.get(k, []) + best))
    return cands


# ---------- Step 5: safety filter — code only (D2–D5) ----------

def pick_variant(tip: Tip, lang: str) -> str | None:
    langs = [v.language for v in tip.variants]
    for l in [lang] + vocab.CLOSE_LANGUAGES.get(lang, []):   # D2 ladder steps 1–2; else skip
        if l in langs:
            return l
    return None


def safety_reason(tip: Tip, prof: Profile) -> str | None:
    """Why this tip must NOT be shown to this user today (None = eligible)."""
    flags, restr = prof.flags(), prof.restriction_codes()
    confirmed = {i.code for i in prof.issues if i.status == "confirmed"}
    if tip.review_status != "approved":
        return f"review {tip.review_status}"
    if hit := set(tip.contraindications) & flags:
        return f"contraindicated: {sorted(hit)}"
    if "no_high_exertion" in restr and tip.exertion in ("moderate", "high"):
        return "clinician restriction: avoid strenuous exercise"
    pending = {t.code for t in prof.tests if t.status != "results_received"}
    if tip.prep_for_test and tip.prep_for_test not in pending:
        return f"test prep for {tip.prep_for_test}, not pending"
    if tip.requires_confirmed_diagnosis and tip.requires_confirmed_diagnosis not in confirmed:
        return f"diagnosis lock: {tip.requires_confirmed_diagnosis} not confirmed"
    if tip.sex != "any" and tip.sex != prof.sex:
        return f"for {tip.sex} only"
    if not tip.min_age <= prof.age <= tip.max_age:
        return "age out of range"
    if tip.life_stage == "pregnant" and prof.life_stage != "pregnant":
        return "pregnancy-only tip"
    if tip.life_stage == "postpartum" and prof.life_stage == "pregnant":
        return "postpartum tip for pregnant user"
    if tip.diet == "nonveg" and prof.diet_type == "veg":
        return "non-veg tip for vegetarian"
    if tip.setting == "gym" and prof.workout_setting == "home":
        return "gym tip for home-workout user"
    if pick_variant(tip, prof.language) is None:
        return f"no {prof.language} variant"
    return None


# ---------- Step 6–8: rank + compose (D4, D8, D9, D13, D14) ----------

def issue_priority(prof: Profile, recency_days: dict[str, int]) -> list[str]:
    """Severity first, recency boost fading over ~2 weeks (D14)."""
    def score(i):
        boost = max(0.0, 1 - recency_days.get(i.code, 30) / 14)
        return SEVERITY[i.severity] + boost
    return [i.code for i in sorted((i for i in prof.issues if i.status != "resolved"), key=score, reverse=True)]


def tip_score(tip: Tip, hist: History, today: int, liked_types: set[str]) -> float:
    s = 0.0
    if tip.tip_id not in hist.seen:
        s += 2                                     # new first (D9)
    elif today - hist.seen[tip.tip_id] >= 7 and tip.interventions:
        s += 1                                     # prescription reminders may return after a week (D9)
    if tip.tip_type in liked_types:
        s += 0.5                                   # engagement picks HOW, not WHAT (D13)
    s += {"A": 0.3, "B": 0.2, "C": 0.1, "D": 0}[tip.evidence_level]
    return s


def build_feed(prof: Profile | None, library: list[Tip], tip_vecs: np.ndarray, hist: History | None = None,
               today: int = 0, recency_days: dict[str, int] | None = None) -> tuple[list[FeedItem], dict]:
    hist, recency_days = hist or History(), recency_days or {}
    by_id = {t.tip_id: t for t in library}
    lang = prof.language if prof else "en"

    # D18 cold start: no usable profile → universally safe tips only.
    if prof is None or (not prof.issues and not prof.goals):
        safe = [t for t in library if t.universally_safe and pick_variant(t, lang)]
        return [FeedItem(t.tip_id, pick_variant(t, lang), "cold_start", "-", "universally safe", False)
                for t in safe[:FEED_LEN]], {}

    cands = find_candidates(prof, library, tip_vecs)
    excluded = {}
    eligible = {}
    for topic, ids in cands.items():
        ok = []
        for tid in ids:
            why = safety_reason(by_id[tid], prof)
            if why:
                excluded[tid] = why
            elif tid not in hist.disliked:          # never the exact disliked video (D9)
                ok.append(tid)
        eligible[topic] = ok

    liked_types = {by_id[t].tip_type for t in hist.liked if t in by_id}
    used, feed = set(), []
    vec_idx = {t.tip_id: n for n, t in enumerate(library)}

    def best(topic):
        pool = [t for t in eligible.get(topic, []) if t not in used]
        # skip near-duplicates of today's tips: same cluster + same type, or near-identical meaning (D3).
        # Similarity alone can't tell duplicates from related tips (health tips all embed close together).
        def dup(t, u):
            a, b = by_id[t], by_id[u]
            same_slot = a.topic_cluster == b.topic_cluster and a.tip_type == b.tip_type
            return same_slot or float(tip_vecs[vec_idx[t]] @ tip_vecs[vec_idx[u]]) > 0.92
        pool = [t for t in pool if not any(dup(t, u) for u in used)]
        return max(pool, key=lambda t: tip_score(by_id[t], hist, today, liked_types), default=None)

    def add(tid, slot, topic, reason):
        used.add(tid)
        t = by_id[tid]
        feed.append(FeedItem(tid, pick_variant(t, lang), slot, topic, reason, t.sensitive))

    # Slot 1: pinned reinforcement while a red flag is active (D4).
    for flag in prof.flags():
        for t in library:
            if t.is_reinforcement_for_flag == flag and pick_variant(t, lang) and t.tip_id not in used:
                add(t.tip_id, "pinned", flag, f"red flag {flag} active")

    order = issue_priority(prof, recency_days)
    # Top issue: up to 2 of the top slots (D8).
    if order:
        for _ in range(2):
            if (tid := best(order[0])) and len(feed) < TOP_N:
                add(tid, "priority", order[0], f"top issue ({order[0]})")
    # ≥1 slot reinforcing a prescribed intervention (D8).
    rx = {i.code for i in prof.interventions}
    rx_tips = [t for t in eligible_ids(eligible) if set(by_id[t].interventions) & rx and t not in used]
    if rx_tips and len(feed) < TOP_N:
        tid = max(rx_tips, key=lambda t: tip_score(by_id[t], hist, today, liked_types))
        add(tid, "prescription", ",".join(sorted(set(by_id[tid].interventions) & rx)), "reinforces prescription")
    # Remaining top slots rotate across other issues: least recently shown first, then priority (D8).
    rest = sorted(order[1:], key=lambda c: (hist.issue_last_shown.get(c, -99), order.index(c)))
    for topic in rest + [k for k in eligible if k not in order]:
        if len(feed) >= FEED_LEN:
            break
        if tid := best(topic):
            add(tid, "rotation" if len(feed) < TOP_N else "extra", topic, f"issue {topic}")
    # Good-to-know backfill when personalized tips run out (v0's middle tier): general wellness, still safety-filtered.
    eligible["backfill"] = [t.tip_id for t in library if (t.general_wellness or t.universally_safe)
                            and t.exertion in ("none", "low") and not t.sensitive   # good-to-know tier stays low-risk
                            and t.tip_id not in hist.disliked and safety_reason(t, prof) is None]
    while len(feed) < FEED_LEN and (tid := best("backfill")):
        add(tid, "backfill", "-", "general wellness")
    return feed, excluded


def eligible_ids(eligible: dict[str, list[str]]) -> list[str]:
    return list(dict.fromkeys(t for ids in eligible.values() for t in ids))
