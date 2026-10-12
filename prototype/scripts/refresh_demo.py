"""Prototype step 10: 7 simulated days for Reema, then the v1 → v2 profile change, then a red-flag fast path."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed.embed import embed
from feed.extract import code_checks
from feed.pipeline import EMBED_MODEL, History, build_feed, safety_reason
from feed.schemas import Profile, RedFlag, Tip

library = [Tip(**t) for t in json.loads((ROOT / "data" / "library.json").read_text())]
by_id = {t.tip_id: t for t in library}
vecs = embed([t.canonical_description for t in library], EMBED_MODEL)
ex = json.loads((ROOT / "data" / "extraction_results_claude-haiku-5.5.json").read_text())
v1 = next(Profile(**r["profile"]) for r in ex if r["pep"] == "reema_v1")
v2 = next(Profile(**r["profile"]) for r in ex if r["pep"] == "reema_v2")
title = lambda tid: next(v.title for v in by_id[tid].variants if v.language == "en")
lines = []


def out(s=""):
    print(s)
    lines.append(s)


# ---- 7 days on profile v1: views, one dislike, likes on how-to videos ----
hist = History()
out("## 7 simulated days on profile v1 (top 5 each day)")
for day in range(7):
    feed, _ = build_feed(v1, library, vecs, hist, today=day)
    top = feed[:5]
    out(f"day {day}: " + " | ".join(f"{f.slot[:4]}:{title(f.tip_id)[:28]}" for f in top))
    for f in top:
        hist.seen[f.tip_id] = day
        hist.issue_last_shown[f.issue] = day
        if by_id[f.tip_id].tip_type == "how_to":
            hist.liked.add(f.tip_id)
    if day == 1:   # she dislikes one video on day 1
        d = next(f.tip_id for f in top if f.slot == "priority")
        hist.disliked.add(d)
        out(f"   ↳ dislikes '{title(d)}'")
shown = [f.tip_id for day in range(7) for f in build_feed(v1, library, vecs, hist, today=day)[0][:5]]
out(f"disliked video shown again after day 1: {any(t in hist.disliked for t in shown)}")

# ---- Profile changes: v1 → v2 (results back, cardiac concern cleared) ----
out("\n## Profile update v1 → v2 (diff of structured profiles, D11)")
rf = lambda p: {r.code: r.status for r in p.red_flags}
tests = lambda p: {t.code: t.status for t in p.tests}
conf = lambda p: {i.code for i in p.issues if i.status == "confirmed"}
out(f"red flags: {rf(v1)} → {rf(v2)}")
out(f"tests:     {tests(v1)} → {tests(v2)}")
out(f"newly confirmed: {sorted(conf(v2) - conf(v1))};  restrictions: {sorted(v2.restriction_codes())}")
pep2 = (ROOT / "data" / "peps" / "reema_v2.xml").read_text()
out(f"old-vs-new code checks (D7): {code_checks(pep2, v2, prev=v1) or 'no flags'}")

recency = {c: 0 for c in conf(v2) - conf(v1)}          # just-changed issues get the recency boost (D14)
before = [f.tip_id for f in build_feed(v1, library, vecs, History(), today=7)[0]]
after_feed, after_excl = build_feed(v2, library, vecs, History(), today=7, recency_days=recency)
after = [f.tip_id for f in after_feed]
out("\nleft the feed:   " + "; ".join(title(t) for t in before if t not in after))
out("joined the feed: " + "; ".join(title(t) for t in after if t not in before))
for tid in ["red_flag_chest_pain", "diet_iron_deficiency_anaemia", "iron_panel_prep", "hiit_basics_cardio"]:
    why = safety_reason(by_id[tid], v2)
    out(f"  {title(tid)[:40]:40} v1: {safety_reason(by_id[tid], v1) or 'eligible':42} v2: {why or 'eligible'}")

# ---- Safety fast path: new red flag mid-day (D11) ----
out("\n## Fast path: Arjun reports new chest pain at 2 PM (feed already built this morning)")
arjun = next(Profile(**r["profile"]) for r in ex if r["pep"] == "arjun")
morning = build_feed(arjun, library, vecs)[0]
flagged = arjun.model_copy(deep=True)
flagged.red_flags = [RedFlag(code="suspected_cardiac", status="active", quote="new chest pain today")]
removed = [f.tip_id for f in morning if safety_reason(by_id[f.tip_id], flagged)]
out("removed from today's feed immediately: " + ("; ".join(title(t) for t in removed) or "none"))
out("pinned: " + title("red_flag_chest_pain"))

(ROOT / "data" / "refresh_demo.md").write_text("# Refresh demo (prototype step 10)\n\n```\n" + "\n".join(lines) + "\n```\n")
